"""Builds turn prompts with shared postflop framework."""


from typing import Any, Dict, Optional
from backend.decision_engine.prompts.utils import build_mdf_section, format_players_info, format_available_actions
from backend.decision_engine.prompts.feature_formatter import summarize_engine_features
from backend.decision_engine.spot_advisor import get_spot_guidance, get_pot_profile, get_spr_bucket

# Funciones auxiliares necesarias para el builder
def _implied_text(spr: Optional[float]) -> str:
    if spr is None:
        return "SPR desconocido"
    if spr >= 6:
        return f"SPR={spr:.1f} → implied odds excelentes (6:1+)"
    if spr >= 3:
        return f"SPR={spr:.1f} → implied moderadas"
    return f"SPR={spr:.1f} → SPR bajo, necesitas equity directa"


def _river_plan_templates(pot_profile: str) -> str:
    srp_plan = (
        "SRP: si completas → value 70-90% pot;"
        " si cae blank → puedes tercer barrel 40-55% pot;"
        " si scare card empeora → check/fold salvo blockers fuertes."
    )
    threebet_plan = (
        "3-BET POT: SPR bajo, cualquier mejora fuerte se stackea."
        " Blank → shove o bet 65% pot con manos top."
        " Scare card → evalúa bloquear combos de nuts antes de bluffcatch."
    )
    
    if pot_profile == '3bet':
        return f"✅ {threebet_plan}"
    return f"✅ {srp_plan}"

def build_turn_prompt(context: Dict[str, Any]) -> str:
   # 1. Obtener resumen estratégico del motor C#
   engine_features = context.get('engine_features')
   hand_eval_text = summarize_engine_features(engine_features)

   # Extraer datos del contexto
   pot = context.get('pot', 30)
   stack = context.get('stack', 90)
   board = context.get('community_cards', [])
   position = context.get('hero_position', 'Unknown')
   hero_cards = context.get('hero_cards', [])
   rivals = context.get('rivals', 1)
   turn_card = board[3] if len(board) >= 4 else 'N/A'
   
   # Calcular perfiles dinámicamente (Turn)
   pot_profile = get_pot_profile(pot, rivals, street='Turn')
   spr = context.get('spr') or (stack / pot if pot > 0 else 10)
   spr_bucket = get_spr_bucket(spr)

   villain_action = context.get('villain_action', 'unknown')
   villain_bet_bb = context.get('villain_bet_bb', 0.0)
   villain_bet_pct = context.get('villain_bet_pct', 0.0)
   players_info = ""
   if context.get('villain_stacks'):
      players_info = "\n" + format_players_info(
         context.get('villain_stacks', {}),
         context.get('villain_positions', {}),
         stack,
         position,
         pot,
      )
   implied_advice = _implied_text(spr)
   mdf_text, required_defense_pct = build_mdf_section(villain_bet_pct)
   river_plan = _river_plan_templates(pot_profile)
   
   # Historial de fase anterior
   historia_flop = context.get('historia_flop', '')
   historia_section = ""
   if historia_flop:
       historia_section = f"\n📜 HISTORIA FLOP:\n{historia_flop}\n"
   
   # POPULATION READS TURN (NL25 ZOOM)
   population_reads = """
📊 POPULATION TENDENCIES NL25 ZOOM (TURN):
- Fold vs 2nd barrel: 45-50% (underfoldean vs teórico 60%).
- Float flop → fold turn: 55% (con aire, no con marginal).
- Call turn con draws: 85% (inelastic to sizing).
- Check-raise turn: 3-5% (muy infrecuente, SIEMPRE fuerte/nuts).
- Donk bet turn: 8-12% (polar: nuts o bluff débil).
➡️ Ajustes: Barrel turn agresivamente por valor (55-65% pot), menos bluffs puros vs call station.
"""

   # 🎯 DETECTAR SPOT POSTFLOP Y CARGAR GUÍA ESTRATÉGICA
   context['street'] = 'Turn'
   spot_guidance = get_spot_guidance(context)
   spot_section = ""
   if spot_guidance:
       spot_section = f"\n{spot_guidance}\n"
   
   # ═══ NUEVO: Bloque de acciones disponibles (detección visual de botones) ═══
   available_actions = context.get('available_actions', [])
   is_facing_bet = context.get('is_facing_bet')
   actions_block = format_available_actions(available_actions, is_facing_bet)
   
   response_schema = "\n".join([
      "{",
      '   "contexto_percibido": {',
      f'       "board_turn": "{turn_card}",',
      f'       "pot_status": "{pot_profile.upper()}",',
      '       "previous_street_action": "Describe acción flop"',
      '   },',
      '   "accion": "bet/check/raise/fold/call",',
      '   "action_type": "bet/check/call/raise_to/fold",',
      '   "amount_bb": 0.0,',
      '   "to_call_bb": 0.0,',
      '   "pot_fraction": 0.0,',
      '   "tipo_jugada": "value/thin_value/bluff/semi-bluff/protection/pot_control",',
      f'   "pot_profile": "{pot_profile.upper()}",',
      f'   "pot_type": "{pot_profile.upper()}",',
      f'   "spr_bucket": "{spr_bucket}",',
      f'   "villain_bet_pct": {villain_bet_pct},',
      '   "required_defense_pct": 0.0,',
      '   "defense_pct": 0.0,',
      '   "plan_river": "Describe 3 escenarios (mejora/blank/empeora) con tamaños específicos",',
      '   "confianza": "high/medium/low",',
      f'   "razonamiento": "Turn {turn_card} → [impacto exacto]. Outs=[X] (~Y%). Pot odds vs bet {villain_bet_pct}% pot. {implied_advice}. Necesito defender {required_defense_pct}% y estoy defendiendo [defense_pct].",',
      '   "decision_final": "ACCIÓN ESPECÍFICA: [BET/CHECK/etc + tamaño] porque [argumento resumido]"',
      "}"
   ])
   # ORDEN HOMOGÉNEO: Título, formato, historia, datos clave, procedimiento, herramientas, checklist, formato JSON y notas
   return f"""
{hand_eval_text}
{historia_section}
{spot_section}

{actions_block}

INSTRUCCIONES PARA INTERPRETAR:
- Usa la evaluación textual para identificar el tipo de mano, su fuerza y posibles draws.
- ⚠️ CRITICAL: "BOARD PAIR" means the pair is on the table, NOT in your hand. You only have kicker value. DO NOT confuse with trips/sets.
- La descripción y ranking te ayudan a clasificar correctamente la mano y evitar errores de interpretación.
- No inventes outs ni draws: usa solo los que aparecen en la evaluación y los datos técnicos.
- Si la evaluación dice “backdoor”, no lo consideres como draw real salvo que el contexto lo justifique.
ANÁLISIS TURN EXPLOTATIVO - NL25 ZOOM

Si el reasoning no empieza así, corrige y vuelve a intentarlo.

DATOS TÉCNICOS (NO MODIFICAR, SOLO USAR):
- Board: {board}
- Carta turn: {turn_card}
- Hero cards: {hero_cards}
- Posición: {position}
- Pot: {pot}bb
- Stack: {stack}bb

⚠️ Debes usar los datos técnicos tal cual aparecen arriba en tu razonamiento. No los inventes ni los modifiques.

POT PROFILE: {pot_profile.upper()} | SPR={spr if spr is not None else 'N/A'} ({spr_bucket})

{players_info}

{population_reads}

{mdf_text}

{river_plan}

FORMATO RESPUESTA (JSON ESTRICTO):
{response_schema}

REGLAS PARA "defense_pct":
- Indica qué % de tu rango continúas con la línea elegida (0-100). Debe ser ≥ {required_defense_pct}% cuando defiendes vs apuesta, salvo razones exploit claras.
- RESPUESTA ÚNICA EN JSON: termina SIEMPRE con un solo objeto JSON válido que incluya todos los campos del formato anterior (pot_profile, pot_type, spr_bucket, villain_bet_pct, required_defense_pct, defense_pct). No añadas texto extra después del JSON.
"""