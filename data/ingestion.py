import pokerkit
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .models import FactHandAction, DimPlayer, DimBoardTexture
from datetime import datetime

class HandHistoryImporter:
    def __init__(self, session: Session):
        self.session = session

    def ingest_hand_text(self, hh_text: str):
        pass

    def _get_or_create_player(self, name: str) -> DimPlayer:
        player = self.session.query(DimPlayer).filter_by(player_name_hash=name).first()
        if player:
            return player

        # Try to create
        try:
            player = DimPlayer(player_name_hash=name, cluster_type="Unknown")
            self.session.add(player)
            self.session.commit()
            return player
        except IntegrityError:
            self.session.rollback()
            # Race condition hit, someone else created it. Query again.
            return self.session.query(DimPlayer).filter_by(player_name_hash=name).one()

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
            time=datetime.now()
        )
        self.session.add(fact)
