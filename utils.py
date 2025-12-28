"""Common helpers for postflop prompt builders."""
from __future__ import annotations

from typing import Tuple, Dict, Any

_MDF_PRESETS = (
    (0.33, 0.75, "Vs 33% pot → defiende 75% (check-raises con draws fuertes)"),
    (0.50, 0.67, "Vs 50% pot → defiende 67% (mezcla calls + raises)"),
    (0.66, 0.60, "Vs 66% pot → defiende 60% (polariza rango)"),
    (1.00, 0.50, "Vs 100% pot → MDF 50% (solo manos fuertes + draws premium)"),
    (1.50, 0.40, "Vs 150% pot → MDF 40% (solo top range / bluffcatchers elite)"),
)


def build_mdf_section(current_bet_pct: float) -> Tuple[str, float]:
    """Return formatted MDF cheatsheet and current required defense percentage (0-100)."""
    lines = ["📐 DEFENSA POR SIZING (MDF)"]
    current_required = 0.0

    if current_bet_pct and current_bet_pct > 0:
        current_required = round(100 * (1 / (1 + current_bet_pct)), 1)
    else:
        current_bet_pct = 0.0

    for preset_pct, preset_mdf, note in _MDF_PRESETS:
        marker = "✅" if abs(current_bet_pct - preset_pct) <= 0.05 else "•"
        lines.append(
            f"{marker} {int(preset_pct * 100)}% pot → MDF {int(preset_mdf * 100)}% | {note}"
        )

    if current_required:
        lines.append(
            f"➡️ Bet actual: {round(current_bet_pct * 100, 1)}% pot → Debes defender ~{current_required}% de tu rango"
        )
    else:
        lines.append("➡️ Bet actual desconocido: calcula MDF si el villano apuesta")

    return "\n".join(lines), current_required

def format_players_info(villain_stacks: Dict[str, float], villain_positions: Dict[int, str], hero_stack: float, hero_pos: str, pot: float) -> str:
    """
    Formatea la información de los jugadores en la mesa.
    Combina stacks y posiciones.
    """
    lines = ["👥 INFORMACIÓN DE JUGADORES:"]
    lines.append(f"- HERO ({hero_pos}): {hero_stack}bb")
    
    if not villain_stacks:
        lines.append("- Rivales: (Sin datos detallados)")
    else:
        for seat_key, stack in villain_stacks.items():
            # seat_key like "seat1" -> int 1
            try:
                seat_num = int(seat_key.replace("seat", ""))
                pos = villain_positions.get(seat_num, "Unknown")
            except:
                pos = "Unknown"
            
            lines.append(f"- {seat_key} ({pos}): {stack}bb")
            
    return "\n".join(lines)


def format_available_actions(available_actions: list, is_facing_bet: bool = None) -> str:
    """
    Generates a prompt block indicating which action buttons are available.
    
    Args:
        available_actions: List of action strings ["FOLD", "CALL", "RAISE"] or ["CHECK", "BET"]
        is_facing_bet: Optional explicit facing_bet indicator
        
    Returns:
        Formatted string block for prompt injection, or empty string if no actions
    """
    if not available_actions:
        return ""
    
    actions_str = ", ".join(available_actions)
    
    # Determine context description
    if is_facing_bet is True or set(available_actions) == {"FOLD", "CALL", "RAISE"}:
        context_desc = "Estás enfrentando una apuesta (FACING BET)"
    elif is_facing_bet is False or set(available_actions) == {"CHECK", "BET"}:
        context_desc = "No hay apuesta que enfrentar (NO BET)"
    else:
        context_desc = "Contexto detectado visualmente"
    
    return f"""
⚡ ACCIONES DISPONIBLES (Detectadas visualmente):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 {context_desc}
🎯 Tus opciones: {actions_str}

⚠️ IMPORTANTE: Tu respuesta DEBE ser una de estas acciones: {actions_str}
   NO respondas con una acción que NO esté en esta lista.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

def get_bluff_ratio(bet_size_pct: float) -> str:
    """
    Calcula ratio GTO bluff-to-value según sizing.
    
    Fórmula: α = bet/(pot+bet), ratio = (1-α)/α
    Fuente: TwoPlusTwo GTO Theory
    
    Ejemplo: 50% pot → α=0.33 → ratio=2:1 (2 bluffs por cada value)
    """
    if bet_size_pct <= 0:
        return ""
    alpha = bet_size_pct / (1 + bet_size_pct)
    ratio = (1 - alpha) / alpha if alpha > 0 else 0
    return f"📊 GTO Ratio: 1 value : {ratio:.1f} bluffs"
