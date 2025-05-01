import os
import sys
import logging
import sqlite3

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_missing_columns():
    """
    Add missing columns to existing database tables.
    This script should be run when the database schema has been updated.
    """
    # Path to the SQLite database
    db_path = os.path.join('database', 'wohnungagent.db')
    
    # Absolute path for when the script is run from different directories
    if not os.path.exists(db_path):
        # Try with parent directory
        db_path = os.path.join('WohnungAgent', 'database', 'wohnungagent.db')
    
    if not os.path.exists(db_path):
        logger.error(f"Database file not found at {db_path}")
        return False
    
    logger.info(f"Migrating database at {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get existing columns in the listings table
        cursor.execute("PRAGMA table_info(listings)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        # Add missing columns if they don't exist
        missing_columns = []
        
        # Check for district column
        if 'district' not in existing_columns:
            missing_columns.append(('district', 'TEXT'))
            logger.info("Adding missing 'district' column")
        
        # Check for other potentially missing columns
        other_columns = [
            ('has_balcony', 'BOOLEAN'),
            ('has_garden', 'BOOLEAN'),
            ('has_elevator', 'BOOLEAN'),
            ('is_furnished', 'BOOLEAN'),
            ('pets_allowed', 'BOOLEAN'),
            ('is_wg', 'BOOLEAN'),
            ('available_from', 'TEXT'),
            ('floor', 'TEXT'),
            ('image_url', 'TEXT'),
            ('description', 'TEXT')
        ]
        
        for col_name, col_type in other_columns:
            if col_name not in existing_columns:
                missing_columns.append((col_name, col_type))
                logger.info(f"Adding missing '{col_name}' column")
        
        # Add each missing column to the database
        for col_name, col_type in missing_columns:
            try:
                # In SQLite, you can't add a NOT NULL column without a default value
                cursor.execute(f"ALTER TABLE listings ADD COLUMN {col_name} {col_type}")
                logger.info(f"Added column '{col_name}' of type '{col_type}'")
            except sqlite3.OperationalError as e:
                logger.error(f"Error adding column '{col_name}': {e}")
        
        # Commit the changes
        conn.commit()
        logger.info("Database migration completed successfully")
        
        return True
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = add_missing_columns()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed. Check the logs for details.")
        sys.exit(1) 