import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot settings
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ALLOWED_CHANNEL_IDS = [
        int(channel_id.strip()) 
        for channel_id in os.getenv('ALLOWED_CHANNEL_IDS', '').split(',') 
        if channel_id.strip()
    ]

    # Database settings
    DB_NAME = os.getenv('DB_NAME', 'beat_saber_scores.db')
    BACKUP_FOLDER = os.getenv('BACKUP_FOLDER', 'backups')

    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'bot.log')

    @classmethod
    def is_allowed_channel(cls, channel_id: int) -> bool:
        return channel_id in cls.ALLOWED_CHANNEL_IDS

    @classmethod
    def ensure_backup_folder(cls) -> None:
        if not os.path.exists(cls.BACKUP_FOLDER):
            os.makedirs(cls.BACKUP_FOLDER)
