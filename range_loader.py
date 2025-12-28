import json
import logging
import random
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class RangeLoader:
    """
    Cargador de rangos preflop con fallback jerárquico.
    Soporta estrategia mixta (probabilidades).
    """
    
    def __init__(self, range_dir="config/preflop_ranges/preflop_ranges"):
        self.range_dir = Path(range_dir)
        self.cache = {}  # Caché de rangos cargados
        self.fallback_used = {}  # Tracking de fallbacks
        
        if not self.range_dir.exists():
            logger.error(f"❌ Directorio de rangos no encontrado: {self.range_dir}")
    
    def load_range(self, range_type: str, position: str, facing: str = "Open", raise_size: float = 2.5) -> Optional[Dict]:
        """
        Carga un rango con sistema de fallback jerárquico.
        
        Args:
            range_type: "RFI", "FOR", "F3B"
            position: "UTG", "HJ", "CO", "BTN"/"BU", "SB", "BB"
            facing: "Open" para RFI, o posición del agresor para FOR/F3B
            raise_size: Tamaño del raise (2.5bb, 3.0bb, etc.)
        
        Returns:
            Dict con el rango cargado, o None si falla todo
        
        Jerarquía de Fallback:
        1. Archivo exacto (ej. FOR_6max_BB_vs_UTG_2.5.json)
        2. Tamaño de raise alternativo (2.5 → 3.0)
        3. Posición genérica similar (CO → BTN)
        4. Rango conservador por defecto
        """
        
        # Normalizar nombres de posiciones
        position = self._normalize_position(position)
        facing = self._normalize_position(facing) if facing != "Open" else facing
        
        # Clave de caché
        cache_key = f"{range_type}_{position}_{facing}_{raise_size}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # NIVEL 1: Intentar cargar archivo exacto
        range_data = self._try_load_exact(range_type, position, facing, raise_size)
        if range_data:
            self.cache[cache_key] = range_data
            logger.info(f"✅ Rango cargado: {range_type}_{position}_vs_{facing}_{raise_size}")
            return range_data
        
        # NIVEL 2: Intentar con raise_size alternativo
        logger.warning(f"⚠️ Rango exacto no encontrado: {cache_key}")
        range_data = self._try_alternative_size(range_type, position, facing, raise_size)
        if range_data:
            self.cache[cache_key] = range_data
            self.fallback_used[cache_key] = "alternative_size"
            return range_data
        
        # NIVEL 3: Intentar posición similar
        range_data = self._try_similar_position(range_type, position, facing, raise_size)
        if range_data:
            self.cache[cache_key] = range_data
            self.fallback_used[cache_key] = "similar_position"
            return range_data
        
        # NIVEL 4: Fallback conservador
        logger.error(f"🚨 FALLBACK CRÍTICO: Usando rango conservador para {cache_key}")
        range_data = self._get_conservative_default(range_type, position, facing)
        self.fallback_used[cache_key] = "conservative_default"
        return range_data
    
    def _normalize_position(self, pos: str) -> str:
        """Normaliza nombres de posiciones"""
        pos = pos.upper()
        if pos in ["BTN", "BUTTON", "BU"]:
            return "BTN"
        return pos
    
    def _try_load_exact(self, range_type: str, position: str, facing: str, raise_size: float) -> Optional[Dict]:
        """Intenta cargar el archivo exacto"""
        filename = f"{range_type}_6max_{position}_vs_{facing}_{raise_size}.json"
        
        # Si es RFI, el formato es diferente
        if range_type == "RFI":
            filename = f"RFI_6max_{position}_{raise_size}.json"
        
        filepath = self.range_dir / filename
        
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON corrupto: {filename} - {e}")
            return None
    
    def _try_alternative_size(self, range_type: str, position: str, facing: str, raise_size: float) -> Optional[Dict]:
        """Intenta con tamaños de raise alternativos"""
        alternative_sizes = [2.5, 3.0, 2.2, 8.5, 9.0]
        
        for alt_size in alternative_sizes:
            if alt_size == raise_size:
                continue
            
            range_data = self._try_load_exact(range_type, position, facing, alt_size)
            if range_data:
                logger.warning(f"🔄 Usando raise_size alternativo: {alt_size} en lugar de {raise_size}")
                return range_data
        
        return None
    
    def _try_similar_position(self, range_type: str, position: str, facing: str, raise_size: float) -> Optional[Dict]:
        """Intenta con posiciones similares"""
        
        # Mapeo de posiciones similares (de más tight a más loose)
        similar_positions = {
            "CO": ["BTN"],  # CO puede usar rangos de BTN (más loose)
            "HJ": ["CO", "BTN"],
            "UTG": ["HJ"],
            "BB": [],  # BB es único
            "SB": [],  # SB es único
        }
        
        if position not in similar_positions:
            return None
        
        for similar_pos in similar_positions[position]:
            range_data = self._try_load_exact(range_type, similar_pos, facing, raise_size)
            if range_data:
                logger.warning(f"🔄 Usando posición similar: {similar_pos} en lugar de {position}")
                return range_data
        
        return None
    
    def _get_conservative_default(self, range_type: str, position: str, facing: str) -> Dict:
        """
        Rangos conservadores por defecto (para no tomar decisiones locas).
        
        Filosofía: Es mejor ser muy tight que muy loose.
        Formato: Probabilidades para estrategia mixta.
        """
        
        # PREMIUMS UNIVERSALES
        premiums = {
            "AA": {"Raise": 1.0, "Call": 0.0, "Fold": 0.0},
            "KK": {"Raise": 1.0, "Call": 0.0, "Fold": 0.0},
            "QQ": {"Raise": 1.0, "Call": 0.0, "Fold": 0.0},
            "JJ": {"Raise": 1.0, "Call": 0.0, "Fold": 0.0},
            "AKS": {"Raise": 1.0, "Call": 0.0, "Fold": 0.0},
            "AKO": {"Raise": 1.0, "Call": 0.0, "Fold": 0.0},
        }
        
        # Añadir manos adicionales según posición y acción
        if range_type == "RFI":
            # Raise First In: Solo premiums en early, más amplio en late
            if position in ["BTN", "CO"]:
                premiums.update({
                    "TT": {"Raise": 1.0, "Call": 0.0, "Fold": 0.0},
                    "99": {"Raise": 1.0, "Call": 0.0, "Fold": 0.0},
                    "AQS": {"Raise": 1.0, "Call": 0.0, "Fold": 0.0},
                    "AQO": {"Raise": 1.0, "Call": 0.0, "Fold": 0.0},
                    "AJS": {"Raise": 1.0, "Call": 0.0, "Fold": 0.0},
                    "KQS": {"Raise": 1.0, "Call": 0.0, "Fold": 0.0},
                })
        
        elif range_type == "FOR":
            # Flat Open Raise: Defender con premiums y pairs para set mining
            premiums.update({
                "TT": {"Raise": 0.2, "Call": 0.8, "Fold": 0.0},
                "99": {"Raise": 0.0, "Call": 1.0, "Fold": 0.0},
                "88": {"Raise": 0.0, "Call": 1.0, "Fold": 0.0},
                "77": {"Raise": 0.0, "Call": 1.0, "Fold": 0.0},
                "AQS": {"Raise": 0.5, "Call": 0.5, "Fold": 0.0},
                "AJS": {"Raise": 0.0, "Call": 1.0, "Fold": 0.0},
            })
        
        elif range_type == "F3B":
            # Fold vs 3-Bet: Solo continuar con monsters
            # Ya tenemos AA, KK, QQ, JJ, AK
            premiums = {
                "AA": {"Raise": 0.8, "Call": 0.2, "Fold": 0.0},  # 4-bet o call
                "KK": {"Raise": 0.8, "Call": 0.2, "Fold": 0.0},
                "QQ": {"Raise": 0.2, "Call": 0.7, "Fold": 0.1},  # Mayormente call
                "AKS": {"Raise": 0.5, "Call": 0.5, "Fold": 0.0},
                "AKO": {"Raise": 0.3, "Call": 0.6, "Fold": 0.1},
            }
        
        logger.warning(f"⚠️ FALLBACK: Usando rango ultra-conservador ({len(premiums)} combos)")
        
        return {
            "_meta": {
                "fallback": True,
                "type": range_type,
                "position": position,
                "facing": facing,
                "note": "⚠️ RANGO CONSERVADOR POR DEFECTO - Archivo no encontrado"
            },
            **premiums
        }
    
    def get_action_for_hand(self, range_data: Dict, hero_cards: list) -> Tuple[str, float, str]:
        """
        Determina la acción para una mano específica según el rango.
        
        Args:
            range_data: Diccionario del rango cargado
            hero_cards: ['Ah', 'Kd'] formato de cartas
        
        Returns:
            Tuple: (acción, confianza, reasoning)
            - acción: "RAISE", "CALL", "FOLD"
            - confianza: probabilidad de la acción elegida (0.0-1.0)
            - reasoning: explicación de la decisión
        """
        
        # Convertir hero_cards a notación de rango
        hand_notation = self._convert_to_notation(hero_cards)
        
        # Buscar la mano en el rango
        if hand_notation not in range_data:
            # Mano no está en el rango → Fold
            is_fallback = range_data.get("_meta", {}).get("fallback", False)
            
            if is_fallback:
                reasoning = f"⚠️ Mano {hand_notation} no está en rango FALLBACK conservador → FOLD por seguridad"
            else:
                reasoning = f"Mano {hand_notation} no está en rango estándar → FOLD"
            
            return "FOLD", 1.0, reasoning
        
        # Obtener probabilidades de la mano
        hand_probs = range_data[hand_notation]
        
        # Estrategia mixta: Elegir acción basada en probabilidades
        actions = ["Raise", "Call", "Fold"]
        probs = [
            hand_probs.get("Raise", 0.0),
            hand_probs.get("Call", 0.0),
            hand_probs.get("Fold", 0.0)
        ]
        
        # Elegir acción según probabilidades (estrategia GTO)
        chosen_action_idx = random.choices(range(len(actions)), weights=probs)[0]
        chosen_action = actions[chosen_action_idx].upper()
        confidence = probs[chosen_action_idx]
        
        # Construir reasoning
        instruction = hand_probs.get("instruction", "Sin instrucción")
        
        reasoning = f"Mano {hand_notation}: {instruction}\n"
        reasoning += f"Probabilidades GTO: Raise={probs[0]:.1%}, Call={probs[1]:.1%}, Fold={probs[2]:.1%}\n"
        reasoning += f"Acción elegida (mixed strategy): {chosen_action} (conf: {confidence:.1%})"
        
        return chosen_action, confidence, reasoning
    
    def _convert_to_notation(self, hero_cards: list) -> str:
        """
        Convierte ['Ah', 'Kd'] a 'AKO' o 'AKS'
        
        Args:
            hero_cards: Lista de 2 cartas en formato ['Ah', 'Kd']
        
        Returns:
            String: 'AKS', 'AKO', 'AA', etc.
        """
        if len(hero_cards) != 2:
            raise ValueError(f"Se esperan 2 cartas, se recibieron {len(hero_cards)}")
        
        # Extraer ranks y suits
        rank1, suit1 = hero_cards[0][0], hero_cards[0][1]
        rank2, suit2 = hero_cards[1][0], hero_cards[1][1]
        
        # Normalizar T para 10
        rank1 = 'T' if rank1 == '1' else rank1
        rank2 = 'T' if rank2 == '1' else rank2
        
        # Orden de ranks (de mayor a menor)
        rank_order = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        
        # Caso 1: Par (Pocket Pair)
        if rank1 == rank2:
            return f"{rank1}{rank2}"
        
        # Caso 2: Suited vs Offsuit
        # Ordenar ranks (más alto primero)
        if rank_order.index(rank1) < rank_order.index(rank2):
            high_rank, low_rank = rank1, rank2
        else:
            high_rank, low_rank = rank2, rank1
        
        # Suited o Offsuit
        suited = 'S' if suit1 == suit2 else 'O'
        
        return f"{high_rank}{low_rank}{suited}"
    
    def get_fallback_report(self) -> str:
        """Genera reporte de cuántas veces se usó el fallback"""
        if not self.fallback_used:
            return "✅ No se usó ningún fallback (todos los rangos encontrados)"
        
        report = "⚠️ FALLBACKS UTILIZADOS:\n"
        for key, fallback_type in self.fallback_used.items():
            report += f"   - {key} → {fallback_type}\n"
        
        report += f"\nTotal de fallbacks: {len(self.fallback_used)}"
        return report
    
    def validate_range_coverage(self, range_data: Dict) -> Dict:
        """
        Valida la cobertura de un rango (cuántas manos tiene).
        
        Returns:
            Dict con estadísticas del rango
        """
        total_hands = 0
        action_counts = {"Raise": 0, "Call": 0, "Fold": 0, "Mixed": 0}
        
        for hand, probs in range_data.items():
            if hand.startswith("_"):  # Skip metadata
                continue
            
            total_hands += 1
            
            # Determinar acción predominante
            raise_prob = probs.get("Raise", 0.0)
            call_prob = probs.get("Call", 0.0)
            fold_prob = probs.get("Fold", 0.0)
            
            max_prob = max(raise_prob, call_prob, fold_prob)
            
            if max_prob == raise_prob and raise_prob > 0.7:
                action_counts["Raise"] += 1
            elif max_prob == call_prob and call_prob > 0.7:
                action_counts["Call"] += 1
            elif max_prob == fold_prob and fold_prob > 0.7:
                action_counts["Fold"] += 1
            else:
                action_counts["Mixed"] += 1
        
        return {
            "total_hands": total_hands,
            "action_breakdown": action_counts,
            "is_tight": total_hands < 50,
            "is_loose": total_hands > 150
        }

