import discord
from discord import app_commands
import logging
import asyncio
from config import Config
from database import Database
from cogs.scores import ScoresCog

# Set up logging
logging.basicConfig(
    filename=Config.LOG_FILE, 
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s:%(levelname)s:%(message)s'
)

class BeatSaberBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        self.db = Database()

    async def setup_hook(self):
        try:
            # Initialize database
            self.db.init_db()
            
            # Verify database has content
            levels = self.db.get_levels()
            if not levels:
                from init_beat_saber_levels import init_beat_saber_levels
                init_beat_saber_levels('beat_saber_levels.csv')
                logging.info("Initialized levels from CSV")
            
            # Add commands from cog
            scores_cog = ScoresCog(self)
            for command in scores_cog.get_app_commands():
                self.tree.add_command(command)
            
            # Start automatic backup task
            self.loop.create_task(self._auto_backup())
        except Exception as e:
            logging.error(f"Error in setup_hook: {e}")
            raise

    async def _auto_backup(self):
        """Automatic backup task that runs every 24 hours"""
        while True:
            try:
                await asyncio.sleep(24 * 60 * 60)  # 24 hours
                backup_file = self.db.backup()
                logging.info(f"Automatic backup created: {backup_file}")
            except Exception as e:
                logging.error(f"Error during automatic backup: {e}")

    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()

# Initialize bot
client = BeatSaberBot()

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    logging.info(f'Bot logged in as {client.user}')
    try:
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} command(s)")
        logging.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
        logging.error(f"Failed to sync commands: {e}")

# Ensure backup folder exists
Config.ensure_backup_folder()

# Run the bot
client.run(Config.BOT_TOKEN)
