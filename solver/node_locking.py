from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func
# Absolute import fix
from data.models import FactHandAction

class NodeLockingEngine:
    def __init__(self, db_session: Session):
        self.session = db_session

    def get_population_tendency(self, street: int, action_type: str, board_texture_id: int) -> float:
        total = self.session.query(func.count(FactHandAction.id)).filter(
            FactHandAction.street == street,
            FactHandAction.board_texture_id == board_texture_id
        ).scalar()

        if total == 0: return 0.0

        count = self.session.query(func.count(FactHandAction.id)).filter(
            FactHandAction.street == street,
            FactHandAction.board_texture_id == board_texture_id,
            FactHandAction.action_type == action_type
        ).scalar()

        return count / total

    def generate_lock_script(self, node_id: str, context: dict) -> str:
        # Simplified for demo
        return f"lock_node {node_id} ..."
