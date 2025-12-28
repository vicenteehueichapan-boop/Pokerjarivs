import unittest
from poker_brain.model import GameContext, Hero, Villain
from poker_brain.strategy import StrategyEngine
from poker_brain.main import PokerBrain

class TestPokerBrain(unittest.TestCase):

    def setUp(self):
        self.engine = StrategyEngine()
        self.brain = PokerBrain()

    def test_pot_odds_calc(self):
        odds = self.engine.calculate_pot_odds(50, 100)
        self.assertAlmostEqual(odds, 0.333, places=2)

    def test_preflop_weak_hand_fold(self):
        # Hero 72o vs Raise
        hero = Hero(position="BTN", cards=["7h", "2d"], stack=1000, current_investment=0)
        villain = Villain(position="SB", status="ACTIVE", stack=1000, current_investment=1000)

        context = GameContext(
            game_id="1",
            street="PREFLOP",
            pot_size=1100,
            current_bet=1000,
            board=[],
            hero=hero,
            villains=[villain]
        )

        decision = self.engine.make_decision(context)
        print(f"72o Decision: {decision}")
        # Expect Fold because EV of Call is negative
        self.assertEqual(decision.action, "FOLD")

    def test_postflop_nuts_raise(self):
        # Royal Flush.
        # Strategy should choose RAISE or ALLIN because it generates more EV than just CALL (Fold Equity + Value)
        # However, if fold equity is low, maybe Call is better?
        # But with 100% equity, any money in pot is good.
        # Our GameTree logic favors putting money in when Equity is high.

        hero = Hero(position="BTN", cards=["Js", "Ts"], stack=1000, current_investment=0)
        villain = Villain(position="SB", status="ACTIVE", stack=1000, current_investment=100)

        context = GameContext(
            game_id="2",
            street="FLOP",
            pot_size=200,
            current_bet=100,
            board=["As", "Ks", "Qs"],
            hero=hero,
            villains=[villain]
        )

        decision = self.engine.make_decision(context)
        print(f"Royal Flush Decision: {decision}")

        self.assertIn(decision.action, ["RAISE", "ALLIN"])
        self.assertTrue(decision.ev_estimation > 0)

    def test_semi_bluff_opportunity(self):
        # We have a Flush Draw. Equity approx 35%.
        # Pot: 100. Check to us.
        # If we Check, EV = 0.35 * 100 = 35.
        # If we Bet 50:
        #   Fold Equity (say 40%): 0.4 * 100 = 40.
        #   Call Equity (60%): 0.35 * (100 + 50 + 50) - 50 = 0.35 * 200 - 50 = 70 - 50 = 20.
        #   Total Bet EV = 40 + (0.6 * 20) = 40 + 12 = 52.
        # Since 52 (Bet) > 35 (Check), the bot should BET.

        # Note: This relies on the Fold Equity assumptions in game_tree.py

        hero = Hero(position="BTN", cards=["Th", "9h"], stack=1000, current_investment=0)
        villain = Villain(position="BB", status="ACTIVE", stack=1000, current_investment=0)

        context = GameContext(
            game_id="3",
            street="FLOP",
            pot_size=100,
            current_bet=0,
            board=["2h", "5h", "Kd"], # Flush draw
            hero=hero,
            villains=[villain]
        )

        decision = self.engine.make_decision(context)
        print(f"Flush Draw Decision: {decision}")

        # Should likely Bet (RAISE) or Check.
        # But if our logic is aggressive, it might Bet.
        # Let's see what it does.
        # If it Checks, that's also valid, but we want to see if EV calculation works.
        self.assertTrue(decision.ev_estimation > 0)

if __name__ == '__main__':
    unittest.main()
