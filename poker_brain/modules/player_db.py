import sqlite3
import os
from dataclasses import dataclass

@dataclass
class PlayerStats:
    hands: int
    vpip_count: int
    pfr_count: int

    @property
    def vpip(self) -> float:
        return self.vpip_count / self.hands if self.hands > 0 else 0.0

    @property
    def pfr(self) -> float:
        return self.pfr_count / self.hands if self.hands > 0 else 0.0

class PlayerDB:
    def __init__(self, db_path="poker_brain_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS players (
                player_id TEXT PRIMARY KEY,
                hands INTEGER DEFAULT 0,
                vpip_count INTEGER DEFAULT 0,
                pfr_count INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()

    def get_player_stats(self, player_id: str) -> PlayerStats:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT hands, vpip_count, pfr_count FROM players WHERE player_id = ?', (player_id,))
        row = c.fetchone()
        conn.close()

        if row:
            return PlayerStats(hands=row[0], vpip_count=row[1], pfr_count=row[2])
        return PlayerStats(0, 0, 0)

    def update_player_stats(self, player_id: str, is_vpip: bool, is_pfr: bool):
        """
        Updates stats for a player. Call this at end of hand or during observation.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Check if exists
        c.execute('SELECT hands, vpip_count, pfr_count FROM players WHERE player_id = ?', (player_id,))
        row = c.fetchone()

        if row:
            hands, v, p = row
            c.execute('''
                UPDATE players
                SET hands = ?, vpip_count = ?, pfr_count = ?
                WHERE player_id = ?
            ''', (hands + 1, v + (1 if is_vpip else 0), p + (1 if is_pfr else 0), player_id))
        else:
            c.execute('''
                INSERT INTO players (player_id, hands, vpip_count, pfr_count)
                VALUES (?, 1, ?, ?)
            ''', (player_id, 1 if is_vpip else 0, 1 if is_pfr else 0))

        conn.commit()
        conn.close()
