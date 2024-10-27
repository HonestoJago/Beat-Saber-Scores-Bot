import discord
from discord import app_commands
from discord.ext import commands
from typing import Literal
import logging
from database import Database
from constants import Difficulty, ScoreLimits
from utils.formatters import (
    create_score_embeds, 
    create_leaderboard_embed,
    create_level_choices,
    create_difficulty_choices
)
from config import Config

class ScoresCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Use the bot's database instance instead of creating a new one
        self.db = bot.db

    @app_commands.command(name="score", description="Record a score for a Beat Saber level")
    @app_commands.describe(
        level="Name of the level",
        difficulty="Difficulty of the level",
        score="Your score for the level (0 to 3,000,000)"
    )
    async def score(self, interaction: discord.Interaction, 
                   level: str,
                   difficulty: str,
                   score: int):
        if not Config.is_allowed_channel(interaction.channel_id):
            await interaction.response.send_message(
                "This command can only be used in designated channels.", 
                ephemeral=True
            )
            return

        # Validate difficulty
        if difficulty not in Difficulty.list():
            await interaction.response.send_message(
                f"Invalid difficulty. Please choose from: {', '.join(Difficulty.list())}", 
                ephemeral=True
            )
            return

        # Validate score range
        if not ScoreLimits.MIN <= score <= ScoreLimits.MAX:
            await interaction.response.send_message(
                f"Invalid score. Please enter a score between {ScoreLimits.MIN:,} and {ScoreLimits.MAX:,}.", 
                ephemeral=True
            )
            return

        # Get valid levels and check match
        levels = self.db.get_levels()
        matched_level = next((l for l in levels if l[1] == level), None)
        if not matched_level:
            await interaction.response.send_message(
                "Invalid level name. Please select a level from the autocomplete menu.", 
                ephemeral=True
            )
            return

        # Insert score
        self.db.insert_score(
            str(interaction.user.id),
            interaction.user.name,
            matched_level[0],
            difficulty,
            score
        )
        
        response = f"Score of {score:,} recorded for {matched_level[1]} ({difficulty})."
        await interaction.response.send_message(response, ephemeral=True)
        
        log_message = f"Score submitted: {interaction.user.name} - {matched_level[1]} ({difficulty}): {score}"
        logging.info(log_message)

    @score.autocomplete('level')
    async def level_autocomplete(self, interaction: discord.Interaction, current: str):
        if not Config.is_allowed_channel(interaction.channel_id):
            return []
        return create_level_choices(self.db.get_levels(), current)

    @score.autocomplete('difficulty')
    async def difficulty_autocomplete(self, interaction: discord.Interaction, current: str):
        return create_difficulty_choices(current)

    @app_commands.command(name="leaderboard", description="Show leaderboard for a specific level")
    @app_commands.describe(
        level="Name of the level",
        difficulty="Difficulty of the level"
    )
    async def leaderboard(self, interaction: discord.Interaction,
                         level: str,
                         difficulty: Literal['Easy', 'Normal', 'Hard', 'Expert', 'Expert+']):
        if not Config.is_allowed_channel(interaction.channel_id):
            await interaction.response.send_message(
                "This command can only be used in designated channels.", 
                ephemeral=True
            )
            return

        try:
            levels = self.db.get_levels()
            matched_level = next((l for l in levels if l[1] == level), None)
            if not matched_level:
                await interaction.response.send_message(f"Level '{level}' not found.")
                return

            # Debug logging
            logging.info(f"Fetching leaderboard for level: {level} (ID: {matched_level[0]}) - {difficulty}")
            
            scores = self.db.get_level_leaderboard(matched_level[0], difficulty)
            logging.info(f"Found {len(scores)} scores for {level} ({difficulty})")
            
            embed = create_leaderboard_embed(matched_level[1], difficulty, scores)
            await interaction.response.send_message(embed=embed)
            logging.info(f"Level leaderboard displayed: {matched_level[1]} ({difficulty})")
            
        except Exception as e:
            logging.error(f"Error displaying leaderboard: {e}")
            await interaction.response.send_message(
                "An error occurred while retrieving the leaderboard.", 
                ephemeral=True
            )

    @leaderboard.autocomplete('level')
    async def leaderboard_level_autocomplete(self, interaction: discord.Interaction, current: str):
        if not Config.is_allowed_channel(interaction.channel_id):
            return []
        return create_level_choices(self.db.get_levels(), current)

    @app_commands.command(name="my_scores", description="View your scores for all levels")
    @app_commands.describe(visibility="Choose whether to display scores publicly or privately")
    async def my_scores(self, interaction: discord.Interaction, 
                       visibility: Literal['Public', 'Private'] = 'Private'):
        if not Config.is_allowed_channel(interaction.channel_id):
            await interaction.response.send_message(
                "This command can only be used in designated channels.", 
                ephemeral=True
            )
            return

        try:
            # Use the shared database connection
            user_scores = self.db.get_user_scores(str(interaction.user.id))
            
            # Debug logging
            logging.info(f"Retrieved scores for {interaction.user.name}: {len(user_scores)} scores found")
            
            if not user_scores:
                await interaction.response.send_message(
                    "You haven't recorded any scores yet.", 
                    ephemeral=(visibility == 'Private')
                )
                return

            embeds = create_score_embeds(interaction.user.name, user_scores)
            
            await interaction.response.send_message(
                embed=embeds[0], 
                ephemeral=(visibility == 'Private')
            )
            
            for embed in embeds[1:]:
                await interaction.followup.send(
                    embed=embed, 
                    ephemeral=(visibility == 'Private')
                )

            logging.info(f"User scores displayed for {interaction.user.name}")
        except Exception as e:
            logging.error(f"Error displaying scores for {interaction.user.name}: {e}")
            await interaction.response.send_message(
                "An error occurred while retrieving your scores.", 
                ephemeral=True
            )

    @app_commands.command(name="check_user_scores", description="Check a specific user's scores (Admin only)")
    @app_commands.describe(user_name="Select a user to view their scores")
    async def check_user_scores(self, interaction: discord.Interaction, user_name: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You don't have permission to use this command.", 
                ephemeral=True
            )
            return

        # Get all scores for the user
        user_scores = self.db.get_user_scores_by_name(user_name)
        if not user_scores:
            await interaction.response.send_message(
                f"No scores found for user {user_name}.", 
                ephemeral=True
            )
            return

        # Create a lookup dictionary for quick score access
        scores_dict = {(level_id, difficulty): score 
                      for level_id, difficulty, score in user_scores}

        # Get all levels for complete display
        levels = self.db.get_levels()
        
        # Create embeds with scores organized by level
        embeds = []
        current_embed = discord.Embed(title=f"Scores for {user_name}", color=0x00ff00)
        field_count = 0

        for level_id, level_name in levels:
            if field_count >= 25:  # Discord's field limit
                embeds.append(current_embed)
                current_embed = discord.Embed(
                    title=f"Scores for {user_name} (Continued)", 
                    color=0x00ff00
                )
                field_count = 0

            # Create formatted score display for each difficulty
            scores = []
            for diff in Difficulty.list():
                score = scores_dict.get((level_id, diff), 'No score')
                if score != 'No score':
                    score = f"{score:,}"
                scores.append(f"{diff}: {score}")

            current_embed.add_field(
                name=level_name,
                value="\n".join(scores),
                inline=False
            )
            field_count += 1

        if field_count > 0:
            embeds.append(current_embed)

        # Send embeds
        await interaction.response.send_message(embed=embeds[0], ephemeral=True)
        for embed in embeds[1:]:
            await interaction.followup.send(embed=embed, ephemeral=True)

        logging.info(f"Admin {interaction.user.name} checked scores for {user_name}")

    @check_user_scores.autocomplete('user_name')
    async def user_name_autocomplete(self, interaction: discord.Interaction, current: str):
        if not interaction.user.guild_permissions.administrator:
            return []
        return [
            app_commands.Choice(name=name, value=name)
            for name in self.db.get_unique_users()
            if current.lower() in name.lower()
        ][:25]  # Discord limit

    @app_commands.command(name="debug_db", description="Debug database connection (Admin only)")
    async def debug_db(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return
        
        try:
            user_id = str(interaction.user.id)
            levels = self.db.get_levels()
            scores = self.db.get_user_scores(user_id)
            
            debug_info = (
                f"Database connection test:\n"
                f"- Levels found: {len(levels)}\n"
                f"- Your scores found: {len(scores)}\n"
                f"- Your user ID: {user_id}"
            )
            
            await interaction.response.send_message(debug_info, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Debug error: {str(e)}", ephemeral=True)
