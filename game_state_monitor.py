"""
Game State Monitor
==================
Sistema de seguimiento de estado para deducir acciones de villanos
basándose en cambios de Pot y Stacks (Diferencial).

Lógica:
- Mantiene memoria del estado anterior (Pot, Hero Stack, Villain Stacks).
- Calcula deltas para inferir quién apostó y cuánto.
- Filtra errores de lectura OCR (saltos imposibles).
"""

from typing import Dict, Optional, Any, List
import time

class TableState:
    """Estado snapshot de una mesa en un momento T"""
    def __init__(self):
        self.timestamp = 0.0
        self.pot = 0.0
        self.hero_stack = 0.0
        self.villain_stacks: Dict[str, float] = {}  # {'seat1': 100.0, ...}
        self.villain_positions: Dict[str, str] = {} # {'seat1': 'SB', ...}
        self.street = "preflop"  # preflop, flop, turn, river
        self.last_aggressor_seat: Optional[str] = None
        self.current_bet: float = 0.0  # Apuesta actual a igualar
        self.hero_position: Optional[str] = None

class TableMonitor:
    """Monitor inteligente para UNA mesa"""
    
    # Orden de posiciones Postflop (SB actúa primero)
    POS_ORDER_POSTFLOP = ['SB', 'BB', 'UTG', 'HJ', 'CO', 'BTN']
    # Orden Preflop (UTG actúa primero)
    POS_ORDER_PREFLOP = ['UTG', 'HJ', 'CO', 'BTN', 'SB', 'BB']
    
    # Orden estándar cíclico (Seat 1 es izquierda de Hero, etc.)
    # Asumiendo Hero -> Seat1 -> Seat2 -> Seat3 -> Seat4 -> Seat5 -> Hero
    ORDER_6MAX_CLOCKWISE = ['SB', 'BB', 'UTG', 'HJ', 'CO', 'BTN']

    # Umbrales para filtrar errores de OCR
    MIN_BET_BB = 0.5  # Mínimo cambio para considerar apuesta
    MAX_STACK_JUMP = 500.0  # Si un stack cambia >500bb de golpe, es error OCR probable
    
    def __init__(self, mesa_id: int):
        self.mesa_id = mesa_id
        self.state = TableState()
        self.history: List[str] = []  # Log de acciones deducidas
        
    def update(self, 
               current_pot: float, 
               current_hero_stack: float, 
               current_villain_stacks: Dict[str, float],
               current_street: str,
               villain_positions: Dict[str, str] = None,
               hero_position: str = None) -> Dict[str, Any]:
        """
        Actualiza estado y deduce qué pasó desde el último frame.
        
        Args:
            current_pot: Pot total actual
            current_hero_stack: Mi stack
            current_villain_stacks: Dict de stacks de rivales ACTIVOS
            current_street: Calle actual
            villain_positions: Dict mapping 'seatX' -> 'UTG'/'SB'/etc. (Opcional)
            hero_position: Posición detectada del Hero (ej: 'BTN', 'SB')
            
        Returns:
            Dict con contexto de acción deducido (villain_bet, aggressor, etc.)
        """
        now = time.time()
        prev = self.state
        
        # 0. Validar inputs y Mapear Posiciones
        if hero_position:
            self.state.hero_position = hero_position
            # Si no nos dan posiciones explícitas, las inferimos del Hero Pos
            if not villain_positions:
                villain_positions = self._map_positions_from_hero(hero_position)
                self.state.villain_positions = villain_positions
        
        villain_positions = villain_positions or self.state.villain_positions or {}
        
        # 1. Detectar cambio de calle (Reset de apuestas)
        if current_street != prev.street:
            print(f"🔄 Mesa {self.mesa_id}: Cambio de calle {prev.street} -> {current_street}")
            self._reset_street_state(current_street)
            # Actualizar snapshot base para la nueva calle
            self._update_snapshot(now, current_pot, current_hero_stack, current_villain_stacks, current_street)
            return self._get_empty_context()

        # 2. Calcular Deltas
        pot_diff = current_pot - prev.pot
        hero_diff = prev.hero_stack - current_hero_stack
        
        # Detectar apuestas de villanos
        detected_bets = []
        
        # Solo chequeamos villanos que existían en el frame anterior y siguen activos
        for seat, stack in current_villain_stacks.items():
            if seat in prev.villain_stacks:
                prev_stack = prev.villain_stacks[seat]
                villain_diff = prev_stack - stack
                
                # Validar que sea una apuesta real y no ruido OCR
                if self.MIN_BET_BB < villain_diff < self.MAX_STACK_JUMP:
                    detected_bets.append({
                        'seat': seat,
                        'amount': villain_diff
                    })
        
        # 3. Deducir Acción
        action_context = self._get_empty_context()
        
        # Si hubo apuestas detectadas por stack tracking (Prioridad Alta)
        if detected_bets:
            # DESEMPATE POR POSICIÓN:
            # Si hay múltiples apuestas (raro en un frame, pero posible),
            # la acción "relevante" es la última en el orden de turno (el agresor más reciente).
            
            # 1. Asignar posición a cada apuesta
            for bet in detected_bets:
                bet['pos'] = villain_positions.get(bet['seat'], 'Unknown')
                
            # 2. Ordenar por prioridad de turno
            order = self.POS_ORDER_PREFLOP if current_street == 'preflop' else self.POS_ORDER_POSTFLOP
            
            def get_pos_index(p):
                try: return order.index(p)
                except ValueError: return -1
            
            # Ordenar: El que actúa MÁS TARDE es el agresor final
            # (Ej: UTG bet, BTN raise -> BTN es el agresor relevante)
            detected_bets.sort(key=lambda x: get_pos_index(x['pos']))
            
            # Tomar la última acción (la más agresiva/reciente)
            final_aggressor = detected_bets[-1]
            
            # Actualizar estado del monitor
            self.state.current_bet = final_aggressor['amount']
            self.state.last_aggressor_seat = final_aggressor['seat']
            
            action_context['villain_bet_bb'] = final_aggressor['amount']
            action_context['villain_action'] = "bet/raise"
            action_context['aggressor_seat'] = final_aggressor['seat']
            action_context['aggressor_pos'] = final_aggressor['pos']
            
            print(f"🕵️ Mesa {self.mesa_id}: Acción ({final_aggressor['pos']}) -> {final_aggressor['seat']} apostó {final_aggressor['amount']:.1f}bb")

        # Si no detectamos cambio en stacks (quizás OCR falló) pero el Pot subió
        elif pot_diff > self.MIN_BET_BB:
            # Si mi stack no bajó, alguien más tuvo que poner dinero
            if hero_diff < self.MIN_BET_BB:
                # Asumimos apuesta del villano (Fallback)
                # OJO: No sabemos quién fue, pero sabemos CUÁNTO
                inferred_bet = pot_diff
                
                # Si ya había una apuesta previa, esto podría ser un Call o Raise
                # Por simplicidad, asumimos que el incremento del pot es la apuesta/call
                
                action_context['villain_bet_bb'] = inferred_bet
                action_context['villain_action'] = "bet/call (inferido por pot)"
                
                # Actualizar estado interno
                if inferred_bet > self.state.current_bet:
                     self.state.current_bet = inferred_bet # Raise
                
                print(f"🕵️ Mesa {self.mesa_id}: Acción detectada por Pot -> Alguien puso {inferred_bet:.1f}bb")

        # 4. Actualizar Snapshot para el siguiente frame
        self._update_snapshot(now, current_pot, current_hero_stack, current_villain_stacks, current_street)
        
        # Completar contexto con estado acumulado
        action_context['current_bet_bb'] = self.state.current_bet
        if action_context['villain_bet_bb'] == 0 and self.state.current_bet > 0:
             # Si en este frame nadie apostó, pero hay una apuesta pendiente de antes
             action_context['villain_bet_bb'] = self.state.current_bet
             action_context['villain_action'] = "pending_action"

        # Calcular % del pot (Importante para prompts)
        if current_pot > 0:
            action_context['villain_bet_pct'] = action_context['villain_bet_bb'] / current_pot
            
        return action_context

    def _map_positions_from_hero(self, hero_pos: str) -> Dict[str, str]:
        """
        Mapea los asientos seat1..seat5 basándose en la posición del Hero.
        Asume mesa 6-max y orden Hero -> Seat1 -> ... -> Seat5 -> Hero (Clockwise)
        """
        try:
            hero_idx = self.ORDER_6MAX_CLOCKWISE.index(hero_pos)
        except ValueError:
            return {} # Posición inválida
            
        mapping = {}
        # Asumiendo que seat1 está a la izquierda de Hero
        for i in range(1, 6):
            seat_key = f"seat{i}"
            # La posición se mueve 1 a la izquierda en la lista de orden por cada asiento
            pos_idx = (hero_idx + i) % 6
            mapping[seat_key] = self.ORDER_6MAX_CLOCKWISE[pos_idx]
            
        return mapping

    def _reset_street_state(self, new_street: str):
        self.state.street = new_street
        self.state.current_bet = 0.0
        self.state.last_aggressor_seat = None
        
    def _update_snapshot(self, time, pot, hero_stack, villain_stacks, street):
        self.state.timestamp = time
        self.state.pot = pot
        self.state.hero_stack = hero_stack
        self.state.villain_stacks = villain_stacks.copy()
        self.state.street = street
        
    def _get_empty_context(self):
        return {
            'villain_bet_bb': 0.0,
            'villain_bet_pct': 0.0,
            'villain_action': 'check/none',
            'aggressor_seat': None
        }

class GameStateMonitor:
    """Fachada principal para gestionar las 6 mesas"""
    
    def __init__(self):
        self.monitors = {i: TableMonitor(i) for i in range(1, 7)}
        
    def update_table(self, 
                     mesa_id: int, 
                     mesa_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa updates de una mesa y devuelve el contexto de acción enriquecido.
        """
        if mesa_id not in self.monitors:
            return {}
            
        # Extraer datos necesarios de mesa_data
        pot = mesa_data.get('pot', 0.0)
        hero_stack = mesa_data.get('stack', 0.0)
        
        # Extraer stacks de villanos de 'players' o 'villain_stacks'
        # mesa_data tiene 'villain_stack_values' preparado por run_full_backend_test
        # Si no, intentamos extraerlo de 'players'
        villain_stacks = mesa_data.get('villain_stack_values', {})
        if not villain_stacks and 'players' in mesa_data:
            # Intentar extraer de players
            players = mesa_data['players']
            for key, val in players.items():
                if 'stack' in key and isinstance(val, dict):
                    # formato players: {'seat1_stack': {'value': 100}}
                    seat = key.split('_')[0] # seat1
                    if val.get('success'):
                         villain_stacks[seat] = val.get('value', 0.0)
        
        # Detectar calle (Preflop por defecto si no hay cartas)
        comm_cards = mesa_data.get('community_cards', [])
        street = 'preflop'
        if len(comm_cards) == 3: street = 'flop'
        elif len(comm_cards) == 4: street = 'turn'
        elif len(comm_cards) == 5: street = 'river'
        
        # Extraer posición de Hero
        hero_position = None
        if 'hero_position' in mesa_data:
             # A veces viene como ('BTN', 0.9, True) o directo 'BTN'
             hp_raw = mesa_data['hero_position']
             if isinstance(hp_raw, tuple):
                 if hp_raw[2]: # success
                     hero_position = hp_raw[0]
             elif isinstance(hp_raw, str):
                 hero_position = hp_raw

        # Delegar al monitor de la mesa
        action_context = self.monitors[mesa_id].update(
            pot, 
            hero_stack, 
            villain_stacks, 
            street,
            villain_positions=mesa_data.get('villain_positions'),
            hero_position=hero_position
        )
        
        return action_context
