# Beat Saber Discord Bot

A Discord bot for tracking Beat Saber scores and maintaining leaderboards. Keep track of your high scores, compete with friends, and see who tops the leaderboards!

## Disclaimer

This is a fan-made Discord bot. This project is not affiliated with, endorsed by, or connected to Beat Saber or Meta. All product names, logos, and brands are property of their respective owners.

## Features

- Track scores across all Beat Saber levels and difficulties
- View personal scores (privately or publicly)
- Compete on level-specific leaderboards
- Auto-complete for level names and difficulties
- Automatic daily database backups
- Admin commands for server management

## Setup

1. Clone the repository
2. Install requirements:   ```
   pip install -r requirements.txt   ```
3. Create a `.env` file using env.example as a template:   ```
   BOT_TOKEN=your_discord_bot_token
   ALLOWED_CHANNEL_IDS=channel_id_1,channel_id_2   ```
4. Run the bot:   ```
   python bot.py   ```

The bot automatically:
- Creates and initializes the database
- Imports all Beat Saber levels
- Sets up daily backups
- Maintains data integrity

## User Commands

- `/score` - Record a score for any level
  - Auto-completes level names and difficulties
  - Validates score ranges
  - Confirms score submission

- `/leaderboard` - View competition rankings
  - Shows top 10 scores for any level/difficulty
  - Displays player names and scores
  - Highlights top 3 positions

- `/my_scores` - Check your personal records
  - View all your scores across levels
  - Choose public or private display
  - Organized by level and difficulty

## Admin Commands

- `/check_user_scores` - View any user's complete score history
- `/backup_now` - Create an immediate database backup

## Level Management

The bot uses `beat_saber_levels.csv` to manage available levels. The included CSV contains all official Beat Saber levels as of October 2024.

To add new levels:
1. Edit `beat_saber_levels.csv` in a text editor (not Excel)
   - Each line should contain exactly one level name
   - Level names can contain any characters (including /, &, etc.)
   - Names must match exactly what appears in Beat Saber
   - No commas or quotation marks needed

## Database Backups

The bot maintains database integrity through:
- Automatic daily backups
- Manual backup option for admins
- Timestamped backup files
- Consistent backup format: `beat_saber_scores_backup_YYYYMMDD_HHMMSS.db`

## Technical Details

- Built with Discord.py
- SQLite database for data storage
- Modular codebase design
- Extensive error handling and logging
- Configurable through environment variables

## Support

If you encounter any issues or have questions:
1. Check the bot's log file for error messages
2. Ensure your `.env` file is configured correctly
3. Verify the bot has proper Discord permissions
4. Make sure you're using the bot in allowed channels
