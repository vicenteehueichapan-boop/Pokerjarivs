from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..data.models import FactHandAction

class NodeLockingEngine:
    def __init__(self, db_session: Session):
        self.session = db_session

    def get_population_tendency(self, street: int, action_type: str, board_texture_id: int) -> float:
        """
        Queries the MDA (Database) to find the frequency of an action in similar spots.
        Returns float (0.0 - 1.0).
        """
        # SQL: SELECT count(*) FROM facts WHERE ...
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
        """
        Compares GTO baseline vs Population and generates a UPI lock script if deviation is high.
        """
        # 1. Get Population Stats
        pop_fold_freq = self.get_population_tendency(
            context['street'], "FOLD", context.get('texture_id', 0)
        )

        # 2. Compare with GTO (Assumed Baseline)
        gto_fold_freq = 0.45 # Example fixed baseline or query solver

        # 3. Detect Deviation
        # If population folds 60% vs 45% GTO -> Lock Node to 60% Fold.
        if abs(pop_fold_freq - gto_fold_freq) > 0.10:
            # We construct a lock command
            # This is simplified; real locking requires setting strat for every hand in range.
            return f"lock_node {node_id} FOLD {pop_fold_freq}"

        return ""
