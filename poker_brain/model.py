from dataclasses import dataclass, field
from typing import List, Optional, Literal

Street = Literal["PREFLOP", "FLOP", "TURN", "RIVER"]
Position = Literal["SB", "BB", "UTG", "UTG+1", "MP", "MP+1", "CO", "BTN"]
ActionType = Literal["FOLD", "CHECK", "CALL", "RAISE", "ALLIN"]

@dataclass
class Hero:
    position: Position
    cards: List[str]  # e.g. ["Ah", "Kd"]
    stack: float
    current_investment: float  # Amount put in current street

@dataclass
class Villain:
    position: Position
    status: str  # "ACTIVE", "FOLDED", "ALLIN"
    stack: float
    current_investment: float
    name: Optional[str] = None # Added for DB persistence
    stats: Optional[dict] = field(default_factory=dict)

@dataclass
class GameContext:
    game_id: str
    street: Street
    pot_size: float
    current_bet: float  # The amount to call to stay in hand (total for this street)
    board: List[str]    # e.g. ["2d", "5s", "9h"]
    hero: Hero
    villains: List[Villain]

@dataclass
class Decision:
    action: ActionType
    amount: float = 0.0
    reasoning: str = ""
    ev_estimation: float = 0.0
