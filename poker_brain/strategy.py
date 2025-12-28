import random
from treys import Card, Deck
from .model import GameContext, Decision
from .modules.evaluator import HandEvaluator
from .modules.opponent_model import OpponentModel
from .modules.game_tree import GameTree

class StrategyEngine:
    def __init__(self):
        self.evaluator = HandEvaluator()
        self.opponent_model = OpponentModel()
        self.game_tree = GameTree()

    def calculate_pot_odds(self, to_call: float, pot_total: float) -> float:
        if to_call <= 0:
            return 0.0
        return to_call / (pot_total + to_call)

    def estimate_equity(self, hero_hand: list[str], board: list[str], villain_position: str, simulations=1000) -> float:
        """
        Estimates equity by simulating Hero vs Villain RANGE.
        """
        # 1. Setup Hero and Board
        hero_cards_int = [Card.new(c) for c in hero_hand]
        board_cards_int = [Card.new(c) for c in board]
        known_cards = set(hero_cards_int + board_cards_int)

        # 2. Get Villain Range (The Professional Upgrade)
        range_strs = self.opponent_model.get_range_list(villain_position)
        villain_combos = self.opponent_model.parse_range(range_strs)

        if not villain_combos:
            # Fallback to random if range is empty/unknown
            # This happens if our parser misses something or position is weird
            villain_combos = None

        wins = 0
        ties = 0

        for _ in range(simulations):
            deck = Deck()
            full_deck = deck.GetFullDeck()

            # 3. Select Villain Hand
            villain_hand = []

            if villain_combos:
                # Filter combos that are impossible (card overlap with Hero/Board)
                valid_combos = [
                    c for c in villain_combos
                    if c[0] not in known_cards and c[1] not in known_cards
                ]

                if valid_combos:
                    villain_hand = random.choice(valid_combos)
                else:
                    # If all combos blocked (rare), take random
                    pass

            if not villain_hand:
                # Random hand fallback
                remaining_deck = [c for c in full_deck if c not in known_cards]
                random.shuffle(remaining_deck)
                villain_hand = [remaining_deck.pop(), remaining_deck.pop()]

            # 4. Runout
            # Remove Villain cards from deck used for runout
            # Note: valid_combos logic ensures no overlap with hero/board.
            # But we need to ensure runout doesn't pick villain cards.

            used_cards = set(known_cards)
            used_cards.add(villain_hand[0])
            used_cards.add(villain_hand[1])

            runout_deck = [c for c in full_deck if c not in used_cards]
            random.shuffle(runout_deck)

            cards_needed = 5 - len(board_cards_int)
            runout = []
            if cards_needed > 0:
                runout = runout_deck[:cards_needed]

            final_board = board_cards_int + runout

            hero_score = self.evaluator.evaluator.evaluate(final_board, hero_cards_int)
            villain_score = self.evaluator.evaluator.evaluate(final_board, villain_hand)

            if hero_score < villain_score:
                wins += 1
            elif hero_score == villain_score:
                ties += 1

        equity = (wins + (ties * 0.5)) / simulations
        return equity

    def make_decision(self, context: GameContext) -> Decision:
        """
        Core decision logic using GameTree search.
        """
        # 1. Identify Villain Position for Range Lookup
        # We need to know WHICH villain we are fighting.
        # MVP assumption: First active villain or the one who bet.
        target_villain_pos = "BTN" # Default
        if context.villains:
            target_villain_pos = context.villains[0].position

        # 2. Analyze Context
        if context.hero.cards:
             equity = self.estimate_equity(
                 context.hero.cards,
                 context.board,
                 target_villain_pos,
                 simulations=500
             )
        else:
             equity = 0.0

        # 3. Generate Options
        candidates = self.game_tree.generate_candidate_actions(context)

        # 4. Evaluate Options
        best_decision = None
        best_ev = -float('inf')

        for decision in candidates:
            # Pass equity to tree evaluator
            ev = self.game_tree.evaluate_node(decision, context, equity)
            decision.ev_estimation = ev
            decision.reasoning = f"EV: {ev:.2f} (Eq: {equity:.2f} vs {target_villain_pos} Range)"

            if ev > best_ev:
                best_ev = ev
                best_decision = decision

        if not best_decision:
            return Decision(action="FOLD", amount=0, reasoning="No valid moves found.")

        return best_decision
