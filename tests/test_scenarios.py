import unittest
from poker_brain.model import GameContext, Hero, Villain
from poker_brain.strategy import StrategyEngine
from poker_brain.main import PokerBrain

class TestPokerBrain(unittest.TestCase):

    def setUp(self):
        self.engine = StrategyEngine()
        self.brain = PokerBrain()

    def test_pot_odds_calc(self):
        # Pot is 100, to call is 50. Total pot becomes 150. Odds = 50/150 = 0.33
        odds = self.engine.calculate_pot_odds(50, 100)
        self.assertAlmostEqual(odds, 0.333, places=2)

    def test_preflop_weak_hand_fold(self):
        # Hero has 72o (worst hand) facing a huge All-in
        # Pot 100, Bet 1000. Odds are terrible. Equity is low. Should Fold.

        hero = Hero(position="BTN", cards=["7h", "2d"], stack=1000, current_investment=0)
        villain = Villain(position="SB", status="ACTIVE", stack=1000, current_investment=1000)

        context = GameContext(
            game_id="1",
            street="PREFLOP",
            pot_size=1000 + 100, # Blind + Bet
            current_bet=1000,
            board=[],
            hero=hero,
            villains=[villain]
        )

        decision = self.engine.make_decision(context)
        print(f"72o Decision: {decision}")
        self.assertEqual(decision.action, "FOLD")

    def test_postflop_nuts_call(self):
        # Board: As Ks Qs
        # Hero: Js Ts (Royal Flush)
        # We have 100% equity. We should Call or Raise any bet.

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

        # Estimate equity might take a second due to simulation
        decision = self.engine.make_decision(context)
        print(f"Royal Flush Decision: {decision}")

        # Should call or raise
        self.assertIn(decision.action, ["CALL", "RAISE"])
        # EV should be very positive
        self.assertTrue(decision.ev_estimation > 0)

    def test_integration_json(self):
        # Test the full input/output dict flow
        input_data = {
          "game_id": "test_1",
          "street": "RIVER",
          "pot_size": 100.0,
          "current_bet": 0.0,
          "board": ["Ah", "Kd", "2s", "5c", "9h"],
          "hero": {
            "position": "BTN",
            "cards": ["Th", "Tc"],
            "stack": 1000.0,
            "current_investment": 0.0
          },
          "villains": [
            {
              "position": "SB",
              "status": "ACTIVE",
              "stack": 950.0,
              "current_investment": 0.0,
              "stats": {}
            }
          ]
        }

        result = self.brain.decide(input_data)
        self.assertIn("action", result)
        self.assertIn("ev_estimation", result)

if __name__ == '__main__':
    unittest.main()
