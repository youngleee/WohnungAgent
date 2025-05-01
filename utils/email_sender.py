import smtplib
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Optional, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class EmailSender:
    """Utility for sending emails"""
    
    def __init__(self, custom_credentials: Optional[Dict[str, str]] = None):
        """
        Initialize the email sender with credentials from environment variables or custom credentials
        
        Args:
            custom_credentials (dict, optional): Dictionary containing email credentials:
                - email_address: sender email
                - email_password: sender password
                - email_smtp_server: SMTP server
                - email_smtp_port: SMTP port
        """
        if custom_credentials:
            self.email_address = custom_credentials.get('email_address')
            self.email_password = custom_credentials.get('email_password')
            self.smtp_server = custom_credentials.get('email_smtp_server')
            self.smtp_port = int(custom_credentials.get('email_smtp_port', '587'))
        else:
            # Use environment variables
            self.email_address = os.getenv('EMAIL_ADDRESS')
            self.email_password = os.getenv('EMAIL_PASSWORD')
            self.smtp_server = os.getenv('EMAIL_SMTP_SERVER')
            self.smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))
        
        if not all([self.email_address, self.email_password, self.smtp_server]):
            logger.warning("Email credentials not fully configured.")
    
    def send_application_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
        reply_to: Optional[str] = None
    ) -> bool:
        """
        Send an application email
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            body (str): Email body (HTML)
            attachments (list): List of file paths to attach
            reply_to (str, optional): Reply-to email address
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not all([self.email_address, self.email_password, self.smtp_server]):
            logger.error("Email sender not properly configured")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add Reply-To header if provided
            if reply_to:
                msg['Reply-To'] = reply_to
            
            # Attach body
            msg.attach(MIMEText(body, 'html'))
            
            # Attach files
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as file:
                            part = MIMEApplication(file.read(), Name=os.path.basename(file_path))
                            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                            msg.attach(part)
                    else:
                        logger.warning(f"Attachment not found: {file_path}")
            
            # Connect to server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
                
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False 