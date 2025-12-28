"""
Decision Core V3 - Con Soporte de Memoria y Caché Contextual
============================================================
Integra:
1. Prompts Modulares
2. Caché Inteligente
3. Memoria de Fases (Extra Context)
4. API de DeepSeek
5. Poker Engine (C#) para análisis técnico
"""

import time
from typing import Dict, Optional
from backend.decision_engine.cache import DecisionCache
from backend.decision_engine.api_client import DeepSeekAPIManager
from backend.decision_engine.validator import validate_mesa_data
from backend.core.street_detector import detect_street
from backend.decision_engine.parser import parse_deepseek_response
from backend.decision_engine.prompts.manager import get_prompt_for_street
from backend.decision_engine.engine_client import PokerEngineClient
from backend.decision_engine.board_analyzer import BoardAnalyzer

class DecisionEngine:
    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        self.cache = DecisionCache() if use_cache else None
        self.api_manager = DeepSeekAPIManager()
        self.engine_client = PokerEngineClient()
        
        if not self.api_manager.has_clients():
            print("⚠️ ADVERTENCIA: No hay API Keys configuradas.")

    def make_decision(self, mesa_data: Dict, mesa_id: int = 1, extra_context: str = "") -> Dict:
        """
        Toma una decisión basada en estado actual + historia previa.
        """
        start_time = time.time()
        
        # 1. Validación
        if not validate_mesa_data(mesa_data):
            return self._error_response("Datos insuficientes")

        # 2. Detectar Calle
        street = detect_street(mesa_data.get('community_cards', []))
        mesa_data['street'] = street

        # 2.5 ENRIQUECIMIENTO: Poker Engine (C#)
        # Solo llamamos si tenemos cartas propias
        if mesa_data.get('hero_cards'):
            print(f"Calculando features con PokerEngine (Mesa {mesa_id})...")
            features = self.engine_client.compute_features(
                game="texas_holdem",
                pockets=mesa_data['hero_cards'],
                board=mesa_data.get('community_cards', [])
            )
            mesa_data['engine_features'] = features
            if features:
                print(f"   Engine: {features.get('hand', {}).get('description')}")
            else:
                print("   Engine: Sin respuesta")

        # 2.6 ENRIQUECIMIENTO: Board Texture (Python)
        if mesa_data.get('community_cards'):
            texture = BoardAnalyzer.analyze_texture(mesa_data['community_cards'])
            mesa_data['textura_board'] = texture
            print(f"   Board Texture: {texture}")
        else:
             mesa_data['textura_board'] = "Preflop"

        # 3. Caché (Con Contexto Histórico)
        if self.use_cache:
            # La clave del caché ahora depende también de la historia
            cached_decision = self.cache.get(mesa_data, history_str=extra_context)
            if cached_decision:
                print(f"CACHE HIT (Mesa {mesa_id})")
                return cached_decision

        # 4. Construir Prompt
        try:
            base_prompt = get_prompt_for_street(street, mesa_data)
            
            # INYECCIÓN DE MEMORIA
            final_prompt = base_prompt
            if extra_context:
                final_prompt = (
                    f"=== HISTORIAL DE LA MANO (MEMORIA) ===\n"
                    f"{extra_context}\n"
                    f"=========================================\n\n"
                    f"{base_prompt}"
                )
            
            # DEBUG: Guardar prompt en archivo para verificación (Por calle)
            try:
                filename = f"prompt_{street}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(final_prompt)
                print(f"\nPrompt {street} guardado en '{filename}' para revisión.\n")
            except Exception as e:
                print(f"No se pudo guardar el prompt: {e}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            return self._error_response(f"Error prompt: {str(e)}")

        # 5. API DeepSeek
        client = self.api_manager.get_client(mesa_id)
        if not client:
            print(f"❌ [Mesa {mesa_id}] NO HAY CLIENTE API - Sin API key configurada")
            return self._error_response("Sin cliente API")

        try:
            print(f"🚀 [Mesa {mesa_id}] LLAMANDO A DEEPSEEK API...")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Eres un asistente experto en Poker. Responde SIEMPRE en formato JSON estricto."},
                    {"role": "user", "content": final_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            raw_content = response.choices[0].message.content
            print(f"✅ [Mesa {mesa_id}] DEEPSEEK RESPONDIÓ: {raw_content[:100]}...")
        except Exception as e:
            print(f"Error API: {e}")
            return self._error_response("Error de conexión")

        # 6. Parsear
        decision_data = parse_deepseek_response(raw_content)
        
        # 7. Guardar Caché
        if self.use_cache and decision_data.get('confidence') == 'HIGH':
            self.cache.set(mesa_data, decision_data, history_str=extra_context)

        return decision_data

    def _error_response(self, reason: str) -> Dict:
        return {
            'decision': 'FOLD',
            'confidence': 'LOW',
            'reasoning': f"ERROR: {reason}",
            'decision_final': 'Fold seguro',
            'size_bb': 0,
            'timestamp': time.time()
        }