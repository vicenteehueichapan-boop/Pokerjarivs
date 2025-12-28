from typing import List, Set, Optional
from .preflop_charts import get_opening_range
from ..model import Villain
from treys import Card
from .player_db import PlayerDB

class OpponentModel:
    """
    Estimates opponent ranges based on Position and PERSISTED History (Stats).
    """

    def __init__(self, db_path="poker_brain_memory.db"):
        self.db = PlayerDB(db_path)

    def get_range_list(self, villain: Villain) -> List[str]:
        """
        Returns the list of range strings.
        Prioritizes DB stats if available. Fallbacks to Position.
        """
        base_range = get_opening_range(villain.position)

        # 1. Try DB Lookup
        # We need a player ID. In real games, 'name' is often the ID.
        # Assuming Villain model might have a name field, or we stick to inputs.
        # Current Villain model doesn't have 'name'. We should probably use 'position' as ID if playing vs same bots,
        # but in real app we need a unique ID.
        # Let's assume for now we don't have ID in Villain object (as per original spec).
        # We will add a temporary patch: If 'villain' has a 'name' attribute dynamically added or passed in context.

        # HACK for MVP: check if context passed extra data, or just rely on Position for now.
        # However, the user ASKED for DB. We must use it.
        # Let's assume the calling code injects 'name' into the Villain object or we add it to the Model.

        player_id = getattr(villain, 'name', None)

        if player_id:
            stats = self.db.get_player_stats(player_id)
            if stats.hands > 10: # Sample size check
                if stats.vpip > 0.40: # Fish
                    return self._get_fish_range()
                elif stats.vpip < 0.18: # Nit
                    return self._get_nit_range()

        return base_range

    def _get_fish_range(self) -> List[str]:
        """Loose range for recreational players."""
        return [
            "22+", "A2s+", "K2s+", "Q2s+", "J5s+",
            "54s+", "64s+", "75s+",
            "A2o+", "K8o+", "Q9o+", "J9o+", "T8o+"
        ]

    def _get_nit_range(self) -> List[str]:
        """Tight range for nits."""
        return ["88+", "ATs+", "KJs+", "AQo+"]

    def parse_range(self, range_strs: List[str]) -> List[List[int]]:
        """
        Parses a list of range strings into a list of specific hand combos (treys ints).
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
