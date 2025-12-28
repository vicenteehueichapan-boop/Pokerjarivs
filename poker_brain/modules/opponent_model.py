from typing import List
from ..model import Villain, GameContext

class OpponentModel:
    """
    Estimates opponent ranges and tendencies.
    In a full bot, this would use a database of stats (HUD).
    For now, it returns a generic 'percentage range' based on position and action.
    """

    def __init__(self):
        pass

    def estimate_range(self, villain: Villain, context: GameContext) -> float:
        """
        Returns the top % of hands the villain is likely holding.
        e.g. 0.15 means "Top 15%".
        """
        # Heuristics
        if villain.stats.get('vpip'):
            # If we have VPIP, use it as a baseline
            return float(villain.stats['vpip'])

        # Position based heuristic
        # UTG is tight, BTN is loose.
        pos = villain.position
        if pos in ["UTG", "UTG+1"]:
            return 0.10 # Tight
        elif pos in ["MP", "MP+1"]:
            return 0.15
        elif pos in ["CO", "BTN"]:
            return 0.30
        elif pos == "SB":
            return 0.40
        elif pos == "BB":
            return 0.50 # Defends wide

        return 0.25 # Default average
