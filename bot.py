import os
import discord
from discord import app_commands, Embed
import sqlite3
from typing import Literal
from datetime import datetime
import logging
import asyncio
import shutil
import dotenv
import csv

# Load environment variables
dotenv.load_dotenv()

# Set up logging
logging.basicConfig(filename='bot.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Initialize Discord bot with appropriate intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Constants
ALLOWED_CHANNEL_IDS = [
    1295047901910925322,
    1290127556611149915
]
BACKUP_FOLDER = 'backups'

# Ensure backup folder exists
if not os.path.exists(BACKUP_FOLDER):
    os.makedirs(BACKUP_FOLDER)
# Database functions
def init_db():
    try:
        conn = sqlite3.connect('beat_saber_scores.db')
        cursor = conn.cursor()

        # Create levels table (simplified)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS levels (
                level_id INTEGER PRIMARY KEY AUTOINCREMENT,
                level_name TEXT UNIQUE NOT NULL
            )
        ''')

        # Create scores table (updated)
        cursor.execute('''
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

        conn.commit()
        logging.info("Database initialization checked and completed.")
    except sqlite3.Error as e:
        logging.error(f"Error during database initialization check: {e}")
    finally:
        conn.close()

def insert_score(user_id, user_name, level_id, difficulty, score):
    conn = sqlite3.connect('beat_saber_scores.db')
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO scores (user_id, user_name, level_id, difficulty, score)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, user_name, level_id, difficulty, score))
        conn.commit()
        logging.info(f"Score inserted: {user_name} - Level ID: {level_id} ({difficulty}): {score}")
    except sqlite3.Error as e:
        logging.error(f"Error inserting score: {e}")
    finally:
        conn.close()

def get_user_scores(user_id):
    try:
        conn = sqlite3.connect('beat_saber_scores.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT s.level_id, l.level_name, s.difficulty, s.score 
            FROM scores s
            JOIN levels l ON s.level_id = l.level_id
            WHERE s.user_id = ?
            ORDER BY s.level_id, s.difficulty
        ''', (user_id,))
        scores = cursor.fetchall()

        return scores
    except sqlite3.Error as e:
        logging.error(f"Error fetching user scores: {e}")
        return []
    finally:
        conn.close()

def get_user_scores_by_name(user_name):
    try:
        conn = sqlite3.connect('beat_saber_scores.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT level_id, difficulty, score FROM scores WHERE user_name = ?
        ''', (user_name,))
        scores = cursor.fetchall()

    except sqlite3.Error as e:
        logging.error(f"Error fetching scores for user {user_name}: {e}")
        scores = []
    finally:
        conn.close()

    return scores

# Function to perform database backup
def perform_backup():
    try:
        backup_filename = os.path.join(BACKUP_FOLDER, f"beat_saber_scores_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        shutil.copy2('beat_saber_scores.db', backup_filename)
        logging.info(f"Database backed up to {backup_filename}")
        return f"Database backed up to {backup_filename}"
    except Exception as e:
        logging.error(f"Error during database backup: {e}")
        return f"Error during database backup: {str(e)}"

# Helper functions
def is_allowed_channel(interaction: discord.Interaction) -> bool:
    return interaction.channel_id in ALLOWED_CHANNEL_IDS

# Function to add a new level (admin only)
def add_level(level_name):
    try:
        conn = sqlite3.connect('beat_saber_scores.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO levels (level_name)
            VALUES (?)
        ''', (level_name,))
        conn.commit()
        logging.info(f"New level added: {level_name}")
        return True
    except sqlite3.Error as e:
        logging.error(f"Error adding new level: {e}")
        return False
    finally:
        conn.close()

# Function to get all levels
def get_levels():
    try:
        conn = sqlite3.connect('beat_saber_scores.db')
        cursor = conn.cursor()
        cursor.execute("SELECT level_id, level_name FROM levels ORDER BY level_name")
        levels = cursor.fetchall()
        return levels
    except sqlite3.Error as e:
        logging.error(f"Error fetching levels: {e}")
        return []
    finally:
        conn.close()

def get_level_leaderboard(level_id, difficulty):
    try:
        conn = sqlite3.connect('beat_saber_scores.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user_name, score FROM scores 
            WHERE level_id = ? AND difficulty = ?
            ORDER BY score DESC, user_name ASC
        ''', (level_id, difficulty))
        scores = cursor.fetchall()

    except sqlite3.Error as e:
        logging.error(f"Error fetching level leaderboard: {e}")
        scores = []
    finally:
        conn.close()

    return scores

# Constants for score validation
MIN_SCORE = 0
MAX_SCORE = 3000000  # Adjust this based on the maximum possible score in Beat Saber

# Valid difficulty levels
VALID_DIFFICULTIES = ['Easy', 'Normal', 'Hard', 'Expert', 'Expert+']

@tree.command(name="score", description="Record a score for a Beat Saber level")
@app_commands.describe(
    level="Name of the level",
    difficulty="Difficulty of the level",
    score="Your score for the level (0 to 3,000,000)"
)
async def score(interaction: discord.Interaction, 
                level: str,
                difficulty: str,
                score: int):
    if not is_allowed_channel(interaction):
        await interaction.response.send_message("This command can only be used in designated channels.", ephemeral=True)
        return

    # Validate difficulty
    if difficulty not in VALID_DIFFICULTIES:
        await interaction.response.send_message(f"Invalid difficulty. Please choose from: {', '.join(VALID_DIFFICULTIES)}", ephemeral=True)
        return

    # Validate score range
    if not MIN_SCORE <= score <= MAX_SCORE:
        await interaction.response.send_message(f"Invalid score. Please enter a score between {MIN_SCORE} and {MAX_SCORE}.", ephemeral=True)
        return

    # Fetch the valid levels list from the database
    levels = get_levels()
    
    # Check if the input level exactly matches any of the valid levels (case-sensitive match)
    matched_level = next((l for l in levels if l[1] == level), None)
    if not matched_level:
        await interaction.response.send_message(f"Invalid level name. Please select a level from the autocomplete menu.", ephemeral=True)
        return

    user_id = str(interaction.user.id)
    user_name = interaction.user.name

    # Insert score into the database using the matched level ID
    insert_score(user_id, user_name, matched_level[0], difficulty, score)
    
    response = f"Score of {score} recorded for {matched_level[1]} ({difficulty})."
    await interaction.response.send_message(response, ephemeral=True)
    
    log_message = f"Score submitted: {user_name} - {matched_level[1]} ({difficulty}): {score}"
    logging.info(log_message)
    print(log_message)  # Print to the terminal

@score.autocomplete('level')
async def level_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    if not is_allowed_channel(interaction):
        return []
    levels = get_levels()
    return [
        app_commands.Choice(name=level[1], value=level[1])
        for level in levels if current.lower() in level[1].lower()
    ][:25]  # Discord has a limit of 25 choices

@score.autocomplete('difficulty')
async def difficulty_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    return [
        app_commands.Choice(name=diff, value=diff)
        for diff in VALID_DIFFICULTIES if current.lower() in diff.lower()
    ]

@tree.command(name="add_level", description="Add a new Beat Saber level (Admin only)")
@app_commands.describe(level_name="Name of the new level")
async def add_level_command(interaction: discord.Interaction, level_name: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    success = add_level(level_name)
    if success:
        await interaction.response.send_message(f"Level '{level_name}' added successfully.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Failed to add level '{level_name}'.", ephemeral=True)

@tree.command(name="leaderboard", description="Show leaderboard for a specific level")
@app_commands.describe(
    level="Name of the level",
    difficulty="Difficulty of the level"
)
async def leaderboard(interaction: discord.Interaction,
                      level: str,
                      difficulty: Literal['Easy', 'Normal', 'Hard', 'Expert', 'Expert+']):
    if not is_allowed_channel(interaction):
        await interaction.response.send_message("This command can only be used in designated channels.", ephemeral=True)
        return

    levels = get_levels()
    matched_level = next((l for l in levels if l[1] == level), None)
    if not matched_level:
        await interaction.response.send_message(f"Level '{level}' not found.")
        return

    scores = get_level_leaderboard(matched_level[0], difficulty)

    if not scores:
        await interaction.response.send_message(f"No scores recorded yet for {matched_level[1]} ({difficulty}).")
        return
    
    embed = Embed(title=f"{matched_level[1]} Leaderboard", description=f"Difficulty: {difficulty}", color=0x00ff00)
    
    leaderboard_text = ""
    for i, (name, score) in enumerate(scores[:10], 1):
        medal = ":first_place:" if i == 1 else ":second_place:" if i == 2 else ":third_place:" if i == 3 else ""
        leaderboard_text += f"{medal} **{i}.** {name}: **{score}**\n"
    
    embed.add_field(name="Top 10", value=leaderboard_text, inline=False)
    
    await interaction.response.send_message(embed=embed)
    logging.info(f"Level leaderboard displayed: {matched_level[1]} ({difficulty})")

@leaderboard.autocomplete('level')
async def level_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    if not is_allowed_channel(interaction):
        return []
    levels = get_levels()
    return [
        app_commands.Choice(name=level[1], value=level[1])
        for level in levels if current.lower() in level[1].lower()
    ][:25]  # Discord has a limit of 25 choices

# Command decorator that creates a slash command named "my_scores"
@tree.command(name="my_scores", description="View your scores for all levels")
# Adds description for the visibility parameter in Discord's UI
@app_commands.describe(visibility="Choose whether to display scores publicly or privately")
# Main command function that takes the interaction object and an optional visibility parameter
async def my_scores(interaction: discord.Interaction, visibility: Literal['Public', 'Private'] = 'Private'):
    # Check if command is used in an allowed channel
    if not is_allowed_channel(interaction):
        await interaction.response.send_message("This command can only be used in designated channels.", ephemeral=True)
        return

    # Get user information from the interaction
    user_id = str(interaction.user.id)
    user_name = interaction.user.name

    # Fetch all scores for this user from the database
    user_scores = get_user_scores(user_id)

    # If user has no scores, send a message and exit
    if not user_scores:
        await interaction.response.send_message("You haven't recorded any scores yet.", ephemeral=(visibility == 'Private'))
        return

    # Initialize list to hold multiple embeds (Discord has a 25 field limit per embed)
    embeds = []
    # Create first embed with user's name
    current_embed = discord.Embed(title=f"Scores for {user_name}", color=0x00ff00)
    field_count = 0

    # Iterate through each score record
    # get_user_scores() returns tuples of (level_id, level_name, difficulty, score)
    for level_id, level_name, difficulty, score in user_scores:
        # If current embed is full (25 fields), create a new one
        if field_count >= 25:
            embeds.append(current_embed)
            current_embed = discord.Embed(title=f"Scores for {user_name} (Continued)", color=0x00ff00)
            field_count = 0

        # Add score as a field to the current embed
        # name= is the header for each field
        # value= is the content below the header
        # score:, adds thousands separators (e.g., 1,000,000)
        current_embed.add_field(
            name=f"{level_name} ({difficulty})", 
            value=f"Score: {score:,}",
            inline=False
        )
        field_count += 1

    # Add the last embed if it has any fields
    if field_count > 0:
        embeds.append(current_embed)

    # Send the first embed
    # ephemeral=True means only the command user can see it
    await interaction.response.send_message(embed=embeds[0], ephemeral=(visibility == 'Private'))
    
    # Send any additional embeds as follow-up messages
    for embed in embeds[1:]:
        await interaction.followup.send(embed=embed, ephemeral=(visibility == 'Private'))

    # Log that the scores were displayed
    logging.info(f"User scores displayed for {user_name}")

@tree.command(name="check_user_scores", description="Check a specific user's scores for each level (Admin only)")
@app_commands.describe(user_name="Select a user to view their scores")
async def check_user_scores(interaction: discord.Interaction, user_name: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    # Fetch all levels
    levels = get_levels()
    user_scores = get_user_scores_by_name(user_name)

    if not user_scores:
        await interaction.response.send_message(f"No scores found for user {user_name}.", ephemeral=True)
        return

    # Create a dictionary of scores for easy lookup
    scores_dict = {(level_id, difficulty): score for level_id, difficulty, score in user_scores}

    # Prepare the response embeds
    embeds = []
    current_embed = discord.Embed(title=f"Scores for {user_name}", color=0x00ff00)
    field_count = 0

    for level_id, level_name in levels:
        if field_count >= 25:
            embeds.append(current_embed)
            current_embed = discord.Embed(title=f"Scores for {user_name} (Continued)", color=0x00ff00)
            field_count = 0

        scores = [
            f"Easy: {scores_dict.get((level_id, 'Easy'), 'No score')}",
            f"Normal: {scores_dict.get((level_id, 'Normal'), 'No score')}",
            f"Hard: {scores_dict.get((level_id, 'Hard'), 'No score')}",
            f"Expert: {scores_dict.get((level_id, 'Expert'), 'No score')}",
            f"Expert+: {scores_dict.get((level_id, 'Expert+'), 'No score')}"
        ]
        current_embed.add_field(name=level_name, value="\n".join(scores), inline=False)
        field_count += 1

    if field_count > 0:
        embeds.append(current_embed)

    await interaction.response.send_message(embed=embeds[0], ephemeral=True)
    for embed in embeds[1:]:
        await interaction.followup.send(embed=embed, ephemeral=True)

    logging.info(f"Admin {interaction.user.name} checked scores for {user_name}")

@check_user_scores.autocomplete('user_name')
async def user_name_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    try:
        conn = sqlite3.connect('beat_saber_scores.db')
        cursor = conn.cursor()

        # Fetch distinct user names from the scores table
        cursor.execute('SELECT DISTINCT user_name FROM scores')
        users = [row[0] for row in cursor.fetchall()]

    except sqlite3.Error as e:
        logging.error(f"Error fetching user names for autocomplete: {e}")
        return []

    finally:
        conn.close()

    # Return up to 25 matching user names (Discord limits to 25)
    return [
        app_commands.Choice(name=user, value=user)
        for user in users if current.lower() in user.lower()
    ][:25]

# Slash command to force a backup
@tree.command(name="backup_now", description="Force a database backup (Admin only)")
async def backup_now(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    result = perform_backup()
    await interaction.response.send_message(result, ephemeral=True)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    logging.info(f'Bot logged in as {client.user}')
    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} command(s)")
        logging.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
        logging.error(f"Failed to sync commands: {e}")

# Function to perform regular database backups
async def backup_database():
    while True:
        try:
            # Perform backup every 24 hours
            await asyncio.sleep(24 * 60 * 60)  # 24 hours in seconds
            
            # Create a backup copy of the database
            backup_filename = os.path.join(BACKUP_FOLDER, f"beat_saber_scores_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            shutil.copy2('beat_saber_scores.db', backup_filename)
            logging.info(f"Database backed up to {backup_filename}")
        except Exception as e:
            logging.error(f"Error during database backup: {e}")

# Update the setup_hook function to include the migration
async def setup_hook():
    # Initialize database
    init_db()
    # Start the backup task
    client.loop.create_task(backup_database())

client.setup_hook = setup_hook

# Insert your bot token here
client.run(os.getenv('BOT_TOKEN'))
