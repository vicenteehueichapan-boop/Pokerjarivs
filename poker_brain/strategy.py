import random
from treys import Card, Deck
from .model import GameContext, Decision, Villain
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

    def estimate_equity(self, hero_hand: list[str], board: list[str], villain: Villain, simulations=1000) -> float:
        """
        Estimates equity by simulating Hero vs Villain RANGE.
        Uses Phevaluator via self.evaluator for speed.
        """
        hero_cards_int = [Card.new(c) for c in hero_hand]
        board_cards_int = [Card.new(c) for c in board]
        known_cards = set(hero_cards_int + board_cards_int)

        range_strs = self.opponent_model.get_range_list(villain)
        villain_combos = self.opponent_model.parse_range(range_strs)

        if not villain_combos:
            villain_combos = None

        wins = 0
        ties = 0

        for _ in range(simulations):
            deck = Deck()
            full_deck = deck.GetFullDeck()

            # Select Villain Hand
            villain_hand_int = []

            if villain_combos:
                valid_combos = [
                    c for c in villain_combos
                    if c[0] not in known_cards and c[1] not in known_cards
                ]

                if valid_combos:
                    villain_hand_int = random.choice(valid_combos)
                else:
                    pass

            if not villain_hand_int:
                remaining_deck = [c for c in full_deck if c not in known_cards]
                random.shuffle(remaining_deck)
                villain_hand_int = [remaining_deck.pop(), remaining_deck.pop()]

            # Runout
            used_cards = set(known_cards)
            used_cards.add(villain_hand_int[0])
            used_cards.add(villain_hand_int[1])

            runout_deck = [c for c in full_deck if c not in used_cards]
            random.shuffle(runout_deck)

            cards_needed = 5 - len(board_cards_int)
            runout_int = []
            if cards_needed > 0:
                runout_int = runout_deck[:cards_needed]

            # Evaluate
            final_board_int = board_cards_int + runout_int

            board_strs = [Card.int_to_str(c) for c in final_board_int]
            villain_hand_strs = [Card.int_to_str(c) for c in villain_hand_int]

            hero_final_strs = hero_hand + board_strs
            villain_final_strs = villain_hand_strs + board_strs

            hero_score = self.evaluator.evaluate_hand([], hero_final_strs)
            villain_score = self.evaluator.evaluate_hand([], villain_final_strs)

            if hero_score < villain_score:
                wins += 1
            elif hero_score == villain_score:
                ties += 1

        equity = (wins + (ties * 0.5)) / simulations
        return equity

    def make_decision(self, context: GameContext) -> Decision:
        target_villain = context.villains[0] if context.villains else Villain("BTN", "ACTIVE", 100, 0)

        if context.hero.cards:
             equity = self.estimate_equity(
                 context.hero.cards,
                 context.board,
                 target_villain,
                 simulations=500
             )
        else:
             equity = 0.0

        candidates = self.game_tree.generate_candidate_actions(context)

        best_decision = None
        best_ev = -float('inf')

        for decision in candidates:
            ev = self.game_tree.evaluate_node(decision, context, equity)
            decision.ev_estimation = ev
            decision.reasoning = f"EV: {ev:.2f} (Eq: {equity:.2f} vs {target_villain.position})"

            if ev > best_ev:
                best_ev = ev
                best_decision = decision

        if not best_decision:
            return Decision(action="FOLD", amount=0, reasoning="No valid moves found.")

        return best_decision
