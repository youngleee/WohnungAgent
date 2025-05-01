# WohnungAgent Testing Guide

This guide will help you test the WohnungAgent application locally before deploying it.

## Fixing WebSocket Issues on Windows

If you're encountering WebSocket errors like:
```
TypeError: WebSocketHandler.__init__() missing 2 required positional arguments: 'application' and 'request'
```

This is a known issue with Streamlit, Tornado, and WebSockets on Windows. We've provided several solutions:

## Solution 1: Use the Troubleshooting Script

```
python troubleshoot.py
```

This script will:
1. Check your Python version and installed packages
2. Verify directory structure
3. Confirm Playwright is installed correctly
4. Give you options to fix common issues and run the app

## Solution 2: Use the Custom Runner

```
python run_app.py
```

This script sets up the environment properly before running Streamlit, which helps avoid WebSocket issues.

## Solution 3: Run the Debug Version

```
python -m streamlit run debug_app.py
```

This is a simplified version that tests core functionality without loading all components.

## Manual Installation Steps

If you prefer to set things up manually:

1. **Update your packages**:
   ```
   pip install -r requirements.txt --upgrade
   ```

2. **Install Playwright browser**:
   ```
   python -m playwright install chromium
   ```

3. **Create necessary directories**:
   ```
   mkdir -p temp templates database
   ```

4. **Set up environment variables** (Windows PowerShell):
   ```
   $env:STREAMLIT_SERVER_HEADLESS = "false"
   $env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"
   ```

5. **Run Streamlit with additional flags**:
   ```
   python -m streamlit run app.py --server.maxUploadSize=10 --server.enableWebsocketCompression=false
   ```

## Testing Specific Features

### 1. Search Functionality
- Enter a location (e.g., "Berlin") in the search field
- Set rent range and other filters
- Click "Suchen" button
- Verify listings appear in the results section

### 2. Application Process
- Select a listing you want to apply to
- Upload test documents for SCHUFA, ID, etc.
- Enter personal information
- Click "Bewerben" button
- Check that the application appears in history

### 3. Template Customization
- Go to Settings tab
- Edit the email or application form templates
- Save changes
- Verify your customized template is used when applying

## Troubleshooting Tips

- **Browser console errors**: Open your browser's developer tools (F12) to check for JavaScript errors
- **Server logs**: Look at the terminal output for Python errors
- **Connection issues**: If WebSocket connections fail, try restarting the server
- **Database errors**: Check if the `database` directory exists and has proper permissions

## Getting Additional Help

If you encounter issues not covered in this guide:
1. Check for updated dependencies: `pip list`
2. Verify your Python version: `python --version`
3. Check if Streamlit is installed correctly: `streamlit --version`

For more details, refer to the [Streamlit troubleshooting guide](https://docs.streamlit.io/knowledge-base/using-streamlit/troubleshooting). 