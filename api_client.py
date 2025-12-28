"""
API Manager
===========
Gestiona múltiples clientes de DeepSeek API para paralelización
"""

import os
from typing import List, Optional
from pathlib import Path
from openai import OpenAI


class DeepSeekAPIManager:
    """
    Gestiona múltiples API keys de DeepSeek para procesamiento paralelo
    
    Soporta hasta 6 clientes simultáneos (1 por mesa) con round-robin
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa manager de APIs
        
        Args:
            api_key: API key específica o None para buscar en environment
                    - DEEPSEEK_API_KEY: Key principal
                    - DEEPSEEK_API_KEY_2, _3, _4, _5, _6: Keys adicionales
        """
        # Cargar variables de entorno si no están cargadas
        self._load_env()
        
        # Cargar múltiples API keys
        self.api_keys = []
        
        if api_key:
            self.api_keys.append(api_key)
        else:
            # Buscar key principal
            main_key = os.getenv('DEEPSEEK_API_KEY')
            if main_key:
                self.api_keys.append(main_key)
            
            # Buscar keys adicionales (2-6 para 6 mesas)
            for i in range(2, 7):
                extra_key = os.getenv(f'DEEPSEEK_API_KEY_{i}')
                if extra_key:
                    self.api_keys.append(extra_key)
        
        # Crear clientes
        if not self.api_keys:
            print("WARNING: No API key de DeepSeek configurada")
            print("   Set DEEPSEEK_API_KEY en environment o pasa api_key al constructor")
            print("   Para paralelización: DEEPSEEK_API_KEY_2, _3, _4, _5, _6")
            self.clients = []
        else:
            # Crear un cliente por cada API key (pool de clients)
            self.clients = [
                OpenAI(api_key=key, base_url="https://api.deepseek.com")
                for key in self.api_keys
            ]
            print(f"DeepSeek clients inicializados: {len(self.clients)} API keys")
            if len(self.clients) > 1:
                print(f"Modo PARALELO: {len(self.clients)} mesas simultáneas sin rate limiting")
    
    def _load_env(self):
        """Carga variables de entorno desde .env si existe"""
        try:
            from dotenv import load_dotenv
            project_root = Path(__file__).parent.parent.parent.parent
            env_file = project_root / '.env'
            if env_file.exists():
                load_dotenv(env_file)
                print(f"Variables de entorno cargadas desde {env_file}")
            else:
                load_dotenv()
        except ImportError:
            pass  # dotenv no instalado
    
    def get_client(self, mesa_id: int = 1) -> Optional[OpenAI]:
        """
        Obtiene cliente específico para una mesa (round-robin)
        
        Args:
            mesa_id: ID de la mesa (1-6)
            
        Returns:
            Cliente OpenAI o None si no hay clientes
        """
        if not self.clients:
            return None
        
        # Round-robin: distribuir carga entre clientes
        client_index = (mesa_id - 1) % len(self.clients)
        return self.clients[client_index]
    
    def has_clients(self) -> bool:
        """Retorna True si hay al menos un cliente configurado"""
        return len(self.clients) > 0
    
    def get_client_count(self) -> int:
        """Retorna número de clientes disponibles"""
        return len(self.clients)
    
    def get_clients(self) -> List[OpenAI]:
        """Retorna lista de todos los clientes"""
        return self.clients
