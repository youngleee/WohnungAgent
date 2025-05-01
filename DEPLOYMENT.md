# WohnungAgent Deployment Guide

This guide will help you deploy the WohnungAgent application to Streamlit Cloud and make it available to your customers.

## Deploying to Streamlit Cloud

### Prerequisites

1. A GitHub account
2. Your WohnungAgent code in a GitHub repository
3. A Streamlit Cloud account (free tier available)

### Deployment Steps

1. **Push your code to GitHub**
   - Create a new repository or use an existing one
   - Push the WohnungAgent code to the repository

2. **Sign up for Streamlit Cloud**
   - Visit [Streamlit Cloud](https://streamlit.io/cloud)
   - Sign in with your GitHub account

3. **Deploy the application**
   - Click "New app" in the Streamlit Cloud dashboard
   - Select your GitHub repository
   - Set the main file path to `app.py`
   - Under "Advanced Settings":
     - Set Python version to 3.10
     - Add any secrets as described below (optional)
   - Click "Deploy"

4. **Verify deployment**
   - Once deployed, Streamlit Cloud will provide a URL for your application
   - Visit the URL to ensure everything is working correctly

## User Experience - Quick Start

WohnungAgent has been designed to be as user-friendly as possible. Your customers can:

1. **Visit the website** - No installation or setup required
2. **Enter their personal info** - Name, email, phone number, etc. in the sidebar
3. **Set search filters** - Location, price range, size, etc.
4. **Run the search** - With a single click
5. **Apply to apartments** - With form auto-filling

## Customer Usage Guide

The application allows your customers to:

### Search for apartments
1. Set search filters in the sidebar under "Suchfilter" tab
2. Select which websites to search (WG-Gesucht, Immobilienscout24, etc.)
3. Click "Suche starten" to find available apartments

### Apply for apartments
1. Enter personal information in the sidebar under "Persönliche Daten" tab
2. Upload required documents (SCHUFA, income proof, ID)
3. Click "Bewerben" on any apartment listing to submit an application

### Track applications
1. View all submitted applications in the "Bewerbungen" tab
2. See status (pending, successful, failed)
3. Access links to listings

## Data Privacy Considerations

The WohnungAgent application handles user data as follows:

1. **Personal Information**: Stored only in the browser session and is never persisted between sessions
2. **Document Storage**: Documents are stored temporarily on the server and are removed when the session ends
3. **Database**: Applications and listings are stored in a SQLite database

## Customization Options

If you want to customize the application:

1. **Form Templates**: Modify the templates in the `templates` directory
2. **Theme**: Adjust the `.streamlit/config.toml` file to change colors and appearance
3. **Scrapers**: Update scraper files in the `scrapers` directory to support different websites

## Limitations of Streamlit Cloud Deployment

1. **Concurrent Users**: Free tier has limited compute resources
2. **Session Duration**: Sessions may time out after periods of inactivity
3. **Storage**: Temporary files are cleared periodically

## Monitoring & Maintenance

- Check the Streamlit Cloud dashboard for app metrics and logs
- Update the code in your GitHub repository to deploy new versions

## Support

If your customers encounter issues:
- Check the application logs in the Streamlit Cloud dashboard
- Verify the search parameters are valid for the target websites
- Ensure the site scrapers are up-to-date with the latest website layouts 