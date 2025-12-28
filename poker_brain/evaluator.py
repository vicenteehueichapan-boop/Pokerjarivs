from treys import Card, Evaluator
from typing import List

class HandEvaluator:
    def __init__(self):
        self.evaluator = Evaluator()

    def get_rank_int(self, card_str: str) -> int:
        """
        Converts a card string like 'Ah' to treys integer representation.
        """
        # treys expects capital letter for Rank and lowercase for Suit.
        # e.g. "Ah"
        if len(card_str) != 2:
             raise ValueError(f"Invalid card string: {card_str}")
        return Card.new(card_str)

    def evaluate_hand(self, board_strs: List[str], hand_strs: List[str]) -> int:
        """
        Returns the treys score (lower is better).
        1 = Royal Flush, 7462 = 7-5-4-3-2 unsuited.
        """
        board = [self.get_rank_int(c) for c in board_strs]
        hand = [self.get_rank_int(c) for c in hand_strs]

        return self.evaluator.evaluate(board, hand)

    def get_rank_class(self, score: int) -> int:
        """
        Returns the class of hand (1=Straight Flush, ..., 9=High Card)
        Note: Treys uses 1 as strongest class? Let's check docs or source.
        Actually treys.Evaluator.get_rank_class(score) returns integer.
        """
        return self.evaluator.get_rank_class(score)

    def class_to_string(self, class_int: int) -> str:
        return self.evaluator.class_to_string(class_int)
