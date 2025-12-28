"""Builds flop prompts with shared postflop framework."""

from typing import Dict, Any

from backend.decision_engine.prompts.utils import build_mdf_section, format_players_info, format_available_actions
from backend.decision_engine.prompts.feature_formatter import summarize_engine_features
from backend.decision_engine.spot_advisor import get_spot_guidance, get_pot_profile, get_spr_bucket

# ═══ RANGOS GTO REALES (Investigación: TwoPlusTwo, MyPokerCoaching, GTO Wizard) ═══
# Fuente: NL25 ZOOM population data 2024

# % de apertura RFI por posición
OPEN_RANGES = {
    "UTG": {"pct": "12-15%", "hands": "TT+, AJs+, KQs, AQo+"},
    "HJ": {"pct": "16-18%", "hands": "77+, ATs+, KJs+, AJo+"},
    "CO": {"pct": "25-28%", "hands": "55+, A8s+, KTs+, QJs, ATo+"},
    "BTN": {"pct": "40-50%", "hands": "22+, A2s+, K5s+, Q8s+, J9s+, 65s+, Kxo+"},
    "SB": {"pct": "35-40%", "hands": "Similar a BTN pero polarizado (3bet o fold)"},
}

# % defensa BB vs cada posición (2.5bb open)
BB_DEFENSE_VS = {
    "UTG": {"total": "17-20%", "3bet": "3-5%", "call": "12-15%"},
    "HJ": {"total": "22-25%", "3bet": "4-5%", "call": "18-20%"},
    "CO": {"total": "28-32%", "3bet": "5-6%", "call": "23-26%"},
    "BTN": {"total": "40-44%", "3bet": "5-6%", "call": "35-38%"},
    "SB": {"total": "50-55%", "3bet": "8-10%", "call": "40-45%"},
}


def get_dynamic_range_section(hero_pos: str, villain_positions: Dict) -> str:
    """
    Genera información de rangos específica basada en posiciones reales.
    
    Args:
        hero_pos: Posición del héroe
        villain_positions: Dict con posiciones de villanos {seat_id: "BB"}
    """
    lines = ["📐 RANGOS DINÁMICOS (GTO vs POBLACIÓN):"]
    
    # Rango de apertura del héroe
    if hero_pos in OPEN_RANGES:
        open_data = OPEN_RANGES[hero_pos]
        lines.append(f"• Tu rango de apertura ({hero_pos}): {open_data['pct']} → {open_data['hands']}")
    
    # Rango de defensa de cada villain
    for seat_id, vil_pos in villain_positions.items():
        if vil_pos == "BB" and hero_pos in BB_DEFENSE_VS:
            defense = BB_DEFENSE_VS[hero_pos]
            lines.append(f"• BB defiende vs {hero_pos}: {defense['total']} (call {defense['call']}, 3bet {defense['3bet']})")
        elif vil_pos in OPEN_RANGES:
            open_data = OPEN_RANGES[vil_pos]
            lines.append(f"• {vil_pos} abre con: {open_data['pct']} → {open_data['hands']}")
    
    if len(lines) == 1:
        lines.append("• (Sin datos específicos de posición)")
    
    return "\n".join(lines)

def _pot_profile_blocks(active_profile: str) -> str:
    srp_line = (
        "SRP (raise único) → rangos amplios, ventaja de nuts repartida."
        " C-bet 60-70% en boards secos, reduce en texturas mojadas."
    )
    threebet_line = (
        "3-BET POT → rangos comprimidos, SPR bajo."
        " C-bet alta frecuencia en boards altos, controla en texturas coordinadas."
    )

    if active_profile == '3bet':
        return f"✅ {threebet_line}"
    return f"✅ {srp_line}"


def _get_cbet_recommendation(engine_features: Dict, pot: float, hero_is_aggressor: bool, board_texture: str) -> str:
    """
    Genera recomendación de C-bet sizing basada en overcards y textura.
    
    Lógica: Más overcards = más fold equity = sizing más grande.
    NL25 Zoom: Pool foldea 60-65% vs c-bet, sizing dinámico es muy +EV.
    """
    if not hero_is_aggressor:
        return ""  # Solo aplica cuando somos el agresor preflop
    
    # Extraer overcards del motor C# (format: {'type': 'TwoOvercards', 'highCardRank': 'Ace'})
    overcards_data = engine_features.get('overcards', {}) if engine_features else {}
    oc_type = overcards_data.get('type', '') if isinstance(overcards_data, dict) else ''
    if oc_type == 'TwoOvercards':
        overcards = 2
    elif oc_type == 'OneOvercard':
        overcards = 1
    else:
        overcards = 0
    has_flush_draw = engine_features.get('draw', {}).get('isFlushDraw', False) if engine_features else False
    has_straight_draw = engine_features.get('draw', {}).get('isStraightDraw', False) if engine_features else False
    
    # Determinar sizing basado en overcards y draws
    if overcards >= 5:
        sizing_pct = 66
        reason = "5+ overcards → máx fold equity. Board amenaza overcards."
    elif overcards >= 3:
        sizing_pct = 50
        reason = "3-4 overcards → sizing medio. Balance protection/value."
    elif overcards >= 1:
        sizing_pct = 33
        reason = "1-2 overcards → sizing pequeño. Board más seco."
    else:
        sizing_pct = 25
        reason = "0 overcards → sizing mínimo. Tu par probablemente ahead."
    
    # Ajustes por textura y draws
    texture_adj = ""
    if "mojado" in board_texture.lower() or "wet" in board_texture.lower():
        sizing_pct = min(sizing_pct + 15, 80)
        texture_adj = "⚠️ Board mojado: +15% sizing para denial de equity."
    
    if has_flush_draw or has_straight_draw:
        draw_type = []
        if has_flush_draw:
            draw_type.append("FD")
        if has_straight_draw:
            draw_type.append("OESD")
        texture_adj += f" Tienes {'+'.join(draw_type)} → bet como semi-bluff."
    
    sizing_bb = round(pot * (sizing_pct / 100), 1)
    
    return f"""
=== 🎯 C-BET RECOMMENDATION (Overcard Logic) ===
Overcards Hero: {overcards}
Recommended Sizing: {sizing_pct}% pot ({sizing_bb} bb)
Reason: {reason}
{texture_adj}

NL25 Insight: Pool foldea 60-65% vs c-bet. Tu sizing debe maximizar fold equity + protección.
================================================
"""

def build_flop_prompt(context: Dict[str, Any]) -> str:
    # 1. Obtener resumen estratégico del motor C#
    engine_features = context.get('engine_features')
    hand_eval_text = summarize_engine_features(engine_features)

    # Extraer datos del contexto
    pot = context.get('pot', 10)
    stack = context.get('stack', 100)
    position = context.get('hero_position', 'Unknown')
    rivals = context.get('rivals', 1)
    board = context.get('community_cards', [])
    hero_cards = context.get('hero_cards', [])
    
    # Calcular perfiles dinámicamente (con street correcta)
    pot_profile = get_pot_profile(pot, rivals, street='Flop')
    spr = context.get('spr') or (stack / pot if pot > 0 else 10)
    spr_bucket = get_spr_bucket(spr)
    
    villain_action = context.get('villain_action', 'unknown')
    villain_bet_bb = context.get('villain_bet_bb', 0.0)
    villain_bet_pct = context.get('villain_bet_pct', 0.0)
    board_texture = context.get('textura_board', 'desconocido')
    
    # Determinar si hero es agresor (Mejorado)
    hero_is_aggressor = context.get('is_aggressor', False)
    if 'preflop_line' in context:
         hero_is_aggressor = (context.get('preflop_line') in {'open', '3-bet', '4-bet'})
    elif context.get('hero_position') in ['BTN', 'CO', 'SB'] and context.get('pot', 0) < 12:
         # Heurística fallback
         hero_is_aggressor = True

    oop_positions = {'BB', 'SB'}
    is_oop = position in oop_positions
    
    # Formatear información de jugadores
    players_info = ""
    if context.get('villain_stacks'):
        players_info = "\n" + format_players_info(
            context.get('villain_stacks', {}),
            context.get('villain_positions', {}),
            stack,
            position,
            pot,
        )

    # ═══ NUEVO: Rangos dinámicos según posición real ═══
    villain_positions_dict = context.get('villain_positions', {})
    dynamic_ranges = get_dynamic_range_section(position, villain_positions_dict)

    # Bloques dinámicos de Población y Táctica
    population_reads = f"""
{dynamic_ranges}

📊 POPULATION TENDENCIES NL25 ZOOM:
• Fold vs c-bet flop: 60-65% (ligeramente overfoldean)
• Call flop con Ax débil: 70% (pagófilos)
• Fold turn después de call flop: 45-50% (underfoldean)
• Bluff frequency river: 12-18% (underbluffean vs teórico 33%)
➡️ Ajusta tu estrategia: más c-bets en flop, más barrels en turn, menos hero-calls river
"""

    # FRAMEWORK DE CONTEO DE COMBOS DETALLADO (Mejora estratégica 2025-11-22)
    equity_framework = """
🎲 EQUITY & COMBO COUNTING FRAMEWORK (EXAMPLE GUIDELINES):

PASO 1: DEFINIR RANGO PRE-FLOP DEL VILLANO
- Estima el rango de defensa típico (NL25: ~35-40% BB vs BTN).
- Categorías: Premium (AA-JJ, AK), Broadway Medium (AQ-AT, KQs), Pares Medios (22-TT), Suited Connectors/Gappers, Suited Ace Low.
- Total combos aprox: ~175-195.

PASO 2: CLASIFICAR RANGO EN ESTE FLOP ESPECÍFICO
- Board: Analiza textura (ej. As 7d 2c).
- 🔴 VALUE FUERTE (Top 10-15%): Sets, Two Pair, Top Pair Top Kicker. Combos que te stackean.
- 🟡 VALUE MARGINAL (25-35%): Top Pair débil (Ax bajos), Second Pair fuerte. Manos que pagan 1 o 2 calles.
- 🟢 DRAWS & BACKDOORS (5-10%): Flush Draws, Straight Draws, Gutshots.
- ⚪ AIRE PURO (40-50%): Missed broadway, underpairs sin set, aire total. Manos que foldean a C-bet.

PASO 3: CALCULAR EQUITY PROMEDIO
- Estima tu equity contra cada categoría.
- Calcula el promedio ponderado.

PASO 4: BLOCKER ANALYSIS
- ¿Qué cartas tienes? (ej. Ah Kd).
- ¿Qué combos de value bloqueas? (ej. Ah bloquea AA, AK, AQ, A7s).
- ¿Qué combos de bluff bloqueas? (ej. Kd bloquea KQs, KJ).
- Impacto neto: Si bloqueas value, tu Fold Equity aumenta.

PASO 5: FOLD EQUITY ESTIMATION
- Estima % de fold vs tu sizing (33%, 50%, 66%).
- ¿Es EV+ apostar considerando el fold equity + tu equity si pagan?

⚠️ INSTRUCCIÓN: Usa este framework en tu campo "razonamiento" con los datos de la mano actual.
"""

    # Historial de fase anterior
    historia_preflop = context.get('historia_preflop', '')
    historia_section = ""
    if historia_preflop:
        historia_section = f"\n📜 HISTORIA PREFLOP:\n{historia_preflop}\n"
    
    # 🎯 SPOT GUIDANCE
    # Asegurar que contexto tiene street
    context['street'] = 'Flop'
    spot_guidance = get_spot_guidance(context)
    spot_section = f"\n{spot_guidance}\n" if spot_guidance else ""

    # JSON Output Mejorado (Solicitado por usuario)
    response_schema = "\n".join([
        "{",
        '  "contexto_percibido": {',
        f'    "board": {str(board)},',
        f'    "pot_status": "{pot_profile.upper()}",',
        '    "villain_action": "Describe acción villano"',
        '  },',
        '  "accion": "bet",',
        '  "accion_detalle": "c-bet 50% pot (3.75bb)",',
        '  "amount_bb": 3.75,',
        '  "pot_fraction": 0.5,',
        '  "tipo_jugada": "value",',
        '',
        '  "contexto": {',
        f'    "pot_profile": "{pot_profile.upper()}",',
        f'    "pot_type": "{pot_profile.upper()}",',
        f'    "spr": {spr:.2f},',
        f'    "spr_bucket": "{spr_bucket}",',
        f'    "textura": "{board_texture}",',
        f'    "effective_stack": {stack}',
        '  },',
        '',
        '  "hero_situation": {',
        f'    "is_aggressor": {str(hero_is_aggressor).lower()},',
        f'    "posicion": "{"OOP" if is_oop else "IP"}",',
        '    "continuation_pct": 0.0,',
        '    "fold_equity_estimada": 0.0',
        '  },',
        '',
        '  "villain_analysis": {',
        '    "range_estimate": "Describe rango percibido (Ax, PP, aire)",',
        '    "estimated_fold_pct": 0.0',
        '  },',
        '',
        '  "hero_strength": {',
        '    "mano": "Describe mano y fuerza",',
        '    "equity_vs_range": 0.0,',
        '    "outs_to_improve": 0,',
        '    "blockers_effect": "Describe efecto de blockers"',
        '  },',
        '',
        '  "plan_turn": {',
        '    "si_mejora": "Acción si mejora",',
        '    "si_blank": "Acción si blank",',
        '    "si_empeora": "Acción si empeora"',
        '  },',
        '',
        '  "razonamiento": "Usa el COMBO COUNTING FRAMEWORK: 1. Rango Preflop... 2. Clasificación Flop... 3. Equity... 4. Blockers... 5. Fold Equity...",',
        '  "decision_final": "BET 50% pot porque [razón resumida]",',
        '  "confianza": "high"',
        "}"
    ])

    # ═══ NUEVO: Bloque de acciones disponibles (detección visual de botones) ═══
    available_actions = context.get('available_actions', [])
    is_facing_bet = context.get('is_facing_bet')
    actions_block = format_available_actions(available_actions, is_facing_bet)
    
    # ═══ [FIX #5] C-BET RECOMMENDATION: Overcard-based sizing ═══
    cbet_advice = _get_cbet_recommendation(engine_features, pot, hero_is_aggressor, board_texture)

    return f"""
{hand_eval_text}
{historia_section}
{spot_section}

{actions_block}

INSTRUCCIONES PARA INTERPRETAR:
- Prioriza los datos calculados por el motor.
- Usa la evaluación textual para identificar el tipo de mano.
- ⚠️ CRITICAL: "BOARD PAIR" means the pair is on the table, NOT in your hand. You only have kicker value. DO NOT confuse with trips/sets.
- No inventes outs: usa solo los que aparecen en los datos técnicos.

ANÁLISIS FLOP EXPLOTATIVO - NL25 ZOOM

DATOS TÉCNICOS (NO MODIFICAR, SOLO USAR):
- Board: {board}
- Textura: {board_texture}
- Hero cards: {hero_cards}
- Posición: {position}
- Pot: {pot}bb
- Stack: {stack}bb

⚠️ Usa estos datos técnicos tal cual.

POT PROFILE: {pot_profile.upper()} | SPR={spr:.2f} ({spr_bucket})

{players_info}

{population_reads}

{equity_framework}

{cbet_advice}

{_pot_profile_blocks(pot_profile)}

FORMATO RESPUESTA (JSON ESTRICTO):
{response_schema}

REGLAS FINALES:
- RESPUESTA ÚNICA EN JSON.
- Si eres agresor, usa "continuation_pct". Si defiendes, usa "defense_pct" (agrega el campo si es necesario).
"""