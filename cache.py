from typing import Dict, Optional, Any
import hashlib
import json

class DecisionCache:
    def __init__(self):
        self._cache = {}

    def _generate_key(self, mesa_data: Dict[str, Any], history_str: str) -> str:
        """Generates a unique key based on critical game state."""
        # Key factors: cards, board, pot, stack, history
        key_elements = [
            str(sorted(mesa_data.get('hero_cards', []))),
            str(sorted(mesa_data.get('community_cards', []))),
            str(mesa_data.get('pot', 0)),
            str(mesa_data.get('stack', 0)),
            # ═══ FIX #1: Incluir contexto de botones para evitar cache hits incorrectos ═══
            str(sorted(mesa_data.get('available_actions', []))),
            str(mesa_data.get('is_facing_bet', False)),
            history_str
        ]
        key_str = "|".join(key_elements)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, mesa_data: Dict[str, Any], history_str: str = "") -> Optional[Dict[str, Any]]:
        key = self._generate_key(mesa_data, history_str)
        return self._cache.get(key)

    def set(self, mesa_data: Dict[str, Any], decision: Dict[str, Any], history_str: str = ""):
        key = self._generate_key(mesa_data, history_str)
        self._cache[key] = decision
