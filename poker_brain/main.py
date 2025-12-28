from .model import GameContext, Decision
from .strategy import StrategyEngine
import json
from dataclasses import asdict

class PokerBrain:
    def __init__(self):
        self.engine = StrategyEngine()

    def decide(self, context_dict: dict) -> dict:
        """
        Main entry point. Receives dictionary (parsed JSON), returns dictionary (JSON).
        """
        # Parse Input
        # Note: We need to reconstruct nested objects manually or use a library.
        # Since we use dataclasses, we can do a simple mapping.

        # Helper to parse villains
        villains = []
        for v in context_dict.get('villains', []):
            villains.append(v) # Actually we need to cast them to Villain objects if we want strict typing
            # But the StrategyEngine expects GameContext object.

        # We need to properly deserialize.
        # For simplicity in this MVP without Pydantic:
        from .model import Hero, Villain

        hero_data = context_dict['hero']
        hero = Hero(**hero_data)

        villain_objs = [Villain(**v) for v in context_dict['villains']]

        context = GameContext(
            game_id=context_dict['game_id'],
            street=context_dict['street'],
            pot_size=context_dict['pot_size'],
            current_bet=context_dict['current_bet'],
            board=context_dict['board'],
            hero=hero,
            villains=villain_objs
        )

        decision = self.engine.make_decision(context)

        return asdict(decision)
