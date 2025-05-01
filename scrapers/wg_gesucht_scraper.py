from .base_scraper import BaseScraper, logger
import asyncio
from typing import Dict, List, Any, Optional
import re
import time
import random

class WGGesuchtScraper(BaseScraper):
    """Scraper for WG-Gesucht website"""
    
    BASE_URL = "https://www.wg-gesucht.de"
    SEARCH_URL = f"{BASE_URL}/wohnungen-in-{{location}}.{{location_id}}.html"

    # City codes for WG-Gesucht
    CITY_CODES = {
        "berlin": "8",
        "hamburg": "55",
        "munich": "90",
        "cologne": "73",
        "frankfurt": "41",
        "stuttgart": "124",
        "düsseldorf": "30",
        "leipzig": "78",
        "dortmund": "26",
        "essen": "35",
        "bremen": "17",
        "dresden": "27",
        "hannover": "57"
    }
    
    def __init__(self, headless=True):
        """
        Initialize the WG-Gesucht scraper
        
        Args:
            headless (bool): Whether to run the browser in headless mode
        """
        super().__init__(headless)
        
    async def _get_city_id(self, city: str) -> Optional[str]:
        """
        Get the city ID for WG-Gesucht
        
        Args:
            city (str): Name of the city
            
        Returns:
            str: City ID or None if not found
        """
        city_lower = city.lower()
        
        # Direct match in our dictionary
        if city_lower in self.CITY_CODES:
            return self.CITY_CODES[city_lower]
            
        # Try to find a partial match
        for known_city, city_id in self.CITY_CODES.items():
            if known_city in city_lower or city_lower in known_city:
                return city_id
                
        # If no match found, try to search on the website
        try:
            await self.page.goto(f"{self.BASE_URL}")
            await self.page.fill('input[name="autocompinp"]', city)
            await asyncio.sleep(1)  # Wait for autocomplete
            
            # Check if we have autocomplete results
            suggestion = await self.page.query_selector('.autocomplete-suggestion')
            if suggestion:
                suggestion_text = await suggestion.text_content()
                match = re.search(r'data-val="(\d+)"', suggestion_text)
                if match:
                    return match.group(1)
        except Exception as e:
            logger.error(f"Error getting city ID for {city}: {e}")
            
        return None
        
    async def _accept_cookies(self):
        """Accept cookies if the dialog appears"""
        try:
            accept_button = await self.page.query_selector('#cmpwelcomebtnyes')
            if accept_button:
                await accept_button.click()
                await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"Could not accept cookies: {e}")
    
    async def search(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for listings with the given filters
        
        Args:
            filters (dict): Dictionary containing:
                - location (str): City name
                - max_price (float): Maximum rent
                - min_size (float): Minimum size in sqm
                - min_rooms (float): Minimum number of rooms
                - wg (bool): Whether to include shared flats
                
        Returns:
            list: List of dictionaries containing listing data
        """
        if not self.page:
            await self.initialize()
            
        listings = []
        location = filters.get('location', '')
        
        # Get city ID for the search URL
        city_id = await self._get_city_id(location)
        if not city_id:
            logger.error(f"Could not find city ID for location: {location}")
            return []
            
        # Construct search URL
        # Remove special characters and spaces from location for URL
        location_url = re.sub(r'[^a-zA-Z0-9]', '', location.lower())
        search_url = self.SEARCH_URL.format(location=location_url, location_id=city_id)
        
        try:
            # Navigate to search page
            await self.page.goto(search_url)
            await self._accept_cookies()
            
            # Check and set filters
            # Price filter
            if 'max_price' in filters and filters['max_price']:
                await self.page.fill('#maxPrice', str(filters['max_price']))
                
            # Size filter
            if 'min_size' in filters and filters['min_size']:
                await self.page.fill('#minSize', str(filters['min_size']))
                
            # Room filter
            if 'min_rooms' in filters and filters['min_rooms']:
                await self.page.select_option('#rMax', str(int(filters['min_rooms'])))
                
            # Apply filters
            await self.page.click('#sp_submit')
            await self.page.wait_for_load_state('networkidle')
            
            # Extract listings
            listing_elements = await self.page.query_selector_all('.wgg_card.offer_list_item')
            
            for element in listing_elements:
                try:
                    # Extract basic info
                    title_element = await element.query_selector('.wgg_card_title')
                    title = await title_element.text_content() if title_element else "No title"
                    
                    # Extract URL
                    url_element = await element.query_selector('a.detailansicht')
                    relative_url = await url_element.get_attribute('href') if url_element else None
                    full_url = f"{self.BASE_URL}{relative_url}" if relative_url else None
                    
                    if not full_url:
                        continue
                    
                    # Extract details
                    details_element = await element.query_selector('.col-xs-11')
                    details_text = await details_element.text_content() if details_element else ""
                    
                    # Extract price
                    price_element = await element.query_selector('.col-xs-3:has-text("€")')
                    price_text = await price_element.text_content() if price_element else "0"
                    price = self.extract_price(price_text)
                    
                    # Extract size
                    size_element = await element.query_selector('.col-xs-3:has-text("m²")')
                    size_text = await size_element.text_content() if size_element else "0"
                    size = self.extract_size(size_text)
                    
                    # Extract rooms
                    rooms_element = await element.query_selector('.col-xs-3:has-text("Zimmer")')
                    rooms_text = await rooms_element.text_content() if rooms_element else "1"
                    rooms = self.extract_rooms(rooms_text)
                    
                    # Extract image
                    img_element = await element.query_selector('img.wgg_thumbnail')
                    img_url = await img_element.get_attribute('src') if img_element else None
                    
                    # Check if it's a shared flat (WG)
                    is_wg = "WG" in title or "Wohngemeinschaft" in title or "Zimmer" in title
                    
                    # Check if it matches all our filters
                    if (filters.get('max_price') and price and price > filters['max_price']):
                        continue
                        
                    if (filters.get('min_size') and size and size < filters['min_size']):
                        continue
                        
                    if (filters.get('min_rooms') and rooms and rooms < filters['min_rooms']):
                        continue
                        
                    if ('wg' in filters and not filters['wg'] and is_wg):
                        continue
                    
                    # Add to listings
                    listings.append({
                        'title': title.strip(),
                        'price': price,
                        'size': size,
                        'rooms': rooms,
                        'location': location,
                        'url': full_url,
                        'image_url': img_url,
                        'source': 'wg_gesucht',
                        'is_wg': is_wg,
                        'has_form': True,  # WG-Gesucht typically uses forms
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
            
            # Check for balcony
            details_text = await self.page.text_content('#rent_wrapper')
            if details_text and ('Balkon' in details_text or 'balcony' in details_text.lower()):
                contact_info['has_balcony'] = True
                
            # Sometimes email is visible
            email_element = await self.page.query_selector('a[href^="mailto:"]')
            if email_element:
                email_href = await email_element.get_attribute('href')
                if email_href:
                    contact_info['email'] = email_href.replace('mailto:', '')
                    
            return contact_info
            
        except Exception as e:
            logger.error(f"Error getting contact info: {e}")
            return contact_info
            
    async def apply_via_form(self, listing_url: str, application_data: Dict[str, Any]) -> bool:
        """
        Apply to a listing via the web form
        
        Args:
            listing_url (str): URL of the listing
            application_data (dict): Dictionary containing:
                - name (str): Full name
                - email (str): Email address
                - phone (str): Phone number
                - message (str): Application message
                
        Returns:
            bool: True if application successful, False otherwise
        """
        if not self.page:
            await self.initialize()
            
        try:
            await self.page.goto(listing_url)
            await self._accept_cookies()
            
            # Find the contact button and click it
            contact_button = await self.page.query_selector('button.btn-md:has-text("Kontaktieren")')
            if contact_button:
                await contact_button.click()
                await asyncio.sleep(2)  # Wait for form to appear
                
                # Fill the form
                await self.page.fill('#contactForm-Message', application_data.get('message', ''))
                await self.page.fill('#contactForm-firstName', application_data.get('first_name', ''))
                await self.page.fill('#contactForm-lastName', application_data.get('last_name', ''))
                await self.page.fill('#contactForm-contactEmail', application_data.get('email', ''))
                await self.page.fill('#contactForm-contactPhone', application_data.get('phone', ''))
                
                # Add some randomness to appear more human
                await asyncio.sleep(random.uniform(1, 2))
                
                # Submit the form
                submit_button = await self.page.query_selector('button[type="submit"]:has-text("Nachricht senden")')
                if submit_button:
                    await submit_button.click()
                    await asyncio.sleep(3)  # Wait for submission
                    
                    # Check for success message
                    success_element = await self.page.query_selector('.alert-success')
                    if success_element:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error applying via form: {e}")
            return False 