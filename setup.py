#!/usr/bin/env python3
import subprocess
import sys
import os

def setup_environment():
    """Set up the environment for WohnungAgent"""
    print("Setting up WohnungAgent environment...")
    
    # Install dependencies
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Install Playwright browsers
    print("Installing Playwright browsers...")
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    
    # Create necessary directories
    for directory in ["temp", "templates", "database"]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")
    
    # Check if .env file exists, create from example if not
    if not os.path.exists(".env") and os.path.exists(".env.example"):
        print("Creating .env file from example...")
        with open(".env.example", "r") as example_file:
            example_content = example_file.read()
        
        with open(".env", "w") as env_file:
            env_file.write(example_content)
        
        print("Created .env file. Please edit it with your email credentials.")
    
    print("\nSetup complete! You can now run the application with:")
    print("streamlit run app.py")

if __name__ == "__main__":
    setup_environment() 