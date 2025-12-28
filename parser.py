"""
Parser robusto para respuestas de DeepSeek con JSON anidado.
Versión: 2.1
Fecha: 2024-11-22
Autor: Sistema Automatizado

CHANGELOG:
- v2.1: Fix de compatibilidad en adaptador (campo 'accion')
- v2.0: Agregado soporte para JSON anidado con contador de llaves
- v2.0: Agregado extractor de markdown blocks
- v2.0: Agregado sistema de cascada de métodos
- v2.0: Agregado logging detallado
- v2.0: Agregado validación robusta
"""

import json
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ResponseParser:
    """Parser de respuestas con múltiples estrategias de extracción."""
    
    def __init__(self):
        self.extraction_methods = [
            self._extract_from_markdown_block,
            self._extract_balanced_json,
            self._extract_simple_json,
            self._parse_as_text
        ]
    
    def parse(self, content: str) -> Dict[str, Any]:
        """
        Parsea respuesta de DeepSeek intentando múltiples métodos.
        
        Args:
            content: Texto completo de la respuesta
            
        Returns:
            Diccionario con la decisión parseada
            
        Raises:
            ValueError: Si ningún método de parsing funciona
        """
        if not content or not content.strip():
            return self._create_default_response("FOLD", "Content vacío")
        
        logger.info(f"Parseando respuesta ({len(content)} chars)")
        
        # Intentar cada método en orden de prioridad
        for method in self.extraction_methods:
            try:
                result = method(content)
                if result:
                    logger.info(f"✅ Parsing exitoso con: {method.__name__}")
                    return self._validate_and_normalize(result)
            except Exception as e:
                logger.debug(f"⚠️ {method.__name__} falló: {e}")
                continue
        
        # Si todo falla, intentar fallback de emergencia
        logger.warning("⚠️ Todos los métodos fallaron, retornando FOLD default")
        return self._create_default_response("FOLD", "Error de parsing total")
    
    def _create_default_response(self, action: str, reason: str) -> Dict[str, Any]:
        return {
            'accion': action.lower(),
            'decision': action.upper(),
            'confidence': 0.3,  # LOW = 0.3
            'reasoning': reason,
            'amount_bb': 0.0,
            'raw_json': {}
        }

    # ========================================================================
    # MÉTODO 1: MARKDOWN CODE BLOCK (PRIORIDAD ALTA)
    # ========================================================================
    
    def _extract_from_markdown_block(self, content: str) -> Optional[Dict]:
        """
        Extrae JSON de bloques markdown ```json ... ```
        """
        patterns = [
            r'```json\s*\n?(.*?)\n?```',
            r'```\s*\n?(.*?)\n?```',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                json_str = match.group(1).strip()
                json_str = re.sub(r'//.*', '', json_str)
                return json.loads(json_str)
        
        return None
    
    # ========================================================================
    # MÉTODO 2: BALANCED JSON EXTRACTION (PRIORIDAD MEDIA)
    # ========================================================================
    
    def _extract_balanced_json(self, content: str) -> Optional[Dict]:
        """
        Extrae JSON balanceado manejando anidamiento.
        Usa un contador de llaves para encontrar el JSON más externo completo.
        """
        start_idx = content.find('{')
        if start_idx == -1:
            return None
        
        brace_count = 0
        in_string = False
        escape_next = False
        
        for i in range(start_idx, len(content)):
            char = content[i]
            
            if char == '"' and not escape_next:
                in_string = not in_string
            elif char == '\\' and not escape_next:
                escape_next = True
                continue
            
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    
                    if brace_count == 0:
                        json_str = content[start_idx:i+1]
                        json_str = re.sub(r'//.*', '', json_str)
                        return json.loads(json_str)
            
            escape_next = False
        
        return None
    
    # ========================================================================
    # MÉTODO 3: SIMPLE JSON (FALLBACK)
    # ========================================================================
    
    def _extract_simple_json(self, content: str) -> Optional[Dict]:
        """
        Intenta extraer JSON simple (sin anidamiento garantizado).
        """
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        
        return None
    
    # ========================================================================
    # MÉTODO 4: TEXT PARSING (ÚLTIMO RECURSO)
    # ========================================================================
    
    def _parse_as_text(self, content: str) -> Optional[Dict]:
        """
        Fallback: busca palabras clave en texto plano.
        """
        logger.warning("⚠️ Usando text parsing (JSON no encontrado)")
        
        content_upper = content.upper()
        
        # Mapeo de keywords a acciones estandarizadas
        action_keywords = {
            'FOLD': 'fold',
            'CHECK': 'check',
            'CALL': 'call',
            'BET': 'bet',
            'RAISE': 'raise',
            'ALL-IN': 'allin',
            'SHOVE': 'allin'
        }
        
        # Buscar la primera keyword que aparezca
        for keyword, action in action_keywords.items():
            if keyword in content_upper:
                # ═══ FIX: No incluir contenido crudo que puede tener JSON ═══
                # Generar reasoning limpio y legible para la memoria
                clean_reasoning = f"Acción {action.upper()} detectada por text parsing (respuesta no-JSON)"
                return {
                    'accion': action,
                    'confidence': 'low',
                    'reasoning': clean_reasoning,
                    'decision_final': f"{action.upper()} (fallback)"
                }
        
        return None
    
    # ========================================================================
    # VALIDACIÓN Y NORMALIZACIÓN
    # ========================================================================
    
    def _validate_and_normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida que el JSON parseado tenga campos mínimos requeridos.
        """
        if 'accion' in data:
            data['accion'] = data['accion'].lower().strip()
        elif 'decision' in data:
            data['accion'] = data['decision'].lower().strip()
        else:
            # Si no hay accion, intentar inferir
            return self._create_default_response("FOLD", "JSON sin campo accion")
        
        # Normalizar campos en español a inglés interno
        if 'razonamiento' in data and 'reasoning' not in data:
            data['reasoning'] = data['razonamiento']

        defaults = {
            'amount_bb': 0.0,
            'confidence': 0.5,  # medium = 0.5
            'reasoning': 'No proporcionado'
        }
        
        for key, default_value in defaults.items():
            if key not in data:
                data[key] = default_value
        
        # Estandarizar para compatibilidad con sistema existente
        data['decision'] = data['accion'].upper()
        if data['decision'] == 'ALLIN': data['decision'] = 'ALL-IN'
        
        # Compatibilidad con parser antiguo (retornar estructura similar)
        # Parsear valores numéricos seguros
        try:
            if 'amount_bb' in data:
                data['amount_bb'] = float(str(data['amount_bb']).replace('%',''))
        except:
            data['amount_bb'] = 0.0
        
        # Convertir confidence string a float si es necesario
        if isinstance(data.get('confidence'), str):
            conf_map = {'LOW': 0.3, 'MEDIUM': 0.5, 'HIGH': 0.8, 'low': 0.3, 'medium': 0.5, 'high': 0.8}
            data['confidence'] = conf_map.get(data['confidence'], 0.5)

        return data

# ========================================================================
# FUNCIÓN DE CONVENIENCIA (BACKWARD COMPATIBLE)
# ========================================================================
def parse_deepseek_response(content: str) -> Dict[str, Any]:
    """
    Función de conveniencia para parsear respuestas.
    Mantiene compatibilidad con código existente.
    """
    parser = ResponseParser()
    result = parser.parse(content)
    
    # Adaptador para mantener la firma de retorno exacta del parser antiguo
    # Convertir confidence string a float si es necesario
    confidence_val = result.get('confidence', 0.5)
    if isinstance(confidence_val, str):
        confidence_map = {'LOW': 0.3, 'MEDIUM': 0.5, 'HIGH': 0.8}
        confidence_val = confidence_map.get(confidence_val.upper(), 0.5)
    
    return {
        'decision': result.get('decision', 'FOLD'),
        'confidence': float(confidence_val),  # Asegurar que es float
        'reasoning': result.get('reasoning', ''),
        'decision_final': result.get('decision_final', ''),
        'size_bb': result.get('amount_bb', 0.0),
        'size_pot': result.get('pot_fraction', 0.0) * 100 if result.get('pot_fraction') else 0.0,
        'accion': result.get('accion', 'fold'), # ✅ AGREGADO: Campo clave para tests
        'action_type': result.get('accion', 'fold'),
        'amount_bb': result.get('amount_bb', 0.0),
        'to_call_bb': result.get('to_call_bb', 0.0),
        'pot_fraction': result.get('pot_fraction', 0.0),
        'raw_json': result,
        'diagnostics': result.get('contexto_percibido', result.get('contexto', {})) # ✅ ACTUALIZADO: Candado de Transparencia
    }
