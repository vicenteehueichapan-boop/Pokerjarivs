"""
ActionFlowManager: Orquestador de Flujo y Turnos de Poker
=========================================================

Este módulo implementa la lógica de "Game Flow" para determinar cuándo es el turno del Hero.
Usa una máquina de estados determinista basada en reglas de Poker (Preflop/Postflop)
y cambios en los stacks (Deltas) para inferir acciones.

Objetivo:
- Evitar llamadas prematuras a DeepSeek (cuando villanos previos no han actuado).
- Evitar llamadas múltiples (si ya decidimos).
- Detectar "Check" vs "Thinking" (inferencia de flujo).
"""

import time
import logging
import threading
from typing import Dict, List, Optional, Set
from backend.vision.position_mapper import PositionMapper

logger = logging.getLogger("ActionFlowManager")

class TableState:
    """Estado mutable de una mesa específica para tracking de flujo."""
    def __init__(self, mesa_id: int):
        self.mesa_id = mesa_id
        self.phase: str = "unknown"
        self.community_cards: List[str] = []
        
        # Snapshot de la última actualización estable
        self.villain_stacks: Dict[int, float] = {}  # {seat: stack}
        self.pot: float = 0.0
        self.last_update_time: float = time.time()
        
        # Tracking de acciones en la calle actual
        # {seat: {'action': 'bet', 'amount': 10.5, 'timestamp': 12345}}
        self.street_actions: Dict[int, Dict] = {}
        self.acted_players: Set[int] = set() # Seats que ya actuaron al menos una vez
        
        self.max_bet_this_street: float = 0.0
        self.aggressor_seat: Optional[int] = None
        self.hero_stack: float = 0.0
        self.calculated_pot: float = 0.0  # Smart Pot (Math-based)
        self.hero_cards: List[str] = []
        self.dealer_pos: int = -1
        self.active_player: int = -1
        self.timestamp: float = 0.0

    def reset_hand(self):
        """Reinicia el estado para una nueva mano."""
        self.community_cards = []
        self.hero_cards = []
        self.pot = 0.0
        self.calculated_pot = 0.0
        # Mantenemos stacks para continuidad, se actualizarán en el siguiente frame

class ActionFlowManager:
    """
    Gestor del flujo de acciones y estado de las mesas.
    Centraliza el estado para que ActionDeductor y DecisionEngine
    tengan una fuente de verdad única.
    """
    
    def __init__(self):
        self.tables: Dict[int, TableState] = {}
        self.logger = logging.getLogger("ActionFlow")
        self.lock = threading.Lock()
    
    def get_table_state(self, mesa_id: int) -> TableState:
        """Obtiene el estado de una mesa, creándolo si no existe."""
        with self.lock:
            if mesa_id not in self.tables:
                self.tables[mesa_id] = TableState(mesa_id)
            return self.tables[mesa_id]

    def reset_hand(self, mesa_id: int):
        """Fuerza el reinicio de estado para una mesa (Nueva Mano)."""
        state = self.get_table_state(mesa_id)
        with self.lock:
            old_pot = state.calculated_pot
            state.reset_hand()
            self.logger.info(f"[Mesa {mesa_id}] 🔄 HAND RESET (Prev Pot: {old_pot:.1f} BB)")

    def update_state(
        self,
        mesa_id: int,
        ocr_pot: float,
        hero_stack: float,
        villain_stacks: Dict[int, float],
        community_cards: List[str],
        hero_cards: List[str],
        dealer_pos: int
    ) -> float:
        """
        Actualiza el estado y retorna el 'Smart Pot' (Pot Calculado).
        
        La lógica 'Smart Pot' prioriza el cálculo matemático (stack deltas)
        sobre el OCR directo, usándolo solo para sincronización inicial
        o correcciones menores.
        """
        state = self.get_table_state(mesa_id)
        
        with self.lock:
            # 1. Calcular contribuciones al pot (Stack Deltas)
            pot_delta = 0.0
            
            # Hero delta
            if state.hero_stack > 0 and hero_stack > 0:
                diff = state.hero_stack - hero_stack
                if diff > 0 and diff < 500: # Sanity check (evitar glitches de OCR extremos)
                    pot_delta += diff

            # Villain deltas
            for seat, stack in villain_stacks.items():
                if seat in state.villain_stacks:
                    prev = state.villain_stacks[seat]
                    if prev > 0 and stack > 0:
                        diff = prev - stack
                        if diff > 0 and diff < 500:
                            pot_delta += diff
            
            # Actualizar Pot Calculado
            state.calculated_pot += pot_delta
            
            # 2. Sincronización Inteligente con OCR (Hybrid Logic)
            # Caso A: Start of Hand / Desync masivo hacia arriba
            # Si el OCR ve un pot grande y nosotros tenemos 0 (o muy poco), confiamos en OCR (ej: llegamos tarde a la mano)
            if state.calculated_pot < 1.0 and ocr_pot > 2.0:
                 self.logger.info(f"[Mesa {mesa_id}] 💰 Pot Sync (Init): {state.calculated_pot:.1f} -> {ocr_pot:.1f}")
                 state.calculated_pot = ocr_pot

            # Caso B: Sanity Check - Si difieren por poco, confiamos en OCR (maneja rake, rounding)
            diff_abs = abs(state.calculated_pot - ocr_pot)
            if diff_abs < 2.0 and ocr_pot > 0:
                # Ajuste suave
                 state.calculated_pot = ocr_pot
            
            # Caso C: OCR dice 0 pero nosotros tenemos pot (El BUG Zombie/Glitch)
            # Si state.calculated_pot > 5 y ocr_pot == 0 -> IGNORAMOS OCR. Mantenemos el calculado.
            
            # Actualizar valores raw en estado
            state.pot = state.calculated_pot # La fuente de verdad ahora es la calculada(o validada)
            state.hero_stack = hero_stack
            state.villain_stacks = villain_stacks.copy()
            state.community_cards = community_cards
            state.hero_cards = hero_cards
            state.dealer_pos = dealer_pos
            state.timestamp = time.time()
            
            return state.calculated_pot

    def _register_action(self, state: TableState, seat: int, action_type: str, amount: float):
        """Registra una acción detectada."""
        is_raise = amount > state.max_bet_this_street
        
        state.street_actions[seat] = {
            'action': 'raise' if is_raise else 'call',
            'amount': amount,
            'total_bet': amount, # Simplificación, idealmente acumularía
            'timestamp': time.time()
        }
        state.acted_players.add(seat)
        
        if amount > state.max_bet_this_street:
            state.max_bet_this_street = amount
            state.aggressor_seat = seat
            # Si hubo raise, re-abrimos acción para los que ya actuaron (menos el raiser)
            # En realidad, en poker engine, todos deben actuar de nuevo excepto el raiser.
            # Pero para simplificar: si hay raise, consideramos que la ronda no ha terminado.
            pass

    def is_hero_turn(self, mesa_id: int, hero_position: str, active_seats: List[int]) -> bool:
        """
        DETERMINA SI ES TURNO DEL HERO.
        Lógica Atómica basada en Posición y Estado de Acción.
        """
        state = self.get_table_state(mesa_id)
        
        # Pre-requisitos básicos
        if not hero_position or hero_position == 'Unknown':
            logger.warning(f"[Mesa {mesa_id}] Hero position unknown, cannot determine turn.")
            return False
            
        # 1. Obtener Orden de Acción (Queue)
        action_order = PositionMapper.get_action_order(
            # Lista de posiciones activas mapeadas
            list(PositionMapper.get_villain_positions(hero_position, active_seats).values()) + [hero_position],
            phase='preflop' if state.phase == 'preflop' else 'postflop'
        )
        
        # 2. Filtrar Queue hasta Hero
        # Ejemplo: ['SB', 'BB', 'UTG', 'HERO(MP)', 'CO'] -> Checkeamos SB, BB, UTG
        try:
            hero_idx = action_order.index(hero_position)
            preceding_actors = action_order[:hero_idx]
        except ValueError:
            return False # Hero no está en el orden??

        # 3. Verificar si TODOS los precedentes han actuado
        # Necesitamos mapear Posición -> SeatID para verificar state.street_actions
        # Esto requiere iterar active_seats y buscar su posición
        
        villain_pos_map = PositionMapper.get_villain_positions(hero_position, active_seats)
        # Invertir mapa: { 'SB': 1, 'BB': 2 ... }
        pos_to_seat = {v: k for k, v in villain_pos_map.items()}
        
        for pos in preceding_actors:
            seat_id = pos_to_seat.get(pos)
            if seat_id is None: continue # Jugador ya no está sentado?
            
            # CRITERIO DE ESPERA:
            # Si el jugador NO ha actuado en esta calle -> NO ES MI TURNO
            # (Excepción: Si estamos en Big Blind preflop y todos foldearon/callearon, 
            #  eventualmente será mi turno, pero 'acted' debería cubrirlo si trackeamos bien)
            
            # Verificamos si seat_id está en acted_players
            if seat_id not in state.acted_players:
                # Caso Check: Si max_bet == 0, y el tiempo pasó... ¿Asumimos check?
                # Por seguridad: Si hay un jugador ACTIVO antes que yo que NO ha puesto plata (y no detectamos check explícito)
                # DEBEMOS ESPERAR.
                # A menos que sea un Check Implicit (pasó tiempo y no hubo acción).
                # Por ahora, seamos conservadores: RETORNA FALSE (ESPERAR).
                # logger.debug(f"Waiting for {pos} (Seat {seat_id}) to act.")
                return False
                
            # Si actuó, verificar si su apuesta es suficiente (Call complete)
            # Esto es complejo sin saber stack sizes exactos, pero con 'acted' es un buen proxy.
            
        # Si llegamos aquí, todos los villanos anteriores actuaron.
        # ¿He actuado YO?
        # En teoría, si el sistema me llama, es porque quizás NO he actuado.
        # O si actué, quizás fue hace mucho.
        # Pero ActionFlowManager se usa para disparar la decisión.
        # Así que asumimos que si llegamos aquí, ES MI TURNO.
        
        return True
