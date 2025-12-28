import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

class PokerEngineClient:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.engine_path = self.project_root / "normalization" / "PokerEngineCore-main" / "src" / "PokerEngine.Cli" / "PokerEngine.Cli.csproj"
        
    def compute_features(self, game: str, pockets: List[str], board: List[str]) -> Dict[str, Any]:
        """
        Llama al PokerEngine (C#) para analizar la mano.
        """
        # Bypass para Preflop o Board Vacío
        # El motor C# (Hand2NoteCore) lanza error "Deuce not found" si se evalúa fuerza sin board.
        if not board or len(board) == 0:
            print("ENGINE: Preflop detected (empty board). Skipping C# engine call.")
            return {
                "street": "Preflop",
                "hand": {
                    "description": "High Card (Preflop)",
                    "type": "HighCard",
                    "rank": 0
                },
                "relevantHandValue": {
                    "labels": ["Preflop"]
                },
                "draw": {
                    "isFlushDraw": False,
                    "isStraightDraw": False,
                    "isGutshot": False,
                    "flushOutsCount": 0,
                    "straightOutsCount": 0
                }
            }

        payload = {
            "op": "compute_features",
            "game": game,
            "pockets": pockets,
            "board": board
        }
        
        json_payload = json.dumps(payload)
        
        # DEBUG LOGS
        print(f"ENGINE DEBUG: Project Path: {self.engine_path}")
        print(f"ENGINE DEBUG: Payload: {json_payload}")

        try:
            # Ejecutar dotnet run
            cmd = ["dotnet", "run", "--project", str(self.engine_path)]
            print(f"ENGINE DEBUG: Executing: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd, 
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.project_root) # Set CWD explicitly
            )
            
            stdout, stderr = process.communicate(input=json_payload)

            if stdout:
                print(f"ENGINE DEBUG: STDOUT (First 500 chars): {stdout[:500]}...")
            if stderr:
                print(f"ENGINE DEBUG: STDERR: {stderr}")

            if process.returncode != 0:
                print(f"PokerEngine Error (Code {process.returncode})")
                return {}

            # Intentar parsear JSON
            # Buscamos el último JSON válido
            lines = stdout.strip().split('\n')
            json_str = ""
            # Estrategia: buscar el bloque JSON principal
            try:
                # Si hay logs de build, el JSON estará al final
                # Buscamos la primera llave { y la última }
                start = stdout.find('{')
                end = stdout.rfind('}')
                if start != -1 and end != -1:
                    clean_json = stdout[start:end+1]
                    return json.loads(clean_json)
                else:
                    print("No JSON found in stdout")
                    return {}
            except json.JSONDecodeError as e:
                print(f"JSON Parse Error: {e}")
                return {}

        except Exception as e:
            print(f"Error llamando a PokerEngine: {e}")
            return {}
