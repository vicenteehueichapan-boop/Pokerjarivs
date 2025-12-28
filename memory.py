from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class GameEvent:
    phase: str
    action: str
    reasoning: str
    villain_stacks: Dict[str, float] = field(default_factory=dict)
    villain_positions: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())

class HandHistory:
    def __init__(self):
        self.events: List[GameEvent] = []

    def add_event(self, phase, action, reasoning, villain_stacks, villain_positions):
        self.events.append(GameEvent(phase, action, reasoning, villain_stacks, villain_positions))
        
    def get_last_stacks(self) -> Dict[str, float]:
        if not self.events: return {}
        return self.events[-1].villain_stacks

class DecisionMemory:
    def __init__(self):
        self.tables = {}
        # ═══ FIX #3: Tracking de cartas para detección de nueva mano ═══
        self._last_hero_cards: Dict[int, List[str]] = {}

    def get_history_text(self, mesa_id: int) -> str:
        if mesa_id not in self.tables: return ""
        history = self.tables[mesa_id].events
        txt = ""
        for event in history:
            # Format: "seat1(BB): 100bb"
            s_str = ", ".join([
                f"{s}({event.villain_positions.get(s, 'Unknown')}): {a}bb" 
                for s, a in event.villain_stacks.items()
            ])
            txt += f"--- FASE PREVIA: {event.phase.upper()} ---\nRivales: [{s_str}]\nTu Acción: {event.action}\nRazón: {event.reasoning}\n\n"
        return txt

    def get_last_stacks(self, mesa_id: int) -> Dict[str, float]:
        return self.tables[mesa_id].get_last_stacks() if mesa_id in self.tables else {}

    def add_event(self, mesa_id, phase, action, reasoning, villain_stacks, villain_positions):
        if mesa_id not in self.tables: self.tables[mesa_id] = HandHistory()
        self.tables[mesa_id].add_event(phase, action, reasoning, villain_stacks, villain_positions)

    def clear_table(self, mesa_id):
        self.tables[mesa_id] = HandHistory()

    def is_new_phase(self, mesa_id, current_phase):
        """DEPRECATED: Usar is_new_hand() para detección más robusta."""
        if mesa_id not in self.tables or not self.tables[mesa_id].events: return True
        return self.tables[mesa_id].events[-1].phase != current_phase

    # ═══ FIX #3: Nueva detección de mano basada en cartas ═══
    def is_new_hand(self, mesa_id: int, current_phase: str, hero_cards: list) -> bool:
        """
        Detecta nueva mano usando múltiples señales (más robusto que is_new_phase).
        
        Args:
            mesa_id: ID de la mesa
            current_phase: Fase actual (preflop/flop/turn/river)
            hero_cards: Cartas actuales del hero
            
        Returns:
            True si es una nueva mano
        """
        # 1. Primera vez en esta mesa
        if mesa_id not in self.tables or not self.tables[mesa_id].events:
            self._last_hero_cards[mesa_id] = list(hero_cards) if hero_cards else []
            return True
        
        # 2. Cambio de cartas = 100% nueva mano
        prev_cards = self._last_hero_cards.get(mesa_id, [])
        current_sorted = sorted(hero_cards) if hero_cards else []
        prev_sorted = sorted(prev_cards) if prev_cards else []
        
        if current_sorted != prev_sorted:
            self._last_hero_cards[mesa_id] = list(hero_cards) if hero_cards else []
            return True
        
        # 3. Transición hacia atrás en fases (RIVER→PREFLOP, etc)
        phase_order = {'preflop': 0, 'flop': 1, 'turn': 2, 'river': 3}
        last_phase = self.tables[mesa_id].events[-1].phase.lower()
        current = current_phase.lower() if current_phase else 'preflop'
        
        if phase_order.get(current, 0) < phase_order.get(last_phase, 0):
            self._last_hero_cards[mesa_id] = list(hero_cards) if hero_cards else []
            return True
        
        return False