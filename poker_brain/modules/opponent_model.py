from typing import List, Set, Optional
from .preflop_charts import get_opening_range
from ..model import Villain
from treys import Card

class OpponentModel:
    """
    Estimates opponent ranges based solely on Position and Stack/Action context.
    Strictly adheres to available inputs (No HUD stats).
    """

    def __init__(self):
        pass

    def get_range_list(self, villain: Villain) -> List[str]:
        """
        Returns the list of range strings for the villain based on their position.
        """
        # 1. Base Range from Position (The most reliable signal without stats)
        # UTG is tight, BTN is wide.
        base_range = get_opening_range(villain.position)

        # 2. Stack Size Heuristics (Optional / Advanced)
        # Without knowing the blind level, raw stack size is ambiguous.
        # However, if we assume the game context implies standard 100bb stacks,
        # we might detect 'short stackers' (often tighter or shove-heavy) vs 'deep stacks'.
        # For this MVP, relying on strict Position Charts is safer than guessing stack depth.

        # Future Upgrade: If we receive 'blind_level' or 'stack_in_bb', we can adjust.
        # e.g. if stack < 40bb, remove speculative hands (suited connectors) and keep high cards.

        return base_range

    def parse_range(self, range_strs: List[str]) -> List[List[int]]:
        """
        Parses a list of range strings into a list of specific hand combos (treys ints).
        Returns a list of pairs: [[c1, c2], [c3, c4], ...]
        """
        combos = []
        seen_hashes = set()

        ranks = "23456789TJQKA"
        suits = "shdc"

        def r_idx(r): return ranks.index(r)

        for r_str in range_strs:
            try:
                current_combos = []
                if "+" in r_str and len(r_str) >= 2 and r_str[0] == r_str[1]:
                    start_rank = r_str[0]
                    idx = r_idx(start_rank)
                    for i in range(idx, len(ranks)):
                        r = ranks[i]
                        c_suits = [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3)]
                        for s1_i, s2_i in c_suits:
                            c1 = Card.new(f"{r}{suits[s1_i]}")
                            c2 = Card.new(f"{r}{suits[s2_i]}")
                            current_combos.append([c1, c2])

                elif "s" in r_str and "+" in r_str:
                    high = r_str[0]
                    low = r_str[1]
                    low_idx = r_idx(low)
                    high_idx = r_idx(high)
                    for i in range(low_idx, high_idx):
                        kicker = ranks[i]
                        for s in suits:
                            c1 = Card.new(f"{high}{s}")
                            c2 = Card.new(f"{kicker}{s}")
                            current_combos.append([c1, c2])

                elif "o" in r_str and "+" in r_str:
                    high = r_str[0]
                    low = r_str[1]
                    low_idx = r_idx(low)
                    high_idx = r_idx(high)
                    for i in range(low_idx, high_idx):
                        kicker = ranks[i]
                        for s1 in suits:
                            for s2 in suits:
                                if s1 == s2: continue
                                c1 = Card.new(f"{high}{s1}")
                                c2 = Card.new(f"{kicker}{s2}")
                                current_combos.append([c1, c2])

                elif "s" in r_str and "+" not in r_str:
                    h = r_str[0]
                    k = r_str[1]
                    for s in suits:
                        c1 = Card.new(f"{h}{s}")
                        c2 = Card.new(f"{k}{s}")
                        current_combos.append([c1, c2])

                elif "o" in r_str and "+" not in r_str:
                    h = r_str[0]
                    k = r_str[1]
                    for s1 in suits:
                        for s2 in suits:
                            if s1 == s2: continue
                            c1 = Card.new(f"{h}{s1}")
                            c2 = Card.new(f"{k}{s2}")
                            current_combos.append([c1, c2])

                for c in current_combos:
                    c_sorted = sorted(c)
                    h = (c_sorted[0], c_sorted[1])
                    if h not in seen_hashes:
                        seen_hashes.add(h)
                        combos.append(c)

            except Exception:
                continue

        return combos
