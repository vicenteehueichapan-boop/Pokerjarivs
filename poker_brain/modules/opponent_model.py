from typing import List, Set
from .preflop_charts import get_opening_range
from treys import Card

class OpponentModel:
    """
    Estimates opponent ranges using GTO charts and parses them into usable card lists.
    """

    def __init__(self):
        pass

    def get_range_list(self, villain_position: str) -> List[str]:
        """
        Returns the list of range strings (e.g. ["77+", "AJs+"]) for the villain.
        """
        # For now, we assume they are the 'Opener' if they are active and we are reacting.
        # A real system would track who opened.
        # If villain matches "UTG" etc.
        return get_opening_range(villain_position)

    def parse_range(self, range_strs: List[str]) -> List[List[int]]:
        """
        Parses a list of range strings into a list of specific hand combos (treys ints).
        Returns a list of pairs: [[c1, c2], [c3, c4], ...]
        """
        combos = []
        ranks = "23456789TJQKA"
        suits = "shdc" # spades, hearts, diamonds, clubs

        # Helper to get index
        def r_idx(r): return ranks.index(r)

        for r_str in range_strs:
            try:
                # 1. Pairs: "77+"
                if "+" in r_str and r_str[0] == r_str[1]:
                    start_rank = r_str[0]
                    idx = r_idx(start_rank)
                    for i in range(idx, len(ranks)):
                        r = ranks[i]
                        # Generate all 6 combos of pair
                        # s/h, s/d, s/c, h/d, h/c, d/c
                        c_suits = [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3)]
                        for s1_i, s2_i in c_suits:
                            c1 = Card.new(f"{r}{suits[s1_i]}")
                            c2 = Card.new(f"{r}{suits[s2_i]}")
                            combos.append([c1, c2])

                # 2. Suited: "AJs+"
                elif "s" in r_str and "+" in r_str:
                    # AJs+ -> AJs, AQs, AKs
                    high = r_str[0]
                    low = r_str[1]
                    low_idx = r_idx(low)
                    high_idx = r_idx(high)

                    for i in range(low_idx, high_idx):
                        kicker = ranks[i]
                        # Suited combos (4)
                        for s in suits:
                            c1 = Card.new(f"{high}{s}")
                            c2 = Card.new(f"{kicker}{s}")
                            combos.append([c1, c2])

                # 3. Offsuit: "AQo+"
                elif "o" in r_str and "+" in r_str:
                     # AQo+ -> AQo, AKo
                    high = r_str[0]
                    low = r_str[1]
                    low_idx = r_idx(low)
                    high_idx = r_idx(high)

                    for i in range(low_idx, high_idx):
                        kicker = ranks[i]
                        # Offsuit combos (12)
                        for s1 in suits:
                            for s2 in suits:
                                if s1 == s2: continue
                                c1 = Card.new(f"{high}{s1}")
                                c2 = Card.new(f"{kicker}{s2}")
                                combos.append([c1, c2])

                # 4. Single Hand: "QJs"
                elif "s" in r_str and "+" not in r_str:
                    h = r_str[0]
                    k = r_str[1]
                    for s in suits:
                        c1 = Card.new(f"{h}{s}")
                        c2 = Card.new(f"{k}{s}")
                        combos.append([c1, c2])

                # 5. Single Hand Offsuit: "KQo" or just "KQ" usually implies offsuit or all?
                # Let's assume explicit 'o' or pairs.
                # This parser is basic.

            except Exception:
                continue # Skip malformed

        return combos
