import sqlite3
import csv
import os

def init_beat_saber_levels(csv_file):
    conn = sqlite3.connect('beat_saber_scores.db')
    cursor = conn.cursor()

    try:
        # Create levels table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS levels (
                level_id INTEGER PRIMARY KEY AUTOINCREMENT,
                level_name TEXT UNIQUE NOT NULL
            )
        ''')

        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                cursor.execute('INSERT OR IGNORE INTO levels (level_name) VALUES (?)', (row[0],))

        conn.commit()
        print(f"Successfully initialized Beat Saber levels from {csv_file}")
    except Exception as e:
        print(f"Error initializing Beat Saber levels: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    csv_file = 'beat_saber_levels.csv'  # Make sure this file exists with the correct format
    init_beat_saber_levels(csv_file)
