import sys
import os
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.models import FactHandAction, DimPlayer
from solver.node_locking import NodeLockingEngine

DB_URL = os.environ.get("DB_URL", "sqlite:///poker_brain_simulation.db")
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)

def analyze_and_lock(session):
    # print("--- Analyzing Population ---")

    # Check Fold Freq of NitNick facing 3bet (Proxy logic)
    # Count folds by NitNick preflop
    folds = session.query(func.count(FactHandAction.id)).filter(
        FactHandAction.street == 0,
        FactHandAction.action_type == "FOLD",
        FactHandAction.player_id.in_(
            session.query(DimPlayer.player_id).filter(DimPlayer.player_name_hash == "NitNick")
        )
    ).scalar()

    # Count total actions by NitNick preflop (Raise, Call, Fold)
    # Since he posts SB, raises, then faces 3bet...
    # We count actions where amount=0 (Fold) vs amount>0 (Call of 3bet).
    # This is a hacky proxy for the specific node.

    # Better proxy: Count hands where NitNick folded / Total hands NitNick played
    # Total hands = count distinct hand_id where player=NitNick

    total_hands = session.query(func.count(func.distinct(FactHandAction.hand_id))).filter(
        FactHandAction.player_id.in_(
            session.query(DimPlayer.player_id).filter(DimPlayer.player_name_hash == "NitNick")
        )
    ).scalar()

    if total_hands == 0: return

    # In our sim, he folds 70% of hands.
    fold_freq = folds / total_hands

    print(f"Detected Population Fold Freq: {fold_freq:.2f}")

    if fold_freq > 0.55:
        print(f"!!! LEAK DETECTED (Overfolding). Generating Lock Script...")
        locker = NodeLockingEngine(session)
        script = f"lock_node node_OOP_3bet_defense FOLD {fold_freq:.2f}"
        print(f"Solver Command: {script}")

if __name__ == "__main__":
    session = Session()
    analyze_and_lock(session)
