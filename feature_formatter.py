from typing import Dict, Any, List

def summarize_engine_features(features: Dict[str, Any]) -> str:
    """
    Convierte el JSON del PokerEngine en un resumen textual para el LLM.
    
    VERSIÓN 2.0 - Usa TODOS los datos disponibles del engine:
    - usesPocketCards (detección robusta de board pairs)
    - overcards (crítico para C-betting)
    - Calidad de draws (Nut vs Weak flush)
    
    Args:
        features: Dict con la salida del engine (hand, draw, relevantHandValue, etc.)
        
    Returns:
        String formateado con el análisis técnico.
    """
    if not features:
        return "⚠️ ANÁLISIS DE MOTOR: No disponible (Error o Timeout)"

    # 1. Hand Value (Mano del Hero)
    hand = features.get('hand', {})
    hand_desc = hand.get('description', 'Unknown')
    hand_type = hand.get('type', 'HighCard')
    
    # 2. Board Hand Value
    board_hand_desc = features.get('boardHand', {}).get('description', 'Unknown')
    
    # 🆕 USAR CAMPO DIRECTO: usesPocketCards
    uses_pocket = features.get('usesPocketCards', True)

    # TRADUCCIÓN HUMANA MEJORADA V2
    if hand_type == 'Pair':
        parts = hand_desc.split()
        if len(parts) >= 2:
            rank = parts[1]
            kickers = ", ".join(parts[2:])
            
            # 🆕 DETECCIÓN ROBUSTA: Usar campo del engine
            if not uses_pocket:
                # El engine confirma que NO usamos nuestras cartas
                hand_desc = f"⚠️ BOARD PAIR of {rank}s (Playing the Board - You DO NOT have trips)\n   Kickers: {kickers}"
            elif rank in board_hand_desc:
                # Fallback por si usesPocketCards no existe (engine viejo)
                hand_desc = f"⚠️ BOARD PAIR of {rank}s (Playing the Board - You DO NOT have trips)"
            else:
                hand_desc = f"Pair of {rank}s (Kickers: {kickers})"
            
    elif hand_type == 'TwoPair':
        parts = hand_desc.split()
        if len(parts) >= 3:
            r1 = parts[1]
            r2 = parts[2]
            hand_desc = f"Two Pair: {r1}s and {r2}s"
    
    # 🆕 3. OVERCARDS (Crítico para C-betting)
    overcards_section = ""
    overcards = features.get('overcards', {})
    oc_type = overcards.get('type')
    
    if oc_type == "TwoOvercards":
        high_card = overcards.get('highCardRank', 'Unknown')
        overcards_section = f"\n- 🎯 OVERCARDS: TWO ({high_card}-high) - Good for C-betting on dry boards"
    elif oc_type == "OneOvercard":
        high_card = overcards.get('highCardRank', 'Unknown')
        overcards_section = f"\n- ⚠️ OVERCARDS: ONE ({high_card}) - Marginal equity"
    elif oc_type == "NoOvercards":
        overcards_section = f"\n- ❌ OVERCARDS: None - Board is higher than your hand"
    
    # 4. Labels (Filtradas - Solo las importantes)
    labels = features.get('relevantHandValue', {}).get('labels', [])
    important_labels = [l for l in labels if any(kw in l.lower() for kw in 
        ['combo draw', 'nut flush', 'two overcards', 'air with', 'bluff catcher', 'monster'])]
    labels_str = ", ".join(important_labels) if important_labels else "Sin etiquetas críticas"

    # 🆕 5. Draws (CON CALIDAD)
    draws = []
    draw_data = features.get('draw', {})
    
    # FLUSH DRAWS - Distinguir calidad
    if draw_data.get('isNutsHighFlushDraw'):
        draws.append("🔥 NUT Flush Draw")
    elif draw_data.get('isFourthOrLowerNutsHighFlushDraw'):
        draws.append("⚠️ WEAK Flush Draw (4th Nut or lower)")
    elif draw_data.get('isFlushDraw'):
        draws.append("Flush Draw")
    
    # STRAIGHT DRAWS
    if draw_data.get('isStraightDraw'):
        draws.append("Straight Draw (Open-Ended)")
    if draw_data.get('isGutshot'):
        draws.append("Gutshot (Inside Straight)")
    
    # BACKDOORS
    if draw_data.get('isTwoPocketsBackdoor'):
        draws.append("Backdoor Flush (2 pocket cards)")
    if draw_data.get('isAceHighBackdoor'):
        draws.append("Backdoor Nut Flush")
    
    draws_str = ", ".join(draws) if draws else "Ninguno"
    
    # 6. Outs
    outs_info = ""
    f_outs = draw_data.get('flushOutsCount', 0)
    s_outs = draw_data.get('straightOutsCount', 0)
    if f_outs > 0 or s_outs > 0:
        outs_info = f" | Outs: Flush={f_outs}, Straight={s_outs}"

    return f"""
🔍 ANÁLISIS TÉCNICO (POKER ENGINE):
- Mano Hero: {hand_desc}
- Mano Board: {board_hand_desc}{overcards_section}
- Etiquetas: {labels_str}
- Proyectos: {draws_str}{outs_info}
- Street: {features.get('street', 'Unknown')}
"""