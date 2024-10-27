from enum import Enum

class Difficulty(Enum):
    EASY = "Easy"
    NORMAL = "Normal"
    HARD = "Hard"
    EXPERT = "Expert"
    EXPERT_PLUS = "Expert+"

    @classmethod
    def list(cls) -> list[str]:
        return [diff.value for diff in cls]

class ScoreLimits:
    MIN = 0
    MAX = 3_000_000

class EmbedLimits:
    FIELDS_PER_EMBED = 25
    COLOR = 0x00ff00  # Green color for embeds
