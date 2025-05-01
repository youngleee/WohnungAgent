from .base_scraper import BaseScraper, logger
import asyncio
from typing import Dict, List, Any, Optional
import re
import time
import random

class ImmonetScraper(BaseScraper):
    """Scraper for Immonet website"""
    
    BASE_URL = "https://www.immonet.de"
    SEARCH_URL = f"{BASE_URL}/immobiliensuche/se/{{location}}/-/wohnung/mieten"
    
    def __init__(self, headless=True):
        """
        Initialize the Immonet scraper
        
        Args:
            headless (bool): Whether to run the browser in headless mode
        """
        super().__init__(headless)
    
    async def _accept_cookies(self):
        """Accept cookies if the dialog appears"""
        try:
            # Accept cookies button
            accept_button = await self.page.query_selector('#didomi-notice-agree-button')
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
                - balcony (bool): Whether the property should have a balcony
                
        Returns:
            list: List of dictionaries containing listing data
        """
        if not self.page:
            await self.initialize()
            
        listings = []
        location = filters.get('location', '')
        
        # Prepare location for URL
        location_url = location.lower().replace(' ', '-').replace('ü', 'ue').replace('ä', 'ae').replace('ö', 'oe').replace('ß', 'ss')
        search_url = self.SEARCH_URL.format(location=location_url)
        
        # Add query parameters for filters
        params = []
        
        if filters.get('max_price'):
            params.append(f"cp={filters['max_price']}")
            
        if filters.get('min_size'):
            params.append(f"wfl={filters['min_size']}")
            
        if filters.get('min_rooms'):
            params.append(f"rm={filters['min_rooms']}")
            
        if filters.get('balcony'):
            params.append("balc=1")
            
        if params:
            search_url += "?" + "&".join(params)
        
        try:
            # Navigate to search page
            await self.page.goto(search_url)
            await self._accept_cookies()
            
            # Wait for listings to load
            await self.page.wait_for_selector('.search-object', timeout=10000)
            
            # Extract listings
            listing_elements = await self.page.query_selector_all('.search-object')
            
            for element in listing_elements:
                try:
                    # Skip promoted listings
                    promoted = await element.query_selector('.top-position-flag')
                    if promoted:
                        continue
                    
                    # Extract title
                    title_element = await element.query_selector('.ellipsis')
                    title = await title_element.text_content() if title_element else "No title"
                    
                    # Extract URL
                    url_element = await element.query_selector('a.block.ellipsis')
                    relative_url = await url_element.get_attribute('href') if url_element else None
                    full_url = f"{self.BASE_URL}{relative_url}" if relative_url and relative_url.startswith('/') else relative_url
                    
                    if not full_url:
                        continue
                    
                    # Extract price
                    price_element = await element.query_selector('.text-right-lg .text-primary')
                    price_text = await price_element.text_content() if price_element else "0 €"
                    price = self.extract_price(price_text)
                    
                    # Extract size
                    facts_elements = await element.query_selector_all('.text-right .text-primary')
                    size_text = await facts_elements[1].text_content() if len(facts_elements) > 1 else "0 m²"
                    size = self.extract_size(size_text)
                    
                    # Extract rooms
                    rooms_text = await facts_elements[0].text_content() if facts_elements else "1 Zi."
                    rooms = self.extract_rooms(rooms_text)
                    
                    # Extract image
                    img_element = await element.query_selector('img.image')
                    img_url = await img_element.get_attribute('data-original') if img_element else None
                    if not img_url and img_element:
                        img_url = await img_element.get_attribute('src')
                    
                    # Extract address
                    address_element = await element.query_selector('.text-100')
                    address = await address_element.text_content() if address_element else location
                    
                    # Check if it's a shared flat (WG)
                    is_wg = "WG" in title or "Wohngemeinschaft" in title or "Zimmer" in title
                    
                    # Add to listings
                    listings.append({
                        'title': title.strip(),
                        'price': price,
                        'size': size,
                        'rooms': rooms,
                        'location': address.strip() if address else location,
                        'url': full_url,
                        'image_url': img_url,
                        'source': 'immonet',
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
            
            # Check for balcony
            details_text = await self.page.text_content('#equipmentid')
            if details_text and ('Balkon' in details_text or 'balcony' in details_text.lower()):
                contact_info['has_balcony'] = True
                
            # Check for email in contact section
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
            contact_button = await self.page.query_selector('button.btn-primary:has-text("Kontaktieren")')
            if not contact_button:
                contact_button = await self.page.query_selector('a.btn-primary:has-text("Kontaktieren")')
                
            if contact_button:
                await contact_button.click()
                await asyncio.sleep(2)  # Wait for form to appear
                
                # Fill the form
                message_field = await self.page.query_selector('textarea#message')
                if message_field:
                    await message_field.fill(application_data.get('message', ''))
                
                # Name fields
                first_name = await self.page.query_selector('input#firstname')
                if first_name:
                    await first_name.fill(application_data.get('first_name', ''))
                    
                last_name = await self.page.query_selector('input#lastname')
                if last_name:
                    await last_name.fill(application_data.get('last_name', ''))
                
                # Email and phone
                email_field = await self.page.query_selector('input#email')
                if email_field:
                    await email_field.fill(application_data.get('email', ''))
                    
                phone_field = await self.page.query_selector('input#phone')
                if phone_field:
                    await phone_field.fill(application_data.get('phone', ''))
                
                # Check privacy policy checkbox if it exists
                privacy_checkbox = await self.page.query_selector('input[type="checkbox"]#agbs')
                if privacy_checkbox:
                    await privacy_checkbox.check()
                
                # Add some randomness to appear more human
                await asyncio.sleep(random.uniform(1, 2))
                
                # Find and click submit button
                submit_button = await self.page.query_selector('button[type="submit"]')
                if submit_button:
                    await submit_button.click()
                    await asyncio.sleep(3)  # Wait for submission
                    
                    # Check for success indicators
                    success_element = await self.page.query_selector('.alert-success')
                    if success_element:
                        return True
            
            logger.warning("Could not apply via form on Immonet")
            return False
            
        except Exception as e:
            logger.error(f"Error applying via form: {e}")
            return False 