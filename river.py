"""Builds river prompts with shared postflop framework."""

# Imports
from typing import Dict, Any
from backend.decision_engine.prompts.utils import build_mdf_section, format_players_info, format_available_actions, get_bluff_ratio
from backend.decision_engine.prompts.feature_formatter import summarize_engine_features
from backend.decision_engine.spot_advisor import get_spot_guidance, get_pot_profile, get_spr_bucket
from backend.decision_engine.river_analyzer import RiverAnalyzer

# Funciones auxiliares
def _overbet_context(spr: float | None) -> tuple[str, bool]:
   if spr is None:
      return ("SPR desconocido, compara tamaño relativo del bet para detectar overbets.", False)
   if spr < 0.6:
      return (f"SPR={spr:.2f} (<0.6) → zona de overbets/polarización.", True)
   return (f"SPR={spr:.2f} → ratio estándar, bets 30-90% pot.", False)

def _blocker_guidelines() -> str:
   return (
      "BLOCKERS CLAVE:\n"
      "- Nut flush blockers (Ah/Ks) habilitan bluffs vs rangos polarizados.\n"
      "- Blocking pares máximos (KK en K83r) reduce combos de value rival.\n"
      "- Bloquea bluffs del rival antes de hero-call: si tienes las manos que bluffea, su rango de bluff se reduce."
   )

def _bluffcatch_matrix() -> str:
   return (
      "BLUFFCATCH / OVERBET:"
      "\n- Si enfrentas overbet (>100% pot) defiende solo top MDF con blockers nut."
      "\n- Vs overbets de 125% pot en NL25 está bien OVERFOLDEAR (defender por debajo de MDF) porque el pool casi no bluffea: solo paga con manos fuertes o blockers premium."
      "\n- Si tu bluffcatcher no bloquea los combos de color/nuts (ej. KQ sin carta de color en board con flush posible), FOLD debe ser la línea por defecto. En `river_population_overfold_vs_raise`, KQ sin diamante **debe foldear** siempre; CALL prohibido."
      "\n- Vs sizings ≤70% pot puedes mezclar bluffcatchers sin blockers pero con showdown value."
      "\n- Missed draws con blockers fuertes → mejores candidatos a shove/bluff."
   )

# Función principal
def build_river_prompt(context: Dict[str, Any]) -> str:
   # 1. Obtener resumen estratégico del motor C#
   engine_features = context.get('engine_features')
   hand_eval_text = summarize_engine_features(engine_features)

   pot = context.get('pot', 60)
   stack = context.get('stack', 55)
   board = context.get('community_cards', [])
   position = context.get('hero_position', 'Unknown')
   hero_cards = context.get('hero_cards', [])
   rivals = context.get('rivals', 1)
   
   # Calcular perfiles dinámicamente (River)
   pot_profile = get_pot_profile(pot, rivals, street='River')
   spr = context.get('spr') or (stack / pot if pot > 0 else 10)
   spr_bucket = get_spr_bucket(spr)

   villain_action = context.get('villain_action', 'unknown')
   villain_bet_bb = context.get('villain_bet_bb', 0.0)
   villain_bet_pct = context.get('villain_bet_pct', 0.0)
   villain_pct_display = round(villain_bet_pct * 100, 1)
   aggressor = context.get('aggressor_pos', 'unknown')
   players_info = ""
   if context.get('villain_stacks'):
      players_info = "\n" + format_players_info(
         context.get('villain_stacks', {}),
         context.get('villain_positions', {}),
         stack,
         position,
         pot,
      )
   overbet_text, is_overbet_zone = _overbet_context(spr)
   mdf_text, required_defense_pct = build_mdf_section(villain_bet_pct)
   
   # POPULATION READS RIVER
   population_reads = """
📊 POPULATION TENDENCIES NL25 ZOOM (RIVER):
- Bluff frequency: 12-18% (vs teórico 33% - SEVERO underbluff).
- Hero-call frequency: 45-50% (overcall vs thin value).
- Fold to river bet después de call-call: 35% (solo aire, cuesta tirar top pair).
- River raise: 95% value, 5% bluff (polar extremo hacia value, FOLD a menos que tengas nuts).
➡️ Ajustes: Apuesta thin value agresivamente, fold vs raise salvo nuts, reduce hero-calls marginales.
"""

   # STACK-OFF DECISION FRAMEWORK
   stack_off_plan = f"""
💰 STACK-OFF DECISION FRAMEWORK (SPR={spr:.2f}):
A) HERO SHOVE (Valor):
   • SPR < 3 con top pair+ es mandatory shove por valor vs calling stations.
   • SPR < 2 con cualquier made hand decente.
   • Target: Manos peores que llaman (Top Pair peor, Second Pair heroico).

B) CALL VILLAIN SHOVE (Defensa):
   • Si villain shovea river, asume fuerza extrema en NL25.
   • Call solo con: Top of range o bluffcatchers que bloquean nuts.
   • Fold exploitativo: Si tienes TPTK pero villain raisea all-in river, es set/two pair el 90% de las veces. FOLD es la línea ganadora en el long run.
"""

   river_mdf_line = (
      f"Vs {villain_pct_display}% pot → MDF ≈ {required_defense_pct}% →"
      " defiende ese porcentaje combinando value combos + bluffcatchers con blockers."
   )
   blocker_text = _blocker_guidelines()
   bluffcatch_text = _bluffcatch_matrix()
   # DATOS TÉCNICOS RIVER
   # Usamos el texto ya formateado, no claves sueltas inconsistentes
   tech_summary = hand_eval_text
   
   # CORRECCIÓN: Carta del river explícita para cumplir test
   river_card = board[-1] if board else "Unknown"

   response_schema = "\n".join([
      "{",
      '   "contexto_percibido": {',
      f'       "board_complete": {str(board)},',
      f'       "spr_final": {spr if spr is not None else 0.0},',
      '       "river_card": "Identifica carta exacta"',
      '   },',
      '   "accion": "bet/check/raise/fold/call",',
      '   "tipo_jugada": "max_value/thin_value/bluff_puro/bluffcatcher/fold",',
      f'   "pot_profile": "{pot_profile.upper()}",',
      f'   "required_defense_pct": {required_defense_pct},',
      '   "defense_pct": 0.0,',
      '   "confianza": "high/medium/low",',
      f'   "razonamiento": "Datos motor: {{tech_summary}}. {overbet_text} MDF objetivo {required_defense_pct}%. Pot odds vs bet {villain_pct_display}% pot. Explica si defense_pct ≥ MDF o si exploit justifica desviación.",',
      '   "decision_final": "ACCIÓN ESPECÍFICA: [BET/CHECK/etc + tamaño] porque [argumento matemático breve]"',
      "}"
   ])
   
   # Historial de fases anteriores
   historia_flop = context.get('historia_flop', '')
   historia_turn = context.get('historia_turn', '')
   historia_section = ""
   if historia_flop or historia_turn:
       historia_section = "📜 HISTORIA DE LA MANO:\n"
       if historia_flop:
           historia_section += f"   FLOP: {historia_flop}\n"
       if historia_turn:
           historia_section += f"   TURN: {historia_turn}\n"
       historia_section += "\n"
   
   # 🎯 DETECTAR SPOT POSTFLOP Y CARGAR GUÍA ESTRATÉGICA
   context['street'] = 'River'
   spot_guidance = get_spot_guidance(context)
   spot_section = ""
   if spot_guidance:
       spot_section = f"\n{spot_guidance}\n"
   
   # ═══ NUEVO: Bloque de acciones disponibles (detección visual de botones) ═══
   available_actions = context.get('available_actions', [])
   is_facing_bet = context.get('is_facing_bet')
   actions_block = format_available_actions(available_actions, is_facing_bet)
   
   # ═══ [FIX #1] RIVER ANALYZER: Full Decision Framework ═══
   river_advice_text = ""
   try:
      action_history = context.get('action_history')
      analyzer = RiverAnalyzer(
         hero_cards=hero_cards,
         board=board,
         hand_strength=engine_features or {},
         action_history=action_history,
         pot=pot,
         stack=stack
      )
      # Get FULL river advice framework (not just sizing)
      river_advice_text = analyzer.get_river_advice()
      # Also get sizing table for reference
      sizing_table = analyzer.get_sizing_table()
      river_advice_text += f"\n{sizing_table}"
      
      hand_classification = analyzer.classify_hand_type()
      print(f"🎯 [River] Hand: {hand_classification}, Full advice injected")
   except Exception as e:
      print(f"⚠️ [River] RiverAnalyzer error: {e}")
   
   # ═══ [FIX #2] Bluff Ratio GTO ═══
   bluff_ratio_text = ""
   if villain_bet_pct > 0:
      bluff_ratio_text = get_bluff_ratio(villain_bet_pct)
   
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
   ANÁLISIS RIVER EXPLOTATIVO - NL25 ZOOM

   Si el reasoning no empieza así, corrige y vuelve a intentarlo.

   DATOS TÉCNICOS (NO MODIFICAR, SOLO USAR):
   {tech_summary}

   ⚠️ Debes usar los datos técnicos tal cual aparecen arriba en tu razonamiento. No los inventes ni los modifiques.

   HERO CARDS: {hero_cards}
   BOARD (RIVER): {board}
   CARTA RIVER: {river_card}
   TEXTURA: {context.get('textura_board', 'desconocido')}
   POT PROFILE: {pot_profile.upper()} | SPR={spr if spr is not None else 'N/A'} ({spr_bucket})

   {players_info}

   {population_reads}

   {stack_off_plan}

   {mdf_text}

   {river_advice_text}

   {bluff_ratio_text}

   🎯 CONTEXTO OVERBET:
   {overbet_text}
   {bluffcatch_text if is_overbet_zone else ""}

   🧩 BLOCKER GUIDELINES:
   {blocker_text}

   FORMATO RESPUESTA (JSON ESTRICTO):
   {response_schema}

   REGLAS PARA "defense_pct":
   - Indica qué % de tu rango continúas con la acción propuesta (0-100). Debe ser ≥ {required_defense_pct}% cuando defiendes vs apuesta, salvo razones exploit claras.
   - RESPUESTA ÚNICA EN JSON: termina SIEMPRE con un solo objeto JSON válido que incluya todos los campos del formato anterior (pot_profile, required_defense_pct, defense_pct). No añadas texto extra después del JSON.

   GUÍAS DE ACCIÓN:
   - Elige combinaciones que bloqueen calls (ej. bloquean nut flush o top pair).
   - Añade overcards o removal a straights.
   - Prioriza tamaños POLARIZADOS (70-110% pot) cuando uses flush draws fallidos; una apuesta pequeña no ejerce suficiente presión.
   - Evita bluffear con manos que bloquean folds (ej. tener la carta que quieres que foldee).
   - Multiway: solo value fuerte, bluffs mínimos.

   ⚠️ amount_bb = tamaño total de tu apuesta/raise. to_call_bb = fichas que agregas cuando igualas. pot_fraction = fracción del pot en decimal (1.10 = overbet 110%).
   ⚠️ "defense_pct" = porcentaje de tu rango que continúa con la acción propuesta (0-100). Justifica cuando sea < {required_defense_pct}%.
   """