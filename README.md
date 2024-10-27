# Beat Saber Discord Bot

A Discord bot for tracking Beat Saber scores and maintaining leaderboards.

## Disclaimer

This is a fan-made Discord bot. This project is not affiliated with, endorsed by, or connected to Beat Saber or Meta. All product names, logos, and brands are property of their respective owners.

## Features

- Record scores for Beat Saber levels
- View personal scores
- View leaderboards by level and difficulty
- Automatic database backups

## Setup

1. Clone the repository
2. Install requirements: `pip install -r requirements.txt`
3. Create a `.env` file with your Discord bot token:   ```
   BOT_TOKEN=your_token_here   ```
4. Initialize the levels database:   ```
   python init_beat_saber_levels.py   ```
5. Run the bot:   ```
   python bot.py   ```

## Commands

- `/score` - Record a score for a level
- `/leaderboard` - View the leaderboard for a level
- `/my_scores` - View your personal scores
- `/add_level` - (Admin only) Add a new level
- `/backup_now` - (Admin only) Force a database backup
