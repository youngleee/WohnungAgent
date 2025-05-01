# WohnungAgent - AI Flat Hunting Assistant

WohnungAgent is an automated tool that helps you find and apply to apartment listings in Germany. It scrapes popular rental websites, filters properties based on your criteria, and can automatically apply to suitable listings.

## Features

- **Multi-site Scraping**: Extracts listings from WG-Gesucht, Immonet, Immowelt, and Immobilienscout24
- **Customizable Filters**: Filter by location, rent, size, number of rooms, and more
- **Automated Applications**: Send emails or fill web forms automatically with your details and documents
- **Application Tracking**: Keep track of where you've applied to avoid duplicates
- **Simple UI**: Easy-to-use Streamlit interface

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Install Playwright browsers:
   ```
   playwright install
   ```
4. Create a `.env` file with your email credentials:
   ```
   EMAIL_ADDRESS=your_email@example.com
   EMAIL_PASSWORD=your_password
   EMAIL_SMTP_SERVER=smtp.example.com
   EMAIL_SMTP_PORT=587
   ```
5. Run the application:
   ```
   streamlit run app.py
   ```

## Usage

1. Set your filter criteria in the sidebar
2. Click "Start Search" to begin scraping
3. Review matching listings
4. Apply automatically or manually to listings
5. Monitor application status and success

## Project Structure

- `app.py`: Main Streamlit application
- `scrapers/`: Contains scrapers for different websites
- `database/`: Database models and operations
- `utils/`: Utility functions
- `templates/`: Email templates and application text

## License

MIT

## Disclaimer

This tool is for educational purposes only. Please use responsibly and in accordance with the terms of service of the websites being scraped. 