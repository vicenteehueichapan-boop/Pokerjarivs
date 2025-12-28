from typing import Dict, Any

def get_pot_profile(pot: float, rivals: int, street: str = 'Flop') -> str:
    """
    Deduce el tipo de bote (SRP, 3BP, 4BP) basado en tamaño del pot y la calle actual.
    Se ajusta porque los botes SRP crecen naturalmente postflop.
    """
    # Umbrales dinámicos
    threshold_3bet = 10.0
    st = street.lower()
    
    if st == 'preflop':
        threshold_3bet = 6.0
    elif st == 'flop':
        threshold_3bet = 12.0 
    elif st in ['turn', 'river']:
        threshold_3bet = 25.0 # En river, un SRP puede tener 20-25bb

    if pot < threshold_3bet:
        return "srp"
    elif pot < (threshold_3bet * 4): # Rango amplio
        return "3bet"
    else:
        return "4bet"

def get_spr_bucket(spr: float) -> str:
    if spr is None: return "unknown"
    if spr > 13: return "deep"
    if spr > 6: return "medium"
    if spr > 3: return "low"
    return "critical"

def get_spot_guidance(context: Dict[str, Any]) -> str:
    """
    Genera consejos estratégicos específicos basados en el contexto.
    """
    guidance = []
    
    # 1. Datos clave
    pot = context.get('pot', 0)
    stack = context.get('stack', 0)
    position = context.get('hero_position', 'Unknown')
    rivals = context.get('rivals', 1)
    street = context.get('street', 'Flop') # Obtener street del contexto
    
    spr = stack / pot if pot > 0 else 10
    
    # 2. Detectar perfil con street correcta
    profile = get_pot_profile(pot, rivals, street)
    
    oop_positions = {'BB', 'SB'}
    is_oop = position in oop_positions
    
    # 3. Generar consejos
    if profile == "3bet":
        guidance.append("🚨 3-BET POT DETECTADO:")
        if is_oop:
            guidance.append("- Estás OOP en bote grande. SPR bajo reduce maniobrabilidad.")
            guidance.append("- Check-shove es potente con Top Pair+ o Draws fuertes.")
        else:
            guidance.append("- Tienes posición (IP). Presiona con apuestas pequeñas (33%) para negar equity.")
    
    elif profile == "srp":
        guidance.append("ℹ️ SINGLE RAISED POT (SRP):")
        if is_oop:
            guidance.append("- OOP: Check-raise selectivo. No regales fichas con manos medias.")
        else:
            guidance.append("- IP: C-bet frecuente en boards secos. Pot control con manos medias.")
            
    if rivals >= 2:
        guidance.append("\n⚠️ MULTIWAY POT (>2 jugadores):")
        guidance.append("- Juega HONESTO. Bluffea casi cero.")
        guidance.append("- Si apuestan, asume fuerza real.")

    if spr < 1:
        guidance.append("\n⚡ SPR CRÍTICO (<1):")
        guidance.append("- Estás commited. Cualquier Top Pair o Draw decente es All-In.")
    
    return "\n".join(guidance)