"""
Preflop Prompt Builder
======================
Construye prompt especializado para decisiones preflop
"""

from typing import Dict, Any
from backend.decision_engine.prompts.feature_formatter import summarize_engine_features
from backend.decision_engine.prompts.utils import format_players_info, format_available_actions
from backend.decision_engine.preflop_range_manager import PreflopRangeManager

# Instancia global para cachear cargas
range_manager = PreflopRangeManager()


def build_preflop_prompt(context: Dict[str, Any]) -> str:
    # 1. Obtener resumen estratégico del motor C#
    engine_features = context.get('engine_features')
    hand_eval_text = summarize_engine_features(engine_features)

    """Construye prompt para decisiones preflop"""

    # Extraer datos directamente de mesa_data
    stack = context.get('stack', 100)
    rivals = context.get('rivals', 0)
    pot = context.get('pot')
    position = context.get('hero_position', 'Unknown')
    hero_cards = context.get('hero_cards', [])
    
    # CONSULTAR RANGE MANAGER
    range_data = range_manager.get_range_data(context)
    
    # 🔒 Validación: Al menos POT debe ser válido
    if pot is None or pot <= 0:
        pot = 1.5

    # MEJORADO: Detección automática de contexto
    if stack <= 15:
        stack_advice = "PUSH/FOLD territory"
        mode = "ICM/CHIPEV"
    elif stack <= 50:
        stack_advice = "Stack medio"
        mode = "MEDIUM_STACK"
    else:
        stack_advice = "Stack profundo"
        mode = "DEEP_STACK"

    # NUEVO: Formatear info de players si está disponible
    players_info = ""
    if context.get('villain_stacks'):
        players_info = "\n" + format_players_info(
            context.get('villain_stacks', {}),
            context.get('villain_positions', {}),
            stack,
            position,
            pot
        )

    chart_block = f"""
    📘 ESTRATEGIA DE RANGOS (PREFLOP RANGE MANAGER):
    - Escenario detectado: {range_data['scenario']}
    - Tabla usada: {range_data['chart_file']}
    - Mano normalizada: {range_data['hand_key']}
    
    🧠 INSTRUCCIÓN ESTRATÉGICA (SEGÚN TABLA):
    "{range_data['instruction']}"
    
    📊 FRECUENCIAS DE ACCIÓN (TABLA):
    {range_data['actions']}
    """

    # ═══ NUEVO: Bloque de acciones disponibles (detección visual de botones) ═══
    available_actions = context.get('available_actions', [])
    is_facing_bet = context.get('is_facing_bet')
    actions_block = format_available_actions(available_actions, is_facing_bet)

    return f"""
    {hand_eval_text}

    {actions_block}

    INSTRUCCIONES PARA INTERPRETAR:
    - Usa la evaluación textual para identificar el tipo de mano.
    - SIGUE LA INSTRUCCIÓN ESTRATÉGICA DE LA TABLA si existe. Es tu fuente principal de verdad.
    
    ANÁLISIS PREFLOP EXPLOTATIVO - NL25 ZOOM

    DATOS TÉCNICOS:
    - Hero cards: {hero_cards}
    - Posición: {position}
    - Stack: {stack}bb [{mode}]
    - Pot: {pot}bb
    - Jugadores activos: {rivals}

    {players_info}
    
    {chart_block}

    FORMATO RESPUESTA (JSON ESTRICTO):
    {{
        "contexto_percibido": {{
            "posicion_hero": "Define tu posición (UTG/MP/CO/BTN/SB/BB)",
            "accion_previa": "Describe qué pasó antes (Limp/Open Raise/Clean)",
            "stack_effective_bb": 0.0
        }},
        "accion": "fold/call/raise/3bet/4bet/allin/push",
        "action_type": "fold/call/raise_to/bet/push/check",
        "amount_bb": 0.0,
        "to_call_bb": 0.0,
        "pot_fraction": 0.0,
        "confidence": "high/medium/low",
        "reasoning": "Mano [X] en rango [posición]. Seguir instrucción: {range_data['instruction']}.",
        "decision_final": "ACCIÓN ESPECÍFICA: [FOLD/CALL/RAISE] porque [razón basada en tabla]"
    }}
    """
