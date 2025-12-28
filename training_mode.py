"""
Training Mode Configuration
===========================

Configuración especial para modo de entrenamiento/testing.

Diferencias vs Producción:
1. ✅ Caché DESACTIVADO (siempre consulta API)
2. ✅ Exploración activada (variaciones en decisiones)
3. ✅ Logging exhaustivo
4. ✅ Guarda TODAS las decisiones (no solo únicas)
"""

from typing import Dict, Any, Optional
from backend.decision_engine.core import DecisionEngine


class TrainingDecisionEngine(DecisionEngine):
    """
    Decision Engine modificado para re-entrenamiento.
    
    Características:
    - Sin caché (siempre toma decisiones frescas)
    - Logging exhaustivo
    - Permite evaluar múltiples veces el mismo spot
    """
    
    def __init__(self, exploration_rate: float = 0.0):
        """
        Args:
            exploration_rate: 0.0 = siempre usa decisión del modelo
                              0.1 = 10% de las veces explora alternativas
                              (útil para generar datos variados)
        """
        # Inicializar SIN caché
        super().__init__(use_cache=False)
        self.exploration_rate = exploration_rate
        self.decision_count = 0
        self.spot_history = {}  # Registra cuántas veces vio cada spot
    
    def make_decision(self, mesa_data: Dict, mesa_id: int = 1, extra_context: str = "") -> Dict:
        """
        Toma decisión sin usar caché.
        
        SIEMPRE consulta la API, incluso si ya vio este spot antes.
        """
        self.decision_count += 1
        
        # Generar key del spot para estadísticas
        spot_key = self._generate_spot_key(mesa_data, extra_context)
        
        if spot_key not in self.spot_history:
            self.spot_history[spot_key] = {'count': 0, 'decisions': []}
        
        self.spot_history[spot_key]['count'] += 1
        
        print(f"\n{'='*70}")
        print(f"TRAINING MODE - Decisión #{self.decision_count}")
        print(f"Spot visto: {self.spot_history[spot_key]['count']} veces")
        print(f"{'='*70}")
        
        # Llamar al engine SIN caché (ya desactivado en __init__)
        decision = super().make_decision(mesa_data, mesa_id, extra_context)
        
        # Registrar decisión para este spot
        self.spot_history[spot_key]['decisions'].append(decision.get('decision'))
        
        # Mostrar variación si hay
        if self.spot_history[spot_key]['count'] > 1:
            prev_decisions = self.spot_history[spot_key]['decisions']
            unique_decisions = set(prev_decisions)
            
            if len(unique_decisions) > 1:
                print(f"⚠️  VARIACIÓN DETECTADA en este spot:")
                print(f"   Decisiones anteriores: {prev_decisions[:-1]}")
                print(f"   Decisión actual: {prev_decisions[-1]}")
            else:
                print(f"ℹ️  Decisión consistente: {prev_decisions[0]}")
        
        return decision
    
    def _generate_spot_key(self, mesa_data: Dict, history: str) -> str:
        """Genera key única para identificar spots idénticos"""
        import hashlib
        
        key_elements = [
            str(sorted(mesa_data.get('hero_cards', []))),
            str(sorted(mesa_data.get('community_cards', []))),
            str(mesa_data.get('pot', 0)),
            str(mesa_data.get('stack', 0)),
            history[:100]  # Solo primeros 100 chars del historial
        ]
        
        key_str = "|".join(key_elements)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get_training_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del entrenamiento.
        
        Returns:
            {
                'total_decisions': int,
                'unique_spots': int,
                'repeated_spots': int,
                'variation_rate': float  # % de spots con decisiones diferentes
            }
        """
        unique_spots = len(self.spot_history)
        repeated_spots = sum(1 for spot in self.spot_history.values() if spot['count'] > 1)
        
        # Calcular variation rate
        spots_with_variation = 0
        for spot_data in self.spot_history.values():
            if len(set(spot_data['decisions'])) > 1:
                spots_with_variation += 1
        
        variation_rate = spots_with_variation / unique_spots if unique_spots > 0 else 0.0
        
        return {
            'total_decisions': self.decision_count,
            'unique_spots': unique_spots,
            'repeated_spots': repeated_spots,
            'variation_rate': variation_rate,
            'spots_detail': self.spot_history
        }


def compare_decisions_over_time(spot_key: str, decisions: list) -> Dict:
    """
    Analiza si las decisiones mejoran con el tiempo.
    
    Args:
        spot_key: Identificador del spot
        decisions: Lista de decisiones en orden cronológico
    
    Returns:
        {
            'consistent': bool,  # ¿Siempre la misma decisión?
            'improved': bool,    # ¿Mejoró con el tiempo? (requiere evaluación externa)
            'variation': str     # Descripción de la variación
        }
    """
    unique = set(decisions)
    
    if len(unique) == 1:
        return {
            'consistent': True,
            'improved': None,  # No se puede determinar sin benchmark
            'variation': f"Siempre {decisions[0]}"
        }
    
    return {
        'consistent': False,
        'improved': None,  # Requiere evaluación con GTO solver
        'variation': f"Varió entre: {', '.join(unique)}"
    }

