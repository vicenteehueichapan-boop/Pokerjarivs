import unittest
import os
from poker_brain.model import GameContext, Hero, Villain
from poker_brain.strategy import StrategyEngine
from poker_brain.modules.player_db import PlayerDB

class TestPersistence(unittest.TestCase):

    def setUp(self):
        # Use a temporary DB for testing
        self.db_name = "test_memory.db"
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

        self.engine = StrategyEngine()
        # Hack to inject the test DB into the engine's model
        self.engine.opponent_model.db = PlayerDB(self.db_name)

    def tearDown(self):
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

    def test_memory_adaptation(self):
        """
        Test:
        1. Meet 'VillainX' (Unknown). He is in UTG. We assume he is Tight.
           Equity should be low for our mediocre hand.

        2. TEACH the bot that 'VillainX' is a maniac (High VPIP).
           Update DB manually.

        3. Meet 'VillainX' again (Same UTG spot).
           Equity should now be HIGH because we know he plays trash.
        """
        player_name = "ManiacMike"

        hero = Hero(position="BTN", cards=["Ah", "9d"], stack=1000, current_investment=0)
        board = ["Ad", "8s", "2c"] # Top pair weak kicker

        # UTG Villain
        villain = Villain(position="UTG", status="ACTIVE", stack=1000, current_investment=0)
        # Inject name for DB lookup (Simulating real app usage)
        villain.name = player_name

        # --- Round 1: Unknown ---
        equity_1 = self.engine.estimate_equity(hero.cards, board, villain, simulations=1000)
        print(f"Equity vs Unknown UTG: {equity_1:.3f}")

        # --- Teach DB ---
        # Simulate seeing 20 hands where he played 15 (75% VPIP)
        for _ in range(20):
            self.engine.opponent_model.db.update_player_stats(player_name, is_vpip=True, is_pfr=False)

        # Verify stats are saved
        stats = self.engine.opponent_model.db.get_player_stats(player_name)
        print(f"Stats for {player_name}: Hands={stats.hands}, VPIP={stats.vpip:.2f}")
        self.assertTrue(stats.vpip > 0.5)

        # --- Round 2: Known Maniac ---
        equity_2 = self.engine.estimate_equity(hero.cards, board, villain, simulations=1000)
        print(f"Equity vs Known Maniac UTG: {equity_2:.3f}")

        # Expectation: A9 vs UTG GTO is bad. A9 vs Maniac is great.
        self.assertGreater(equity_2, equity_1 + 0.10, "Should have >10% more equity after learning player is a fish")

if __name__ == '__main__':
    unittest.main()
