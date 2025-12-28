import time
import sys
import os
from multiprocessing import Pool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.simulate_population import simulate_hand
from scripts.run_mda_analysis import analyze_and_lock
from data.models import Base

# Setup DB
DB_URL = os.environ.get("DB_URL", "sqlite:///poker_brain_simulation.db")
engine = create_engine(DB_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def worker_play_batch(n_hands):
    """
    Worker function to simulate hands in a separate process.
    """
    # Create new session per process
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        simulate_hand(session, n_hands)
    finally:
        session.close()

def train_loop():
    print("=== STARTING MASSIVE TRAINING LOOP ===")
    cycle = 0
    BATCH_SIZE = 100 # Small for demo, usually 10,000
    N_WORKERS = 2 # Parallel processes

    while True:
        cycle += 1
        print(f"\n--- CYCLE {cycle} ---")

        # 1. GENERATE DATA (Self-Play)
        print(f"Generating {BATCH_SIZE * N_WORKERS} hands in parallel...")
        with Pool(processes=N_WORKERS) as pool:
            pool.map(worker_play_batch, [BATCH_SIZE] * N_WORKERS)

        # 2. ANALYZE & IMPROVE
        print("Analyzing Population Tendencies...")
        session = Session()
        analyze_and_lock(session)
        session.close()

        # 3. UPDATE AGENTS (Mock)
        print("Updating Agent Neural Networks with new Strategy...")
        # In real impl, we would reload the weights here.

        # Stop for demo after 1 cycle
        if cycle >= 1:
            print("=== TRAINING CYCLE COMPLETE (Demo Stop) ===")
            break

        time.sleep(1)

if __name__ == "__main__":
    train_loop()
