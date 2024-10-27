import csv
import os
import logging
from database import Database
from config import Config

def init_beat_saber_levels(csv_file: str) -> None:
    """Initialize the database with levels from CSV file, preserving existing levels"""
    db = Database()
    
    try:
        # Initialize database tables if they don't exist
        db.init_db()
        
        # Get existing levels
        with Database() as db:
            existing_levels = db.execute("SELECT level_name FROM levels")
            existing_level_names = {level[0] for level in existing_levels} if existing_levels else set()
        
        # Read and insert only new levels
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            levels_added = 0
            for row in csv_reader:
                level_name = row[0].strip()
                if level_name and level_name not in existing_level_names:
                    if db.add_level(level_name):
                        levels_added += 1
                        existing_level_names.add(level_name)
                    
        if levels_added > 0:
            logging.info(f"Added {levels_added} new levels from {csv_file}")
            print(f"Added {levels_added} new levels from {csv_file}")
        else:
            print("No new levels to add.")
        
    except Exception as e:
        error_msg = f"Error initializing Beat Saber levels: {e}"
        logging.error(error_msg)
        print(error_msg)
        raise

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        filename=Config.LOG_FILE,
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s:%(levelname)s:%(message)s'
    )
    
    csv_file = 'beat_saber_levels.csv'
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        exit(1)
        
    init_beat_saber_levels(csv_file)
