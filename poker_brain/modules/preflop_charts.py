from typing import Dict, List

# Standard 6-Max Opening Ranges (Simplified GTO)
# Notation:
# "22+": Pairs 22 through AA
# "A2s+": Suited Ace from A2s to AKs
# "ATo+": Offsuit Ace from ATo to AKo
# "KJs+": Suited King KJs, KQs
# "QJs": QJs only
# "JTs": JTs only

# We need a parser for this notation later.
# For simplicity in MVP, we define these as lists of generic hands or keep string representation
# and let the OpponentModel parse them.

RANGES_6MAX_OPEN: Dict[str, List[str]] = {
    "UTG": [
        "77+",
        "AJs+", "KQs",
        "AQo+"
    ], # Tight (~15%)
    "MP": [
        "55+",
        "ATs+", "KJs+", "QJs", "JTs",
        "AJo+", "KQo"
    ], # (~19%)
    "CO": [
        "22+",
        "A2s+", "KTo+", "QTo+", "JTo",
        "A8o+", "K9s+", "Q9s+", "J9s+", "T9s", "98s", "87s"
    ], # (~30%)
    "BTN": [
        "22+",
        "A2s+", "K2s+", "Q5s+", "J7s+", "T7s+", "97s+", "86s+",
        "A2o+", "K7o+", "Q9o+", "J9o+", "T9o"
    ], # Wide (~50%)
    "SB": [
        "22+",
        "A2s+", "K5s+", "Q8s+", "J8s+",
        "A7o+", "K9o+", "QTo+"
    ], # Blind vs Blind (~40%)
    "BB": [
        # BB doesn't "Open", they Defend. But if they 3bet...
        "88+", "AQs+", "AQs+"
    ]
}

def get_opening_range(position: str) -> List[str]:
    """Returns the list of hand patterns for a given position."""
    # Normalize position names if needed
    pos = position.upper()
    if pos in RANGES_6MAX_OPEN:
        return RANGES_6MAX_OPEN[pos]
    return RANGES_6MAX_OPEN["BTN"] # Default to wide if unknown
