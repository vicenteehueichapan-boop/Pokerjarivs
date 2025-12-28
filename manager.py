from typing import Dict, Any
import importlib

# Mapeo de streets a módulos de construcción de prompts
PROMPT_BUILDERS = {
    'preflop': 'backend.decision_engine.prompts.preflop',
    'flop': 'backend.decision_engine.prompts.flop',
    'turn': 'backend.decision_engine.prompts.turn',
    'river': 'backend.decision_engine.prompts.river'
}

def get_prompt_for_street(street: str, context: Dict[str, Any]) -> str:
    """
    Despacha la construcción del prompt al módulo correspondiente según la calle.
    """
    # Normalización defensiva (Case-insensitive)
    street_key = street.lower().strip()
    
    if street_key not in PROMPT_BUILDERS:
         raise ValueError(f"Street no válida: {street}. Valores permitidos: {list(PROMPT_BUILDERS.keys())}")

    module_name = PROMPT_BUILDERS[street_key]
    
    try:
        module = importlib.import_module(module_name)
        
        # Convención: cada módulo tiene una función build_{street}_prompt
        builder_func_name = f"build_{street_key}_prompt"
        builder_func = getattr(module, builder_func_name)
        
        return builder_func(context)
        
    except ImportError as e:
        raise ImportError(f"No se pudo cargar el módulo de prompt para {street_key}: {e}")
    except AttributeError as e:
        raise AttributeError(f"El módulo {module_name} no tiene la función {builder_func_name}: {e}")
    except Exception as e:
        raise Exception(f"Error construyendo prompt para {street_key}: {e}")
