#!/usr/bin/env python
"""
Script to run database migrations for WohnungAgent
"""
import os
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the migration function
from WohnungAgent.database.migrate import add_missing_columns

if __name__ == "__main__":
    print("Running database migration for WohnungAgent...")
    success = add_missing_columns()
    
    if success:
        print("✅ Migration completed successfully!")
        print("The district column and any other missing columns have been added to the database.")
        print("You can now restart the application.")
    else:
        print("❌ Migration failed. Please check the logs for details.")
        sys.exit(1) 