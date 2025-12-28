from typing import Dict, List

# Standard 6-Max Opening Ranges (Population Adjusted for NL25)
# These ranges reflect "Average Regular" play.
# UTG is tight. BTN is wide.

RANGES_6MAX_OPEN: Dict[str, List[str]] = {
    "UTG": [
        "77+",
        "ATs+", "KJs+", "QJs", "JTs",
        "AQo+"
    ], # Tight (~14%)
    "UTG+1": [
        "77+",
        "ATs+", "KJs+", "QJs", "JTs",
        "AQo+"
    ], # Alias for MP in 6max sometimes, treating as tight
    "MP": [
        "55+",
        "A9s+", "KTs+", "QTs+", "JTs",
        "AJo+", "KQo"
    ], # (~18%)
    "CO": [
        "22+",
        "A2s+", "K9s+", "Q9s+", "J9s+", "T8s+", "98s", "87s",
        "ATo+", "KJo+", "QJo+"
    ], # (~28%)
    "BTN": [
        "22+",
        "A2s+", "K5s+", "Q8s+", "J8s+", "T7s+", "97s+", "86s+", "75s+", "65s", "54s",
        "A2o+", "K9o+", "Q9o+", "J9o+", "T9o"
    ], # Wide (~45%)
    "SB": [
        "22+",
        "A2s+", "K8s+", "Q9s+", "J9s+",
        "A9o+", "KTo+", "QJo+"
    ], # Blind vs Blind (~35% - often depends on BB)
    "BB": [
        # BB Defending Range (Wide)
        # Often defends any pair, any suited connector, any Ace
        "22+", "A2s+", "K2s+", "Q5s+", "J7s+", "T7s+", "97s+", "87s", "76s",
        "A2o+", "K8o+", "Q9o+", "J9o+", "T8o+"
    ]
}

def get_opening_range(position: str) -> List[str]:
    """Returns the list of hand patterns for a given position."""
    pos = position.upper()
    if pos in RANGES_6MAX_OPEN:
        return RANGES_6MAX_OPEN[pos]
    # Fallback mappings for weird input
    if "UTG" in pos: return RANGES_6MAX_OPEN["UTG"]
    if "MP" in pos: return RANGES_6MAX_OPEN["MP"]
    return RANGES_6MAX_OPEN["BTN"] # Default to wide
