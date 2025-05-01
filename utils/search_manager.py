import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
import time
from scrapers import (
    BaseScraper,
    WGGesuchtScraper,
    ImmoScoutScraper,
    ImmonetScraper,
    ImmoweltScraper
)

logger = logging.getLogger(__name__)

class SearchManager:
    """
    Manages the search process across multiple websites
    """
    
    def __init__(self, sources: Optional[List[str]] = None):
        """
        Initialize the search manager
        
        Args:
            sources (list): List of sources to search (defaults to all)
        """
        self.sources = sources or ['wg_gesucht', 'immoscout24', 'immonet', 'immowelt']
        self.scrapers = {}
        
    async def initialize_scrapers(self, headless: bool = True):
        """
        Initialize all scrapers
        
        Args:
            headless (bool): Whether to run browsers in headless mode
        """
        if 'wg_gesucht' in self.sources:
            self.scrapers['wg_gesucht'] = WGGesuchtScraper(headless=headless)
            
        if 'immoscout24' in self.sources:
            self.scrapers['immoscout24'] = ImmoScoutScraper(headless=headless)
            
        if 'immonet' in self.sources:
            self.scrapers['immonet'] = ImmonetScraper(headless=headless)
            
        if 'immowelt' in self.sources:
            self.scrapers['immowelt'] = ImmoweltScraper(headless=headless)
            
        # Initialize all scrapers
        for source, scraper in self.scrapers.items():
            try:
                await scraper.initialize()
                logger.info(f"Initialized scraper for {source}")
            except Exception as e:
                logger.error(f"Error initializing scraper for {source}: {e}")
                
    async def close_scrapers(self):
        """Close all scrapers"""
        for source, scraper in self.scrapers.items():
            try:
                await scraper.close()
                logger.info(f"Closed scraper for {source}")
            except Exception as e:
                logger.error(f"Error closing scraper for {source}: {e}")
                
    async def search_all(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search across all websites with the given filters
        
        Args:
            filters (dict): Dictionary of filters to apply
            
        Returns:
            list: Combined list of listings from all sources
        """
        if not self.scrapers:
            await self.initialize_scrapers()
            
        all_listings = []
        search_tasks = []
        
        # Create a search task for each scraper
        for source, scraper in self.scrapers.items():
            task = asyncio.create_task(self._search_with_source(source, scraper, filters))
            search_tasks.append(task)
            
        # Wait for all search tasks to complete
        results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Search error: {result}")
            elif isinstance(result, list):
                all_listings.extend(result)
                
        return all_listings
        
    async def _search_with_source(
        self, 
        source: str, 
        scraper: BaseScraper, 
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Search a single source with the given filters
        
        Args:
            source (str): Name of the source
            scraper (BaseScraper): The scraper for the source
            filters (dict): Dictionary of filters to apply
            
        Returns:
            list: List of listings from the source
        """
        try:
            logger.info(f"Searching {source} with filters: {filters}")
            listings = await scraper.search(filters)
            logger.info(f"Found {len(listings)} listings on {source}")
            return listings
        except Exception as e:
            logger.error(f"Error searching {source}: {e}")
            return []
    
    def combine_with_database(self, new_listings: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Combine new listings from scraping with existing listings from the database
        
        Args:
            new_listings (list): List of new listings from scraping
            filters (dict): Filters to apply to database listings
            
        Returns:
            list: Combined list of listings
        """
        # Import database operations here to avoid circular imports
        try:
            from database.operations import get_listings_with_filters
        except ImportError as e:
            logger.error(f"Error importing database operations: {e}")
            # If we can't import the database module, just return the new listings
            for listing in new_listings:
                listing['from_db'] = False
            return new_listings
        
        try:
            # Get existing listings from database
            db_listings = get_listings_with_filters(filters)
            
            # Convert DB listings to dictionaries
            db_listings_dict = []
            try:
                db_listings_dict = [
                    {
                        'id': listing.id,
                        'title': listing.title,
                        'price': listing.price,
                        'size': listing.size,
                        'rooms': listing.rooms,
                        'location': listing.location,
                        'url': listing.url,
                        'contact_email': getattr(listing, 'contact_email', None),
                        'has_form': getattr(listing, 'has_form', False),
                        'has_balcony': getattr(listing, 'has_balcony', False),
                        'has_garden': getattr(listing, 'has_garden', False),
                        'has_elevator': getattr(listing, 'has_elevator', False),
                        'is_furnished': getattr(listing, 'is_furnished', False),
                        'pets_allowed': getattr(listing, 'pets_allowed', False),
                        'is_wg': getattr(listing, 'is_wg', False),
                        'district': getattr(listing, 'district', None),
                        'available_from': getattr(listing, 'available_from', None),
                        'floor': getattr(listing, 'floor', None),
                        'image_url': getattr(listing, 'image_url', None),
                        'source': listing.source,
                        'created_at': listing.created_at,
                        'from_db': True
                    }
                    for listing in db_listings
                ]
            except Exception as e:
                logger.error(f"Error converting database listings to dictionaries: {e}")
                # Continue with an empty list if there's an error
                db_listings_dict = []
            
            # Add a flag to new listings
            for listing in new_listings:
                listing['from_db'] = False
                
            # Combine lists and ensure uniqueness by URL
            all_listings = db_listings_dict.copy()
            db_urls = {listing['url'] for listing in db_listings_dict}
            
            for listing in new_listings:
                if listing['url'] not in db_urls:
                    all_listings.append(listing)
            
            logger.info(f"Combined {len(db_listings_dict)} database listings with {len(new_listings)} new listings")
            return all_listings
            
        except Exception as e:
            logger.error(f"Error combining listings with database: {e}")
            # If we can't access the database, just return the new listings
            for listing in new_listings:
                listing['from_db'] = False
            return new_listings 