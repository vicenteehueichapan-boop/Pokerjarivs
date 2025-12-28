import json
from typing import Dict, Any
from engine.prompts import get_prompt_for_street as _get_prompt
try:
    from engine.prompts.players_formatter import format_players_info as _format_players
except ImportError:
    _format_players = None

def format_engine_features_block(context: Dict[str, Any]) -> str:
    """
    Formatea el bloque técnico como JSON fiel, ordenado y legible.
    Incluye engine_features, engine_features_metadata y engine_features_error si existen.
    """
    block = {}
    if 'engine_features' in context:
        block['engine_features'] = context['engine_features']
    if 'engine_features_metadata' in context:
        block['engine_features_metadata'] = context['engine_features_metadata']
    if 'engine_features_error' in context:
        block['engine_features_error'] = context['engine_features_error']
    if not block:
        return '\nDATOS TÉCNICOS: ❌ No hay evaluación técnica disponible.'
    return '\nDATOS TÉCNICOS (JSON):\n' + json.dumps(block, indent=3, ensure_ascii=False)

def get_prompt_for_street_json(street: str, context: Dict[str, Any]) -> str:
    """
    Genera el prompt para la fase indicada, insertando el bloque técnico JSON fiel,
    y soportando funciones auxiliares como formateo de jugadores si el contexto lo requiere.
    """
    # 1. Obtener el prompt base real del builder modular
    prompt = _get_prompt(street, context)

    # 2. Formatear bloque técnico JSON fiel
    engine_block = format_engine_features_block(context)

    # 3. Insertar el bloque técnico JSON justo después de la evaluación de mano
    lines = prompt.split('\n')
    insert_idx = None
    for i, line in enumerate(lines):
        # Busca la línea de evaluación de mano (usualmente contiene 'Evaluación de mano' o similar)
        if 'Evaluación de mano' in line or '[Evaluación de mano' in line:
            insert_idx = i + 1
            break
    if insert_idx is not None:
        lines.insert(insert_idx, engine_block)
        prompt = '\n'.join(lines)
    else:
        # Si no encuentra, lo agrega al inicio
        prompt = engine_block + '\n' + prompt

    return prompt

def format_players_info(players_data: Dict, hero_stack: float, hero_position: str = 'Unknown', pot: float = 0) -> str:
    """
    Formatea la información de jugadores usando la función auxiliar del sistema si está disponible.
    """
    if _format_players:
        return _format_players(players_data, hero_stack, hero_position, pot)
    return "[INFO JUGADORES NO DISPONIBLE]"
