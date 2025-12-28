import sys
import os
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path if run directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.models import Base, FactHandAction, DimPlayer
from data.ingestion import HandHistoryImporter

DB_URL = os.environ.get("DB_URL", "sqlite:///poker_brain_simulation.db")
engine = create_engine(DB_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def simulate_hand(session, n_hands=1):
    """
    Simulates hands for training data.
    """
    importer = HandHistoryImporter(session)
    # print(f"Simulating {n_hands} hands...")

    for i in range(n_hands):
        hand_id = f"train_hand_{random.randint(0, 1000000)}"

        # Simple Scenario: Blind vs Blind
        # SB (Nit) vs BB (Maniac)

        # Posts
        importer.record_action(hand_id, "NitNick", 0, "POST", 0.5, 0.5)
        importer.record_action(hand_id, "ManiacMike", 0, "POST", 1.0, 1.5)

        # Action
        # Nit Raises
        importer.record_action(hand_id, "NitNick", 0, "RAISE", 3.0, 4.5)
        # Maniac 3-bets
        importer.record_action(hand_id, "ManiacMike", 0, "RAISE", 10.0, 14.5)

        # Nit Decision (The Leak)
        if random.random() < 0.70:
            importer.record_action(hand_id, "NitNick", 0, "FOLD", 0.0, 14.5)
        else:
            importer.record_action(hand_id, "NitNick", 0, "CALL", 7.0, 21.5)

        session.commit()

if __name__ == "__main__":
    session = Session()
    simulate_hand(session, n_hands=500)
