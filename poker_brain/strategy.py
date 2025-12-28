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

    def estimate_equity(self, hero_hand: list[str], board: list[str], simulations=1000) -> float:
        """
        Estimates equity by simulating the remaining streets against a random hand.
        """
        # Convert hero cards and board to treys format
        hero_cards_int = [Card.new(c) for c in hero_hand]
        board_cards_int = [Card.new(c) for c in board]

        wins = 0
        ties = 0

        for _ in range(simulations):
            deck = Deck()
            full_deck = deck.GetFullDeck()
            # Remove known cards (inefficient but safe for MVP)
            known = set(hero_cards_int + board_cards_int)
            remaining_deck = [c for c in full_deck if c not in known]
            random.shuffle(remaining_deck)

            # Villain Hand (Random for now, could use OpponentModel ranges in future)
            villain_hand = [remaining_deck.pop(), remaining_deck.pop()]

            cards_needed = 5 - len(board_cards_int)
            runout = []
            if cards_needed > 0:
                for _ in range(cards_needed):
                    runout.append(remaining_deck.pop())

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
        # 1. Analyze Context
        if context.hero.cards:
             equity = self.estimate_equity(context.hero.cards, context.board, simulations=500)
        else:
             equity = 0.0

        # 2. Generate Options
        candidates = self.game_tree.generate_candidate_actions(context)

        # 3. Evaluate Options
        best_decision = None
        best_ev = -float('inf')

        for decision in candidates:
            ev = self.game_tree.evaluate_node(decision, context, equity)
            decision.ev_estimation = ev
            decision.reasoning = f"Simulated EV: {ev:.2f} (Equity: {equity:.2f})"

            if ev > best_ev:
                best_ev = ev
                best_decision = decision

        # Fallback if empty (shouldn't happen)
        if not best_decision:
            return Decision(action="FOLD", amount=0, reasoning="No valid moves found.")

        return best_decision
