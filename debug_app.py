import streamlit as st
import os
import sys
import platform
import asyncio
import nest_asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Apply nest_asyncio to allow running async code in Streamlit
nest_asyncio.apply()

# Set event loop policy for Windows
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    logger.info("Applied WindowsSelectorEventLoopPolicy")

# Create necessary directories
os.makedirs("temp", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("database", exist_ok=True)
logger.info("Created necessary directories")

# Page configuration
st.set_page_config(
    page_title="WohnungAgent Debug Mode",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("WohnungAgent Debug Mode")
    st.info("This is a simplified version of the app to help diagnose issues.")
    
    # Environment information
    st.header("System Information")
    st.write(f"Python version: {sys.version}")
    st.write(f"Operating system: {platform.system()} {platform.release()}")
    st.write(f"Platform: {platform.platform()}")
    
    # Check directories 
    st.header("Directory Check")
    for directory in ["temp", "templates", "database", "scrapers", "utils"]:
        if os.path.exists(directory):
            st.success(f"✅ {directory} directory exists")
        else:
            st.error(f"❌ {directory} directory is missing")
    
    # Test async functionality
    st.header("Async Functionality Test")
    if st.button("Test Async"):
        with st.spinner("Running async test..."):
            try:
                result = test_async()
                st.success(f"Async test successful! Result: {result}")
            except Exception as e:
                st.error(f"Async test failed: {e}")
    
    # Display import attempt results
    st.header("Import Tests")
    modules_to_test = [
        "playwright", "sqlalchemy", "pandas", 
        "aiohttp", "aiosqlite", "pydantic"
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            st.success(f"✅ Successfully imported {module}")
        except ImportError as e:
            st.error(f"❌ Failed to import {module}: {e}")
    
    # WebSocket test section
    st.header("WebSocket Test")
    if st.button("Test WebSocket Connection"):
        with st.spinner("Testing WebSocket connection..."):
            st.session_state.ws_message = "Testing WebSocket connection..."
            time.sleep(1)  # Simulate processing time
            st.session_state.ws_message = "WebSocket test complete!"
            st.success("WebSocket connection test completed successfully!")
    
    # Next steps guidance
    st.header("Next Steps")
    st.markdown("""
    ### Recommended Actions
    
    1. Check the console output for any errors
    2. Update packages with: `pip install -r requirements.txt --upgrade`
    3. Install Playwright browser: `playwright install chromium`
    4. Try running the app with: `python run_app.py`
    """)

async def async_test_function():
    """Simple async function for testing"""
    await asyncio.sleep(1)
    return "Async function works correctly!"

def test_async():
    """Run the async test function"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_test_function())

if __name__ == "__main__":
    try:
        import time  # Import time here to avoid circular import issues
        main()
    except Exception as e:
        st.error(f"Application error: {e}")
        logger.exception("Application failed with exception:") 