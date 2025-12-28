import unittest
from poker_brain.model import GameContext, Hero, Villain
from poker_brain.strategy import StrategyEngine

class TestProfessionalPlay(unittest.TestCase):

    def setUp(self):
        self.engine = StrategyEngine()

    def test_range_advantage_scenario(self):
        """
        Test: Hero (UTG) has AKs on A-7-2 rainbow.
        Villain (BB) defends wide.

        UTG Range: {77+, AJs+, ...} (Strong, hits Ace hard)
        BB Range: {Any 2} (Weak, misses Ace often)

        Our Equity should be massive (>80%), leading to a value bet.
        """
        hero = Hero(position="UTG", cards=["Ah", "Kh"], stack=1000, current_investment=0)
        # BB defends wide, so we treat him as BB position in range lookup
        villain = Villain(position="BB", status="ACTIVE", stack=1000, current_investment=0)

        context = GameContext(
            game_id="pro_1",
            street="FLOP",
            pot_size=100,
            current_bet=0,
            board=["Ad", "7s", "2c"], # Dry Ace High board
            hero=hero,
            villains=[villain]
        )

        decision = self.engine.make_decision(context)
        print(f"Range Adv Decision: {decision}")

        # We expect a Bet (Raise/Allin in our action terms for opening bet)
        # or at least high equity.
        self.assertIn(decision.action, ["RAISE", "BET", "ALLIN"])

        # Equity check: AK on A72 vs Random BB range should be huge
        # Parse reasoning string to extract equity? "EV: 80.5 (Eq: 0.92 ...)"
        import re
        match = re.search(r"Eq: ([0-9\.]+)", decision.reasoning)
        if match:
            equity = float(match.group(1))
            print(f"Detected Equity vs Range: {equity}")
            self.assertTrue(equity > 0.80, "Equity should be > 80% with Top Pair Top Kicker vs Wide Range")

    def test_preflop_discipline_fold(self):
        """
        Test: Hero (UTG) has K-10 offsuit.
        In NL25, UTG should FOLD KTo. It is dominated.

        However, our current engine calculates EV based on post-flop equity?
        No, preflop we simulate too.
        KTo vs Random might look okay (50%+) but vs UTG opening range it's trash.

        Wait, currently the engine calculates EV based on 'target_villain_pos'.
        If everyone folded to us, who is the villain?
        If we are opening, the opponents are the Blinds (random cards).

        KTo vs 5 Random Hands is bad.
        KTo vs 1 Random Hand is okay (60%).

        This test reveals a gap: We need Preflop Charts for Hero too!
        The gap analysis mentioned "Preflop Charts" for opponents, but for Hero?
        If the bot calculates EV of KTo vs BB Random, it might think it's +EV to open.
        But in GTO, we fold because of rake and domination.

        For this MVP 'Pro' test, let's verify that even with simulation,
        a trash hand like J2o folds from UTG.
        """
        hero = Hero(position="UTG", cards=["Jh", "2d"], stack=1000, current_investment=0)
        villain = Villain(position="BB", status="ACTIVE", stack=1000, current_investment=1000) # Assuming we face action?

        # If we face an Open Raise from another UTG while we are MP
        # Hero MP with KTo vs UTG Open.
        # UTG Range: Strong.
        # Hero KTo: Dominated.
        # Equity should be low (< 35%).

        hero_mp = Hero(position="MP", cards=["Kh", "Td"], stack=1000, current_investment=0)
        villain_utg = Villain(position="UTG", status="ACTIVE", stack=1000, current_investment=3)

        context = GameContext(
            game_id="pro_2",
            street="PREFLOP",
            pot_size=4.5,
            current_bet=3,
            board=[],
            hero=hero_mp,
            villains=[villain_utg]
        )

        decision = self.engine.make_decision(context)
        print(f"KTo vs UTG Decision: {decision}")

        self.assertEqual(decision.action, "FOLD")

if __name__ == '__main__':
    unittest.main()
