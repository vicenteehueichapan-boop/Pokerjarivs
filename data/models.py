from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, BigInteger, Numeric, SmallInteger
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class DimPlayer(Base):
    __tablename__ = 'dim_players'

    player_id = Column(Integer, primary_key=True)
    player_name_hash = Column(String, unique=True, index=True)
    cluster_type = Column(String) # "Reg", "Fish", "Whale"
    # JSONB in Postgres, String/JSON in SQLite
    hud_profile_json = Column(String)

class DimBoardTexture(Base):
    __tablename__ = 'dim_board_textures'

    texture_id = Column(Integer, primary_key=True)
    description = Column(String) # "Ace High Monotone"
    high_card_rank = Column(Integer) # 0-12
    is_paired = Column(Boolean)
    is_monotone = Column(Boolean)
    straight_potential = Column(SmallInteger) # 0-3

class FactHandAction(Base):
    """
    Hypertable in TimescaleDB.
    Captures every atomic action in a hand.
    """
    __tablename__ = 'fact_hand_actions'

    id = Column(BigInteger, primary_key=True)
    time = Column(DateTime(timezone=True), server_default=func.now(), index=True) # Partition Key

    hand_id = Column(String, index=True) # Using String for HH UUIDs
    player_id = Column(Integer, ForeignKey('dim_players.player_id'))

    street = Column(SmallInteger) # 0=Pre, 1=Flop, 2=Turn, 3=River
    action_type = Column(String) # "FOLD", "CHECK", "CALL", "BET", "RAISE"
    amount = Column(Numeric)
    pot_size = Column(Numeric)
    effective_stack = Column(Numeric)

    board_texture_id = Column(Integer, ForeignKey('dim_board_textures.texture_id'), nullable=True)

    # Pre-calculated metrics for fast OLAP
    facing_bet_ratio = Column(Float) # Bet size relative to pot faced

    player = relationship("DimPlayer")
    board_texture = relationship("DimBoardTexture")

# Additional dimensions could be added for Situation, GameType, etc.
