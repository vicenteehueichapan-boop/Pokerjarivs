import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

class PreflopRangeManager:
    """
    Gestor de rangos preflop.
    Selecciona la tabla correcta basada en la situación (RFI, vs Open, vs 3Bet)
    y extrae la instrucción estratégica para la mano específica.
    """
    
    def __init__(self, ranges_dir: str = "config/preflop_ranges/preflop_ranges"):
        self.ranges_dir = Path(ranges_dir)
        # Cache para no recargar archivos constantemente
        self.cache: Dict[str, Dict] = {}

    def _load_json(self, filename: str) -> Dict:
        if filename in self.cache:
            return self.cache[filename]
        
        path = self.ranges_dir / filename
        if not path.exists():
            print(f"Rango no encontrado: {filename}")
            return {}
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.cache[filename] = data
                return data
        except Exception as e:
            print(f"Error leyendo rango {filename}: {e}")
            return {}

    def _normalize_hand(self, cards: list) -> str:
        """Convierte ['Ah', 'Kd'] -> 'AKO' o ['Th', 'Th'] -> 'TT'"""
        if not cards or len(cards) != 2:
            return ""
            
        r1, s1 = cards[0][:-1], cards[0][-1]
        r2, s2 = cards[1][:-1], cards[1][-1]
        
        # Ordenar por rango (A > K > ... > 2)
        ranks = "AKQJT98765432"
        if ranks.index(r1) > ranks.index(r2):
            r1, r2 = r2, r1
            s1, s2 = s2, s1
            
        if r1 == r2:
            return f"{r1}{r2}"
        elif s1 == s2:
            return f"{r1}{r2}S"
        else:
            return f"{r1}{r2}O"

    def get_range_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determina el archivo correcto y extrae datos de la mano.
        """
        hero_pos = context.get('hero_position', 'BTN')
        hero_cards = context.get('hero_cards', [])
        pot = context.get('pot', 1.5)
        villain_pos = "Unknown" # Debería venir del contexto si enfrentamos raise
        
        # Lógica simplificada de selección de archivo (se puede expandir)
        # 1. Detectar escenario
        scenario = "RFI"
        filename = ""
        
        # Si pot es pequeño (ciegas) -> RFI
        if pot <= 1.5:
            scenario = "RFI"
            # Default sizing 2.5bb para la mayoría, 2.2bb para BU
            sizing = "2.2" if hero_pos == "BU" or hero_pos == "BTN" else "2.5"
            # Ajuste nombre posicion
            pos_map = {"BTN": "BU", "SB": "SB", "BB": "BB", "CO": "CO", "HJ": "HJ", "UTG": "UTG"}
            file_pos = pos_map.get(hero_pos, "BU")
            filename = f"RFI_6max_{file_pos}_{sizing}.json"
            
        # Si pot indica Raise previo (2bb - 5bb) -> Facing Open (FOR)
        elif pot > 1.5 and pot < 6:
            scenario = "FOR"
            # Necesitamos saber QUIÉN abrió. Por ahora simulamos vs UTG o CO para fallbacks
            # Idealmente context debe traer 'aggressor_position'
            villain_pos = context.get('aggressor_position', 'UTG')
            filename = f"FOR_6max_{hero_pos}_vs_{villain_pos}_2.5.json"
            
        # Si pot indica 3Bet (> 7bb) -> Facing 3Bet (F3B)
        elif pot >= 6:
            scenario = "F3B"
            villain_pos = context.get('aggressor_position', 'SB') # Simulacion
            filename = f"F3B_6max_{hero_pos}_vs_{villain_pos}.json" # Nombre aprox

        # 2. Cargar datos
        range_data = self._load_json(filename)
        if not range_data:
            # Fallback a RFI BTN si falla para no devolver vacío
            range_data = self._load_json("RFI_6max_BU_2.2.json")
            filename += " (Fallback)"

        # 3. Buscar mano
        hand_key = self._normalize_hand(hero_cards)
        hand_info = range_data.get(hand_key, {})
        
        return {
            "scenario": scenario,
            "chart_file": filename,
            "hand_key": hand_key,
            "instruction": hand_info.get("instruction", "Juega estándar según fuerza de mano."),
            "actions": {k: v for k, v in hand_info.items() if k != "instruction"}
        }

