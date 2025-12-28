from typing import List
from phevaluator import evaluate_cards
from treys import Card as TreysCard, Evaluator as TreysEvaluator

class HandEvaluator:
    def __init__(self):
        self.treys_evaluator = TreysEvaluator()

    def get_rank_int(self, card_str: str) -> int:
        if len(card_str) != 2:
             raise ValueError(f"Invalid card string: {card_str}")
        return TreysCard.new(card_str)

    def evaluate_hand(self, board_strs: List[str], hand_strs: List[str]) -> int:
        if not board_strs and not hand_strs:
            return 7463

        all_cards = board_strs + hand_strs
        if len(all_cards) < 5:
             return 7463

        try:
            rank = evaluate_cards(*all_cards)
            # print(f"DEBUG EVAL: Input={all_cards} Rank={rank}")
            return rank
        except Exception as e:
            print(f"ERROR EVAL: {e}")
            return 7463

    def get_hand_class(self, score: int) -> str:
        if score > 7462: return "Preflop/Unknown"
        class_int = self.treys_evaluator.get_rank_class(score)
        return self.treys_evaluator.class_to_string(class_int)

    def analyze_texture(self, board_strs: List[str]) -> dict:
        if not board_strs:
            return {"type": "preflop"}

        suits = [s[1] for s in board_strs]
        suit_counts = {s: suits.count(s) for s in set(suits)}
        max_suit = max(suit_counts.values()) if suit_counts else 0

        is_flush_possible = max_suit >= 3
        is_flush_draw_on_board = max_suit == 2

        return {
            "is_flush_possible": is_flush_possible,
            "is_flush_draw_on_board": is_flush_draw_on_board,
            "board_len": len(board_strs)
        }
