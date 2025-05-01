import os
import sys
import platform
import subprocess
import asyncio

def fix_windows_asyncio():
    """Apply specific fixes for Windows asyncio"""
    if platform.system() == 'Windows':
        # Set the event loop policy
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        # Set environment variables to help Streamlit
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['STREAMLIT_SERVER_HEADLESS'] = 'false'
        os.environ['STREAMLIT_SERVER_PORT'] = '8502'  # Use a different port
        
        # Tornado-specific settings to avoid WebSocket issues
        os.environ['TORNADO_DISABLE_WEBSOCKET'] = '1'
        
        # Add settings to work around WebSocket issues
        os.environ['STREAMLIT_SERVER_ENABLE_STATIC_SERVING'] = 'true'
        os.environ['STREAMLIT_SERVER_MAX_UPLOAD_SIZE'] = '5'
        os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'true'
        os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

def run_streamlit_directly():
    """Run Streamlit using a direct approach that works better on Windows"""
    print("Starting WohnungAgent on Windows...")
    print("This approach bypasses some Streamlit features but should work more reliably.")
    
    # Ensure directories exist
    os.makedirs("temp", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    os.makedirs("database", exist_ok=True)
    
    # Create the command
    python_exe = sys.executable
    module_path = "-m"
    streamlit_module = "streamlit"
    run_command = "run"
    app_path = "app.py"
    
    # Add specific parameters to avoid WebSocket issues
    disable_websocket_compression = "--server.enableWebsocketCompression=false"
    max_upload_size = "--server.maxUploadSize=5"
    port = "--server.port=8502"
    address = "--server.address=localhost"
    browser_server_address = "--browser.serverAddress=localhost"
    
    # Build the command
    cmd = [
        python_exe, module_path, streamlit_module, run_command, app_path,
        disable_websocket_compression, max_upload_size, port, address, 
        browser_server_address
    ]
    
    print("=" * 50)
    print("Starting Streamlit with special configuration...")
    print("URL: http://localhost:8502")
    print("=" * 50)
    print("Press Ctrl+C to exit")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        
if __name__ == "__main__":
    fix_windows_asyncio()
    run_streamlit_directly() 