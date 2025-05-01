import os
import sys
import subprocess
import importlib
import pkg_resources

def print_header(message):
    print("\n" + "=" * 50)
    print(f" {message}")
    print("=" * 50)

def check_python_version():
    print_header("Python Version")
    print(f"Python version: {sys.version}")
    if sys.version_info.major == 3 and sys.version_info.minor >= 8:
        print("✅ Python version is compatible.")
    else:
        print("❌ Python version may be incompatible. Python 3.8+ is recommended.")

def check_installed_packages():
    print_header("Installed Packages")
    required_packages = [
        "streamlit", "playwright", "sqlalchemy", "pydantic", "python-dotenv",
        "pandas", "asyncio", "aiohttp", "aiosqlite", "apscheduler", 
        "nest_asyncio", "tornado", "watchdog"
    ]
    
    installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
    
    for package in required_packages:
        if package in installed_packages:
            print(f"✅ {package}: {installed_packages[package]}")
        else:
            print(f"❌ {package}: Not installed")

def check_directories():
    print_header("Directory Structure")
    required_dirs = ["temp", "templates", "database", "scrapers", "utils"]
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ {directory} directory exists")
        else:
            print(f"❌ {directory} directory is missing")
            try:
                os.makedirs(directory)
                print(f"  Created {directory} directory")
            except Exception as e:
                print(f"  Failed to create {directory} directory: {e}")

def check_playwright():
    print_header("Playwright Setup")
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "--help"], 
                       stdout=subprocess.PIPE, 
                       stderr=subprocess.PIPE)
        print("✅ Playwright is installed.")
    except Exception as e:
        print(f"❌ Playwright check failed: {e}")

def fix_common_issues():
    print_header("Fixing Common Issues")
    
    # Fix 1: Install missing packages
    print("Installing/upgrading required packages...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "-r", "requirements.txt"], 
                       stdout=subprocess.PIPE)
        print("✅ Packages installed/upgraded")
    except Exception as e:
        print(f"❌ Failed to install packages: {e}")
    
    # Fix 2: Install Playwright browsers
    print("Installing Playwright browsers...")
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                       stdout=subprocess.PIPE)
        print("✅ Playwright browsers installed")
    except Exception as e:
        print(f"❌ Failed to install Playwright browsers: {e}")
    
    # Fix 3: Create necessary directories
    print("Creating necessary directories...")
    for directory in ["temp", "templates", "database"]:
        os.makedirs(directory, exist_ok=True)
    print("✅ Directories created")

def run_streamlit():
    print_header("Running Streamlit")
    print("Starting Streamlit server... Press Ctrl+C to exit")
    print("If the browser doesn't open automatically, visit: http://localhost:8501")
    print()
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])

if __name__ == "__main__":
    print_header("WohnungAgent Troubleshooter")
    
    check_python_version()
    check_installed_packages()
    check_directories()
    check_playwright()
    
    print_header("Recommended Actions")
    print("1. Run automatic fixes")
    print("2. Run the Streamlit application")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ")
    
    if choice == "1":
        fix_common_issues()
        input("\nPress Enter to continue...")
        run_streamlit()
    elif choice == "2":
        run_streamlit()
    else:
        print("Exiting...") 