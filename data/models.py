from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Numeric, SmallInteger
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class DimPlayer(Base):
    __tablename__ = 'dim_players'

    player_id = Column(Integer, primary_key=True)
    player_name_hash = Column(String, unique=True, index=True)
    cluster_type = Column(String)
    hud_profile_json = Column(String)

class DimBoardTexture(Base):
    __tablename__ = 'dim_board_textures'

    texture_id = Column(Integer, primary_key=True)
    description = Column(String)
    high_card_rank = Column(Integer)
    is_paired = Column(Boolean)
    is_monotone = Column(Boolean)
    straight_potential = Column(SmallInteger)

class FactHandAction(Base):
    __tablename__ = 'fact_hand_actions'

    # Removed autoincrement=True as Integer PK implies it in standard SQL/ORM behavior usually
    id = Column(Integer, primary_key=True)
    time = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    hand_id = Column(String, index=True)
    player_id = Column(Integer, ForeignKey('dim_players.player_id'))

    street = Column(SmallInteger)
    action_type = Column(String)
    amount = Column(Numeric)
    pot_size = Column(Numeric)
    effective_stack = Column(Numeric, nullable=True)

    board_texture_id = Column(Integer, ForeignKey('dim_board_textures.texture_id'), nullable=True)
    facing_bet_ratio = Column(Float, nullable=True)

    player = relationship("DimPlayer")
    board_texture = relationship("DimBoardTexture")
