import pokerkit
from sqlalchemy.orm import Session
from .models import FactHandAction, DimPlayer, DimBoardTexture
from datetime import datetime

class HandHistoryImporter:
    def __init__(self, session: Session):
        self.session = session

    def ingest_hand_text(self, hh_text: str):
        """
        Parses raw hand history text using PokerKit and populates the DB.
        """
        try:
            # PokerKit generic parser (supports many formats)
            # For this example we assume a compatible format or use raw loading if PokerKit supports it directly
            # PokerKit usually parses specific formats like PokerStars, etc.
            # Let's assume we use `pokerkit.HandHistory.from_text` equivalent or iterate
            # For demonstration, we'll simulate the extraction from a PokerKit 'Hand' object.

            # Simulated usage (since PokerKit API is strict on formats)
            # hand = pokerkit.HandHistory.load(hh_text)
            pass

        except Exception as e:
            print(f"Error parsing hand: {e}")
            return

    def _get_or_create_player(self, name: str) -> DimPlayer:
        player = self.session.query(DimPlayer).filter_by(player_name_hash=name).first()
        if not player:
            player = DimPlayer(player_name_hash=name, cluster_type="Unknown")
            self.session.add(player)
            self.session.commit()
        return player

    def record_action(self, hand_id: str, player_name: str, street: int, action: str, amount: float, pot: float):
        """
        Directly records an action (called by the parser loop).
        """
        player = self._get_or_create_player(player_name)

        fact = FactHandAction(
            hand_id=hand_id,
            player_id=player.player_id,
            street=street,
            action_type=action,
            amount=amount,
            pot_size=pot,
            time=datetime.now() # In real ETL, use hand timestamp
        )
        self.session.add(fact)
        # Batch commit recommended in production
