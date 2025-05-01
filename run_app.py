import os
import sys
import subprocess
import asyncio
import nest_asyncio
import platform

def setup_env():
    """Set up the environment for running Streamlit"""
    print("Setting up environment for WohnungAgent...")
    
    # Create necessary directories
    os.makedirs("temp", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    os.makedirs("database", exist_ok=True)
    
    # Set event loop policy for Windows
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Apply nest_asyncio
    nest_asyncio.apply()
    
    # Set environment variables to help with Windows WebSocket issues
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'false'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    # For Windows: Disable browser opening automatically to prevent socket conflicts
    if platform.system() == 'Windows':
        os.environ['STREAMLIT_BROWSER_SERVER_ADDRESS'] = 'localhost'
        os.environ['STREAMLIT_SERVER_PORT'] = '8501'
        os.environ['STREAMLIT_CLIENT_TOOLBAR_ITEMS'] = '["fullscreen", "downloadPDF"]'
    
    print("Environment setup complete!")

def run_streamlit():
    """Run the Streamlit application"""
    print("Starting WohnungAgent with Streamlit...")
    print("URL: http://localhost:8501")
    
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py"]
    
    # Add flags to help with stability
    cmd += ["--server.maxUploadSize=10", "--server.enableWebsocketCompression=false"]
    
    try:
        # Run Streamlit as a subprocess
        process = subprocess.Popen(cmd)
        process.wait()
    except KeyboardInterrupt:
        print("\nShutting down WohnungAgent...")
        process.terminate()
    except Exception as e:
        print(f"Error running Streamlit: {e}")

if __name__ == "__main__":
    setup_env()
    run_streamlit() 