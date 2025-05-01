from playwright.async_api import async_playwright
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import re

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base class for all property listing scrapers"""
    
    def __init__(self, headless=True):
        """
        Initialize the scraper
        
        Args:
            headless (bool): Whether to run the browser in headless mode
        """
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        
    async def initialize(self):
        """Initialize the browser and page"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        )
        self.page = await self.context.new_page()
        
    async def close(self):
        """Close browser resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
    @staticmethod
    def extract_price(price_text: str) -> Optional[float]:
        """
        Extract numeric price from text
        
        Args:
            price_text (str): Text containing the price
            
        Returns:
            float: Extracted price or None if not found
        """
        if not price_text:
            return None
            
        # Extract numbers, handle both dot and comma as decimal separator
        match = re.search(r'(\d+[.,]?\d*)', price_text.replace('.', '').replace(',', '.'))
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None
        
    @staticmethod
    def extract_size(size_text: str) -> Optional[float]:
        """
        Extract numeric size from text
        
        Args:
            size_text (str): Text containing the size
            
        Returns:
            float: Extracted size in sqm or None if not found
        """
        if not size_text:
            return None
            
        # Extract number followed by m²
        match = re.search(r'(\d+[.,]?\d*)\s*(?:m²|qm)', size_text.replace(',', '.'))
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None
        
    @staticmethod
    def extract_rooms(rooms_text: str) -> Optional[float]:
        """
        Extract number of rooms from text
        
        Args:
            rooms_text (str): Text containing the number of rooms
            
        Returns:
            float: Extracted number of rooms or None if not found
        """
        if not rooms_text:
            return None
            
        # Extract number of rooms (can be decimal like 2.5)
        match = re.search(r'(\d+[.,]?\d*)\s*(?:Zimmer|room|rooms)', rooms_text.replace(',', '.'))
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None
    
    @abstractmethod
    async def search(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for listings with the given filters
        
        Args:
            filters (dict): Dictionary of filters to apply
            
        Returns:
            list: List of dictionaries containing listing data
        """
        pass
    
    @abstractmethod
    async def get_contact_info(self, listing_url: str) -> Dict[str, Any]:
        """
        Get contact information for a listing
        
        Args:
            listing_url (str): URL of the listing
            
        Returns:
            dict: Dictionary containing contact information
        """
        pass
    
    @abstractmethod
    async def apply_via_form(self, listing_url: str, application_data: Dict[str, Any]) -> bool:
        """
        Apply to a listing via a web form
        
        Args:
            listing_url (str): URL of the listing
            application_data (dict): Dictionary containing application data
            
        Returns:
            bool: True if application successful, False otherwise
        """
        pass 