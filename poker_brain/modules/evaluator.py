from treys import Card, Evaluator
from typing import List, Tuple

class HandEvaluator:
    def __init__(self):
        self.evaluator = Evaluator()

    def get_rank_int(self, card_str: str) -> int:
        if len(card_str) != 2:
             raise ValueError(f"Invalid card string: {card_str}")
        return Card.new(card_str)

    def evaluate_hand(self, board_strs: List[str], hand_strs: List[str]) -> int:
        board = [self.get_rank_int(c) for c in board_strs]
        hand = [self.get_rank_int(c) for c in hand_strs]
        if not board: # Preflop
            return 7463 # Worse than worst hand, just a placeholder
        return self.evaluator.evaluate(board, hand)

    def get_hand_class(self, score: int) -> str:
        """
        Returns string like "Pair", "Flush", etc.
        """
        # Treys specific:
        # 1 = Straight Flush
        # ...
        # 9 = High Card
        if score > 7462: return "Preflop/Unknown"
        class_int = self.evaluator.get_rank_class(score)
        return self.evaluator.class_to_string(class_int)

    def analyze_texture(self, board_strs: List[str]) -> dict:
        """
        Returns info about board texture (is it wet? flushy?).
        """
        # MVP Implementation
        if not board_strs:
            return {"type": "preflop"}

        suits = [s[1] for s in board_strs]
        ranks = [s[0] for s in board_strs] # Strings 'A', 'K', etc.

        # Check for Flush draw possibilities on board
        suit_counts = {s: suits.count(s) for s in set(suits)}
        max_suit = max(suit_counts.values()) if suit_counts else 0

        is_flush_possible = max_suit >= 3
        is_flush_draw_on_board = max_suit == 2

        return {
            "is_flush_possible": is_flush_possible,
            "is_flush_draw_on_board": is_flush_draw_on_board,
            "board_len": len(board_strs)
        }
