from discord import Embed, app_commands
from typing import List, Tuple
from constants import EmbedLimits, Difficulty

def create_score_embeds(user_name: str, scores: List[Tuple], continued: bool = False) -> List[Embed]:
    """Create Discord embeds for displaying scores"""
    embeds = []
    current_embed = Embed(
        title=f"Scores for {user_name}" + (" (Continued)" if continued else ""), 
        color=EmbedLimits.COLOR
    )
    field_count = 0

    for level_id, level_name, difficulty, score in scores:
        if field_count >= EmbedLimits.FIELDS_PER_EMBED:
            embeds.append(current_embed)
            current_embed = Embed(
                title=f"Scores for {user_name} (Continued)", 
                color=EmbedLimits.COLOR
            )
            field_count = 0

        current_embed.add_field(
            name=f"{level_name} ({difficulty})",
            value=f"Score: {score:,}",
            inline=False
        )
        field_count += 1

    if field_count > 0:
        embeds.append(current_embed)

    return embeds

def create_leaderboard_embed(level_name: str, difficulty: str, scores: List[Tuple]) -> Embed:
    """Create Discord embed for leaderboard display"""
    embed = Embed(
        title=f"{level_name} Leaderboard", 
        description=f"Difficulty: {difficulty}", 
        color=EmbedLimits.COLOR
    )
    
    if not scores:
        embed.add_field(
            name="No scores yet", 
            value="Be the first to set a score!", 
            inline=False
        )
        return embed

    leaderboard_text = ""
    for i, (name, score) in enumerate(scores[:10], 1):
        medal = "👑" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else ""
        leaderboard_text += f"{medal} **{i}.** {name}: **{score:,}**\n"
    
    embed.add_field(name="Top 10", value=leaderboard_text, inline=False)
    return embed

def create_level_choices(levels: List[Tuple], current: str) -> List[app_commands.Choice[str]]:
    """Create autocomplete choices for level selection"""
    return [
        app_commands.Choice(name=level[1], value=level[1])
        for level in levels 
        if current.lower() in level[1].lower()
    ][:25]  # Discord limit

def create_difficulty_choices(current: str) -> List[app_commands.Choice[str]]:
    """Create autocomplete choices for difficulty selection"""
    return [
        app_commands.Choice(name=diff, value=diff)
        for diff in Difficulty.list()
        if current.lower() in diff.lower()
    ]
