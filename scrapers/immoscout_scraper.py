from .base_scraper import BaseScraper, logger
import asyncio
from typing import Dict, List, Any, Optional
import re
import time
import random
import json

class ImmoScoutScraper(BaseScraper):
    """Scraper for Immobilienscout24 website"""
    
    BASE_URL = "https://www.immobilienscout24.de"
    SEARCH_URL = f"{BASE_URL}/Suche/de/{{state}}/{{city}}/wohnung-mieten"
    
    def __init__(self, headless=True):
        """
        Initialize the Immobilienscout24 scraper
        
        Args:
            headless (bool): Whether to run the browser in headless mode
        """
        super().__init__(headless)
    
    async def _accept_cookies(self):
        """Accept cookies if the dialog appears"""
        try:
            # First check for the initial cookie banner
            accept_button = await self.page.query_selector('#onetrust-accept-btn-handler')
            if accept_button:
                await accept_button.click()
                await asyncio.sleep(1)
                
            # Sometimes there's a second consent dialog
            consent_button = await self.page.query_selector('button.consent-accept-all')
            if consent_button:
                await consent_button.click()
                await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"Could not accept cookies: {e}")
    
    async def _get_state_from_city(self, city: str) -> str:
        """
        Get the state for a given city - simplified mapping
        
        Args:
            city (str): City name
            
        Returns:
            str: State name for URL
        """
        # Map of major cities to their states for URL
        city_state_map = {
            "berlin": "berlin",
            "hamburg": "hamburg",
            "munich": "bayern",
            "münchen": "bayern",
            "cologne": "nordrhein-westfalen",
            "köln": "nordrhein-westfalen",
            "frankfurt": "hessen",
            "stuttgart": "baden-wuerttemberg",
            "düsseldorf": "nordrhein-westfalen",
            "dusseldorf": "nordrhein-westfalen",
            "leipzig": "sachsen",
            "dortmund": "nordrhein-westfalen",
            "essen": "nordrhein-westfalen",
            "bremen": "bremen",
            "dresden": "sachsen",
            "hannover": "niedersachsen"
        }
        
        city_lower = city.lower()
        
        # Direct match in our dictionary
        if city_lower in city_state_map:
            return city_state_map[city_lower]
            
        # Try to find a partial match
        for known_city, state in city_state_map.items():
            if known_city in city_lower or city_lower in known_city:
                return state
                
        # Default to a common state if we can't match
        return "deutschland"
    
    async def search(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for listings with the given filters
        
        Args:
            filters (dict): Dictionary containing:
                - location (str): City name
                - max_price (float): Maximum rent
                - min_size (float): Minimum size in sqm
                - min_rooms (float): Minimum number of rooms
                - balcony (bool): Whether the property should have a balcony
                
        Returns:
            list: List of dictionaries containing listing data
        """
        if not self.page:
            await self.initialize()
            
        listings = []
        location = filters.get('location', '')
        
        # Get state from city for search URL
        state = await self._get_state_from_city(location)
        
        # Construct search URL - normalize location name for URL
        location_url = location.lower().replace(' ', '-').replace('ü', 'ue').replace('ä', 'ae').replace('ö', 'oe').replace('ß', 'ss')
        search_url = self.SEARCH_URL.format(state=state, city=location_url)
        
        # Add query parameters for filters
        params = []
        
        if filters.get('max_price'):
            params.append(f"price=-{filters['max_price']}")
            
        if filters.get('min_size'):
            params.append(f"livingspace={filters['min_size']}-")
            
        if filters.get('min_rooms'):
            params.append(f"numberofrooms={filters['min_rooms']}-")
            
        if filters.get('balcony'):
            params.append("balcony=YES")
            
        if params:
            search_url += "?" + "&".join(params)
        
        try:
            # Navigate to search page
            await self.page.goto(search_url)
            await self._accept_cookies()
            
            # Wait for listings to load
            await self.page.wait_for_selector('.result-list__listing', timeout=10000)
            
            # Extract listings
            listing_elements = await self.page.query_selector_all('li.result-list__listing')
            
            for element in listing_elements:
                try:
                    # Skip sponsored listings
                    sponsored = await element.query_selector('.label-sponsor')
                    if sponsored:
                        continue
                    
                    # Extract title
                    title_element = await element.query_selector('h2[data-test="expose-title"]')
                    title = await title_element.text_content() if title_element else "No title"
                    
                    # Extract URL
                    url_element = await element.query_selector('a.result-list-entry__brand-title-container')
                    relative_url = await url_element.get_attribute('href') if url_element else None
                    full_url = f"{self.BASE_URL}{relative_url}" if relative_url else None
                    
                    if not full_url:
                        continue
                    
                    # Extract price
                    price_element = await element.query_selector('[data-test="price"]')
                    price_text = await price_element.text_content() if price_element else "0"
                    price = self.extract_price(price_text)
                    
                    # Extract size
                    size_element = await element.query_selector('[data-test="area"]')
                    size_text = await size_element.text_content() if size_element else "0"
                    size = self.extract_size(size_text)
                    
                    # Extract rooms
                    rooms_element = await element.query_selector('[data-test="rooms"]')
                    rooms_text = await rooms_element.text_content() if rooms_element else "1"
                    rooms = self.extract_rooms(rooms_text)
                    
                    # Extract image
                    img_element = await element.query_selector('img.result-list-entry__image')
                    img_url = await img_element.get_attribute('src') if img_element else None
                    
                    # Extract address
                    address_element = await element.query_selector('[data-test="address"]')
                    address = await address_element.text_content() if address_element else location
                    
                    # Check if it's a shared flat (WG)
                    is_wg = "WG" in title or "Wohngemeinschaft" in title or "Zimmer" in (title + address)
                    
                    # Add to listings
                    listings.append({
                        'title': title.strip(),
                        'price': price,
                        'size': size,
                        'rooms': rooms,
                        'location': address.strip() if address else location,
                        'url': full_url,
                        'image_url': img_url,
                        'source': 'immoscout24',
                        'is_wg': is_wg,
                        'has_form': True
                    })
                    
                except Exception as e:
                    logger.error(f"Error extracting listing: {e}")
            
            return listings
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []
    
    async def get_contact_info(self, listing_url: str) -> Dict[str, Any]:
        """
        Get contact information for a listing
        
        Args:
            listing_url (str): URL of the listing
            
        Returns:
            dict: Dictionary containing contact information
        """
        if not self.page:
            await self.initialize()
            
        contact_info = {
            'email': None,
            'has_form': True,
            'has_balcony': False
        }
        
        try:
            await self.page.goto(listing_url)
            await self._accept_cookies()
            
            # Check for balcony in the amenities
            amenities_text = await self.page.text_content('.criteriagroup--amenities')
            if amenities_text and ('Balkon' in amenities_text or 'balcony' in amenities_text.lower()):
                contact_info['has_balcony'] = True
                
            # Sometimes email is visible in contact section
            contact_section = await self.page.query_selector('.contact-data')
            if contact_section:
                contact_text = await contact_section.text_content()
                email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', contact_text)
                if email_match:
                    contact_info['email'] = email_match.group(0)
            
            return contact_info
            
        except Exception as e:
            logger.error(f"Error getting contact info: {e}")
            return contact_info
    
    async def apply_via_form(self, listing_url: str, application_data: Dict[str, Any]) -> bool:
        """
        Apply to a listing via the web form
        
        Args:
            listing_url (str): URL of the listing
            application_data (dict): Dictionary containing application data
                
        Returns:
            bool: True if application successful, False otherwise
        """
        if not self.page:
            await self.initialize()
            
        try:
            await self.page.goto(listing_url)
            await self._accept_cookies()
            
            # Find and click the contact button
            contact_button = await self.page.query_selector('button.contact-button')
            if not contact_button:
                contact_button = await self.page.query_selector('a.button-primary:has-text("Kontakt")')
                
            if contact_button:
                await contact_button.click()
                await asyncio.sleep(2)  # Wait for form to appear
                
                # Check if we need to login first
                login_form = await self.page.query_selector('form.login-form')
                if login_form:
                    logger.warning("Login required for ImmobilienScout24 application")
                    return False
                
                # Fill the form if available
                message_field = await self.page.query_selector('#contactForm-Message, textarea[name="message"]')
                if message_field:
                    await message_field.fill(application_data.get('message', ''))
                
                # Fill other fields if they exist
                name_field = await self.page.query_selector('input[name="contactName"]')
                if name_field:
                    name = f"{application_data.get('first_name', '')} {application_data.get('last_name', '')}".strip()
                    await name_field.fill(name)
                
                email_field = await self.page.query_selector('input[name="email"], input[type="email"]')
                if email_field:
                    await email_field.fill(application_data.get('email', ''))
                
                phone_field = await self.page.query_selector('input[name="phone"], input[type="tel"]')
                if phone_field:
                    await phone_field.fill(application_data.get('phone', ''))
                
                # Add some randomness to appear more human
                await asyncio.sleep(random.uniform(1, 2))
                
                # Look for submit button
                submit_button = await self.page.query_selector('button[type="submit"]:has-text("Anfrage senden"), button.submit-button')
                if submit_button:
                    await submit_button.click()
                    await asyncio.sleep(3)  # Wait for submission
                    
                    # Check for success indicators
                    success_element = await self.page.query_selector('.success-message, .message-success')
                    if success_element:
                        return True
            
            logger.warning("Could not apply via form on ImmobilienScout24")
            return False
            
        except Exception as e:
            logger.error(f"Error applying via form: {e}")
            return False 