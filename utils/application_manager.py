import logging
import os
from typing import Dict, Any, List, Optional, Tuple
import asyncio
from database import (
    add_listing, 
    get_listing_by_url, 
    create_application, 
    update_application_status,
    has_applied_to_listing
)
from .email_sender import EmailSender
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class ApplicationManager:
    """
    Manages the application process for listings
    """
    
    def __init__(self, application_data: Dict[str, Any], attachments: Optional[List[str]] = None, email_settings: Optional[Dict[str, str]] = None):
        """
        Initialize the application manager
        
        Args:
            application_data (dict): Dictionary containing application data
            attachments (list): List of file paths to attach to emails
            email_settings (dict, optional): Dictionary containing email credentials
        """
        self.application_data = application_data
        self.attachments = attachments or []
        self.email_settings = email_settings
        
        # Use service email as fallback if user email settings are not provided
        if email_settings and all([
            email_settings.get('email_address'),
            email_settings.get('email_password'),
            email_settings.get('email_smtp_server')
        ]):
            self.email_sender = EmailSender(custom_credentials=email_settings)
            self.using_service_email = False
        else:
            # Fall back to service email from environment variables
            self.email_sender = EmailSender()
            self.using_service_email = True
            logger.info("Using service email account for applications")
        
    async def apply_to_listing(self, scraper: BaseScraper, listing: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Apply to a listing using the appropriate method
        
        Args:
            scraper (BaseScraper): The scraper for the website
            listing (dict): The listing data
            
        Returns:
            tuple: (success, message)
        """
        # Check if we've already applied
        existing_listing = get_listing_by_url(listing['url'])
        
        if existing_listing:
            if has_applied_to_listing(existing_listing.id):
                return False, "Already applied to this listing"
            listing_id = existing_listing.id
        else:
            # Add listing to database
            new_listing = add_listing(listing)
            if not new_listing:
                return False, "Failed to add listing to database"
            listing_id = new_listing.id
        
        # Get detailed contact info
        contact_info = await scraper.get_contact_info(listing['url'])
        
        # Update listing with additional info
        listing.update(contact_info)
        
        # Apply via email if available
        if listing.get('email'):
            success = self._apply_via_email(listing)
            method = "email"
        # Otherwise apply via form
        elif listing.get('has_form', False):
            success = await scraper.apply_via_form(listing['url'], self.application_data)
            method = "form"
        else:
            return False, "No contact method available"
            
        # Log the application in database
        status = "success" if success else "failed"
        application = create_application(
            listing_id=listing_id,
            method=method,
            status=status
        )
        
        if success:
            return True, f"Successfully applied via {method}"
        else:
            return False, f"Failed to apply via {method}"
            
    def _apply_via_email(self, listing: Dict[str, Any]) -> bool:
        """
        Apply to a listing via email
        
        Args:
            listing (dict): The listing data
            
        Returns:
            bool: True if application successful, False otherwise
        """
        if not listing.get('email'):
            logger.error("No email address provided for listing")
            return False
        
        # Add reply-to header if using service email account
        reply_to = None
        if self.using_service_email and self.application_data.get('email'):
            reply_to = self.application_data.get('email')
            
        # Prepare email subject and body
        subject = f"Application for {listing['title']}"
        
        # Create HTML email body
        body = f"""
        <html>
        <body>
            <p>Dear landlord,</p>
            
            <p>I am writing to express my interest in the apartment listed as "{listing['title']}" located in {listing['location']}.</p>
            
            <p>{self.application_data.get('message', '')}</p>
            
            <p>My contact details:</p>
            <ul>
                <li>Name: {self.application_data.get('first_name', '')} {self.application_data.get('last_name', '')}</li>
                <li>Email: {self.application_data.get('email', '')}</li>
                <li>Phone: {self.application_data.get('phone', '')}</li>
            </ul>
            
            <p>I have attached the required documents to this email.</p>
            
            <p>I look forward to hearing from you soon.</p>
            
            <p>Kind regards,<br>
            {self.application_data.get('first_name', '')} {self.application_data.get('last_name', '')}</p>
        </body>
        </html>
        """
        
        # Send email
        return self.email_sender.send_application_email(
            to_email=listing['email'],
            subject=subject,
            body=body,
            attachments=self.attachments,
            reply_to=reply_to
        ) 