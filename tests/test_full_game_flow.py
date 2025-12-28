import unittest
import os
from poker_brain.model import GameContext, Hero, Villain
from poker_brain.strategy import StrategyEngine
from poker_brain.modules.player_db import PlayerDB

class TestFullGameFlow(unittest.TestCase):

    def setUp(self):
        self.engine = StrategyEngine()

    def test_ak_multi_street_aggression(self):
        """
        Test a full hand flow: AKs vs Villain.
        """
        hero_stack = 1000

        # --- STREET 1: PREFLOP ---
        hero = Hero(position="BTN", cards=["Ah", "Kh"], stack=hero_stack, current_investment=0)
        villain = Villain(position="UTG", status="ACTIVE", stack=1000, current_investment=30)

        ctx_pre = GameContext(
            game_id="game_1", street="PREFLOP", pot_size=45, current_bet=30,
            board=[], hero=hero, villains=[villain]
        )

        dec_pre = self.engine.make_decision(ctx_pre)
        # print(f"[Preflop] AKs: {dec_pre.action} ({dec_pre.reasoning})")
        self.assertIn(dec_pre.action, ["RAISE", "ALLIN"])

        # --- STREET 2: FLOP ---
        hero.current_investment = 0
        ctx_flop = GameContext(
            game_id="game_1", street="FLOP", pot_size=200, current_bet=0,
            board=["Ks", "7d", "2c"], hero=hero, villains=[villain]
        )

        dec_flop = self.engine.make_decision(ctx_flop)
        # print(f"[Flop] K-7-2: {dec_flop.action} ({dec_flop.reasoning})")
        self.assertIn(dec_flop.action, ["RAISE", "BET", "ALLIN"])

        # --- STREET 3: TURN ---
        ctx_turn = GameContext(
            game_id="game_1", street="TURN", pot_size=300, current_bet=0,
            board=["Ks", "7d", "2c", "3h"], hero=hero, villains=[villain]
        )

        dec_turn = self.engine.make_decision(ctx_turn)
        # print(f"[Turn] K-7-2-3: {dec_turn.action} ({dec_turn.reasoning})")
        # Should bet
        self.assertIn(dec_turn.action, ["RAISE", "BET", "ALLIN", "CHECK"])

        # --- STREET 4: RIVER ---
        ctx_river = GameContext(
            game_id="game_1", street="RIVER", pot_size=400, current_bet=200,
            board=["Ks", "7d", "2c", "3h", "Ad"], hero=hero, villains=[villain]
        )

        dec_river = self.engine.make_decision(ctx_river)
        # print(f"[River] Two Pair vs Bet: {dec_river.action} ({dec_river.reasoning})")
        self.assertNotEqual(dec_river.action, "FOLD")

if __name__ == '__main__':
    unittest.main()
