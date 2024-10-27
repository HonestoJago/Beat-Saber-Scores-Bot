import sqlite3
import logging
from typing import List, Tuple, Optional, Dict
from datetime import datetime
import shutil
import os
from config import Config

class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass

class Database:
    def __init__(self, db_name: str = Config.DB_NAME):
        self.db_name = db_name
        self.conn = None
        self._connect()

    def _connect(self):
        """Establish database connection if not exists"""
        if not self.conn:
            try:
                self.conn = sqlite3.connect(self.db_name)
                logging.info("Database connection established")
            except sqlite3.Error as e:
                logging.error(f"Error connecting to database: {e}")
                raise DatabaseError(f"Failed to connect to database: {e}")

    def _ensure_connection(self):
        """Ensure database connection is active"""
        try:
            # Try a simple query to test connection
            self.conn.execute("SELECT 1")
        except (sqlite3.Error, AttributeError):
            self._connect()

    def execute(self, query: str, params: tuple = ()) -> Optional[List[Tuple]]:
        """Execute a query and return results if any"""
        self._ensure_connection()
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            if query.lower().startswith('select'):
                result = cursor.fetchall()
                self.conn.commit()
                return result
            self.conn.commit()
            return None
        except sqlite3.Error as e:
            logging.error(f"Database error executing {query}: {e}")
            self.conn.rollback()
            raise DatabaseError(f"Database operation failed: {e}")

    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logging.info("Database connection closed")

    def __enter__(self):
        self._ensure_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.conn.rollback()
        else:
            self.conn.commit()

    def init_db(self) -> None:
        """Initialize database tables"""
        try:
            self.execute('''
                CREATE TABLE IF NOT EXISTS levels (
                    level_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level_name TEXT UNIQUE NOT NULL
                )
            ''')
            
            self.execute('''
                CREATE TABLE IF NOT EXISTS scores (
                    user_id TEXT,
                    user_name TEXT,
                    level_id INTEGER,
                    difficulty TEXT,
                    score INTEGER,
                    PRIMARY KEY (user_id, level_id, difficulty),
                    FOREIGN KEY (level_id) REFERENCES levels(level_id)
                )
            ''')
            
            logging.info("Database initialization completed successfully")
        except Exception as e:
            logging.error(f"Failed to initialize database: {e}")
            raise

    def backup(self) -> str:
        """Create a backup of the database"""
        try:
            backup_filename = os.path.join(
                Config.BACKUP_FOLDER,
                f"beat_saber_scores_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            shutil.copy2(self.db_name, backup_filename)
            logging.info(f"Database backed up to {backup_filename}")
            return backup_filename
        except Exception as e:
            logging.error(f"Backup failed: {e}")
            raise DatabaseError(f"Backup failed: {e}")

    def get_user_scores(self, user_id: str) -> List[Tuple]:
        """Get all scores for a specific user"""
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT s.level_id, l.level_name, s.difficulty, s.score 
                FROM scores s
                JOIN levels l ON s.level_id = l.level_id
                WHERE s.user_id = ?
                ORDER BY l.level_name, s.difficulty
            ''', (user_id,))
            result = cursor.fetchall()
            # Debug logging
            logging.debug(f"Raw query result for user {user_id}: {result}")
            return result if result is not None else []
        except Exception as e:
            logging.error(f"Error getting scores for user {user_id}: {e}")
            return []

    def get_level_leaderboard(self, level_id: int, difficulty: str) -> List[Tuple]:
        """Get leaderboard for a specific level and difficulty"""
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT user_name, score 
                FROM scores 
                WHERE level_id = ? AND difficulty = ?
                ORDER BY score DESC, user_name ASC
            ''', (level_id, difficulty))
            result = cursor.fetchall()
            # Debug logging
            logging.debug(f"Leaderboard query for level {level_id} ({difficulty}): Found {len(result) if result else 0} scores")
            return result if result is not None else []
        except Exception as e:
            logging.error(f"Error getting leaderboard for level {level_id} ({difficulty}): {e}")
            return []

    def insert_score(self, user_id: str, user_name: str, level_id: int, 
                    difficulty: str, score: int) -> None:
        """Insert or update a score"""
        self.execute('''
            INSERT OR REPLACE INTO scores (user_id, user_name, level_id, difficulty, score)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, user_name, level_id, difficulty, score))
        logging.info(f"Score inserted: {user_name} - Level ID: {level_id} ({difficulty}): {score}")

    def get_levels(self) -> List[Tuple]:
        """Get all levels"""
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT level_id, level_name 
                FROM levels 
                ORDER BY level_name
            ''')
            result = cursor.fetchall()
            # Debug logging
            logging.debug(f"Retrieved {len(result) if result else 0} levels")
            return result if result is not None else []
        except Exception as e:
            logging.error(f"Error getting levels: {e}")
            return []

    def add_level(self, level_name: str) -> bool:
        """Add a new level"""
        try:
            self.execute('INSERT INTO levels (level_name) VALUES (?)', (level_name,))
            logging.info(f"New level added: {level_name}")
            return True
        except sqlite3.IntegrityError:
            logging.warning(f"Level already exists: {level_name}")
            return False

    def get_user_scores_by_name(self, user_name: str) -> List[Tuple]:
        """Get all scores for a specific user by name"""
        return self.execute('''
            SELECT s.level_id, s.difficulty, s.score 
            FROM scores s
            WHERE s.user_name = ?
            ORDER BY s.level_id, s.difficulty
        ''', (user_name,))

    def get_unique_users(self) -> List[str]:
        """Get list of all unique usernames"""
        result = self.execute('SELECT DISTINCT user_name FROM scores ORDER BY user_name')
        return [row[0] for row in result] if result else []
