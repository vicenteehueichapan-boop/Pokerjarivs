"""
Decision Logger - Sistema de logging y análisis para reentrenamiento

Registra todas las decisiones del bot para análisis posterior y reentrenamiento.
Permite comparar decisiones reales vs GTO y detectar spots problemáticos.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class DecisionLogger:
    """
    Sistema de logging avanzado para decisiones de poker.
    Guarda decisiones, contexto, y análisis para reentrenamiento.
    """
    
    def __init__(self, log_dir="logs/decisions"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivo de sesión actual
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session_file = self.log_dir / f"session_{timestamp}.jsonl"
        
        # Archivo de análisis agregado
        self.analysis_file = self.log_dir / "analysis_summary.json"
        
        # Stats en memoria
        self.session_stats = {
            "total_decisions": 0,
            "by_street": {"preflop": 0, "flop": 0, "turn": 0, "river": 0},
            "by_action": {"FOLD": 0, "CALL": 0, "RAISE": 0, "BET": 0, "CHECK": 0},
            "errors": []
        }
    
    def log_decision(self, decision_data: Dict):
        """
        Registra una decisión completa con todo el contexto.
        
        Args:
            decision_data: Dict con toda la información de la decisión
                - street: "preflop", "flop", "turn", "river"
                - hero_cards: ['Ah', 'Kd']
                - board: ['Ks', '9h', '3d'] (si aplica)
                - position: "CO", "BTN", etc.
                - action_taken: "RAISE", "CALL", "FOLD"
                - confidence: 0.0-1.0
                - reasoning: String con razonamiento
                - pot: Float
                - stack: Float
                - villain_pattern: Dict (si disponible)
                - timestamp: Auto-generado
                - hand_id: Opcional, para tracking
        """
        # Agregar metadata
        decision_data["timestamp"] = datetime.now().isoformat()
        decision_data["session_id"] = self.current_session_file.stem
        
        # Guardar en archivo JSONL (una línea por decisión)
        with open(self.current_session_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(decision_data, ensure_ascii=False) + '\n')
        
        # Actualizar stats
        self.session_stats["total_decisions"] += 1
        street = decision_data.get("street", "unknown")
        action = decision_data.get("action_taken", "unknown")
        
        if street in self.session_stats["by_street"]:
            self.session_stats["by_street"][street] += 1
        
        if action in self.session_stats["by_action"]:
            self.session_stats["by_action"][action] += 1
    
    def load_session(self, session_file: str = None) -> List[Dict]:
        """
        Carga una sesión completa de decisiones.
        
        Args:
            session_file: Nombre del archivo (None = sesión actual)
        
        Returns:
            Lista de decisiones
        """
        if session_file is None:
            filepath = self.current_session_file
        else:
            filepath = self.log_dir / session_file
        
        if not filepath.exists():
            return []
        
        decisions = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    decisions.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        
        return decisions
    
    def analyze_decision(self, decision_data: Dict, gto_action: Optional[str] = None) -> Dict:
        """
        Analiza una decisión individual comparándola con GTO (si disponible).
        
        Args:
            decision_data: Decisión a analizar
            gto_action: Acción GTO recomendada (opcional)
        
        Returns:
            Dict con análisis:
            - is_gto_aligned: Boolean
            - deviation_severity: "none", "minor", "major"
            - risk_level: "low", "medium", "high"
            - notes: Lista de observaciones
        """
        analysis = {
            "is_gto_aligned": None,
            "deviation_severity": "unknown",
            "risk_level": "low",
            "notes": []
        }
        
        action = decision_data.get("action_taken", "").upper()
        confidence = decision_data.get("confidence", 0.5)
        street = decision_data.get("street", "")
        
        # Comparar con GTO si disponible
        if gto_action:
            if action == gto_action.upper():
                analysis["is_gto_aligned"] = True
                analysis["deviation_severity"] = "none"
                analysis["notes"].append("✅ Alineado con GTO")
            else:
                analysis["is_gto_aligned"] = False
                
                # Determinar severidad
                if action == "FOLD" and gto_action in ["RAISE", "BET"]:
                    analysis["deviation_severity"] = "major"
                    analysis["risk_level"] = "high"
                    analysis["notes"].append("⚠️ CRÍTICO: Foldeo en spot GTO agresivo")
                
                elif action in ["RAISE", "BET"] and gto_action == "FOLD":
                    analysis["deviation_severity"] = "major"
                    analysis["risk_level"] = "high"
                    analysis["notes"].append("⚠️ CRÍTICO: Apuesta en spot GTO fold")
                
                elif action == "CALL" and gto_action in ["RAISE", "BET"]:
                    analysis["deviation_severity"] = "minor"
                    analysis["risk_level"] = "medium"
                    analysis["notes"].append("⚠️ Pasivo vs GTO agresivo")
                
                else:
                    analysis["deviation_severity"] = "minor"
                    analysis["notes"].append("⚠️ Desviación menor de GTO")
        
        # Análisis de confianza
        if confidence < 0.5:
            analysis["notes"].append(f"⚠️ Baja confianza ({confidence:.1%})")
            analysis["risk_level"] = "high"
        elif confidence < 0.7:
            analysis["notes"].append(f"ℹ️ Confianza moderada ({confidence:.1%})")
        else:
            analysis["notes"].append(f"✅ Alta confianza ({confidence:.1%})")
        
        # Análisis contextual
        if street == "river" and action in ["BET", "RAISE"]:
            analysis["notes"].append("💡 River bet - Verificar si es value o bluff")
        
        if action == "FOLD" and street == "preflop":
            analysis["notes"].append("💡 Fold preflop - Verificar si está en rango")
        
        return analysis
    
    def get_session_stats(self, session_file: str = None) -> dict:
        """
        Retorna estadísticas de sesión como diccionario.
        
        Returns:
            Dict con estadísticas
        """
        decisions = self.load_session(session_file)
        
        if not decisions:
            return {
                "total_decisions": 0,
                "streets": {},
                "actions": {},
                "avg_confidence": 0.0
            }
        
        # Stats básicas
        total = len(decisions)
        by_street = {"preflop": 0, "flop": 0, "turn": 0, "river": 0}
        by_action = {}
        confidences = []
        
        for dec in decisions:
            street = dec.get("street", "unknown")
            action = dec.get("action_taken", "unknown")
            conf = dec.get("confidence", 0.5)
            
            if street in by_street:
                by_street[street] += 1
            
            by_action[action] = by_action.get(action, 0) + 1
            
            # Manejar confidence que puede ser float o string
            if isinstance(conf, str):
                conf_map = {'LOW': 0.3, 'MEDIUM': 0.5, 'HIGH': 0.8}
                conf = conf_map.get(conf.upper(), 0.5)
            confidences.append(float(conf))
        
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            "total_decisions": total,
            "streets": by_street,
            "actions": by_action,
            "avg_confidence": avg_conf
        }
    
    def generate_session_report(self, session_file: str = None) -> str:
        """
        Genera un reporte detallado de una sesión.
        
        Returns:
            String formateado con el reporte
        """
        stats = self.get_session_stats(session_file)
        
        if stats["total_decisions"] == 0:
            return "❌ No hay decisiones en esta sesión"
        
        total = stats["total_decisions"]
        by_street = stats["streets"]
        by_action = stats["actions"]
        
        # Generar reporte
        report = f"""
{'='*70}
📊 REPORTE DE SESIÓN
{'='*70}

📈 ESTADÍSTICAS GENERALES:
   Total de decisiones: {total}
   
   Por calle:
      Preflop: {by_street['preflop']} ({by_street['preflop']/total*100:.1f}%)
      Flop:    {by_street['flop']} ({by_street['flop']/total*100:.1f}%)
      Turn:    {by_street['turn']} ({by_street['turn']/total*100:.1f}%)
      River:   {by_street['river']} ({by_street['river']/total*100:.1f}%)
   
   Por acción:
"""
        
        for action, count in sorted(by_action.items(), key=lambda x: x[1], reverse=True):
            pct = count / total * 100
            report += f"      {action}: {count} ({pct:.1f}%)\n"
        
        # Calcular métricas agregadas
        folds = by_action.get("FOLD", 0)
        aggression = by_action.get("RAISE", 0) + by_action.get("BET", 0)
        
        vpip = ((total - folds) / total * 100) if total > 0 else 0
        aggression_pct = (aggression / total * 100) if total > 0 else 0
        
        report += f"""
📊 MÉTRICAS CLAVE:
   VPIP estimado: {vpip:.1f}% (% de manos jugadas)
   Aggression:    {aggression_pct:.1f}% (% de raises/bets)
   
{'='*70}
"""
        
        return report
    
    def find_problematic_spots(self, min_decisions: int = 10) -> List[Dict]:
        """
        Identifica spots problemáticos en las decisiones registradas.
        
        Returns:
            Lista de spots que requieren atención
        """
        decisions = self.load_session()
        
        if len(decisions) < min_decisions:
            return [{
                "issue": "insufficient_data",
                "message": f"Solo {len(decisions)} decisiones. Mínimo: {min_decisions}"
            }]
        
        problems = []
        
        # Detector 1: Demasiados folds preflop
        preflop_decisions = [d for d in decisions if d.get("street") == "preflop"]
        if preflop_decisions:
            preflop_folds = len([d for d in preflop_decisions if d.get("action_taken") == "FOLD"])
            fold_rate = preflop_folds / len(preflop_decisions)
            
            if fold_rate > 0.8:  # >80% folds
                problems.append({
                    "issue": "too_tight_preflop",
                    "severity": "high",
                    "message": f"Fold rate preflop: {fold_rate:.1%} (muy tight)",
                    "recommendation": "Revisar rangos preflop, puede estar dejando pasar value"
                })
        
        # Detector 2: Baja confianza consistente
        low_conf_decisions = [d for d in decisions if d.get("confidence", 1.0) < 0.5]
        if len(low_conf_decisions) > len(decisions) * 0.3:  # >30% baja confianza
            problems.append({
                "issue": "low_confidence",
                "severity": "medium",
                "message": f"{len(low_conf_decisions)} decisiones con baja confianza",
                "recommendation": "Revisar rangos o feature formatter, sistema inseguro"
            })
        
        # Detector 3: No hay agresión en river
        river_decisions = [d for d in decisions if d.get("street") == "river"]
        if river_decisions:
            river_bets = len([d for d in river_decisions if d.get("action_taken") in ["BET", "RAISE"]])
            bet_rate = river_bets / len(river_decisions)
            
            if bet_rate < 0.1:  # <10% bets en river
                problems.append({
                    "issue": "too_passive_river",
                    "severity": "medium",
                    "message": f"Solo {bet_rate:.1%} bets en river (muy pasivo)",
                    "recommendation": "Revisar thin value betting, puede estar dejando dinero"
                })
        
        return problems
    
    def export_for_training(self, output_file: str = "training_data.json"):
        """
        Exporta decisiones en formato para reentrenamiento.
        
        Formato compatible con sistemas de ML.
        """
        decisions = self.load_session()
        
        training_data = []
        for dec in decisions:
            # Extraer features relevantes
            training_sample = {
                "features": {
                    "street": dec.get("street"),
                    "position": dec.get("position"),
                    "pot": dec.get("pot", 0),
                    "stack": dec.get("stack", 0),
                    "spr": dec.get("stack", 0) / dec.get("pot", 1) if dec.get("pot", 0) > 0 else 999,
                    "hero_cards": dec.get("hero_cards", []),
                    "board": dec.get("board", []),
                    "villain_pattern": dec.get("villain_pattern", {}),
                },
                "label": {
                    "action": dec.get("action_taken"),
                    "confidence": dec.get("confidence", 0.5)
                },
                "metadata": {
                    "timestamp": dec.get("timestamp"),
                    "reasoning": dec.get("reasoning", "")
                }
            }
            
            training_data.append(training_sample)
        
        # Guardar
        output_path = self.log_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    def compare_decisions(self, decision1: Dict, decision2: Dict) -> Dict:
        """
        Compara dos decisiones para el mismo spot.
        
        Args:
            decision1: Primera decisión (ej: Bot)
            decision2: Segunda decisión (ej: GTO o Tu decisión)
        
        Returns:
            Dict con comparación detallada
        """
        comparison = {
            "same_action": False,
            "confidence_diff": 0.0,
            "analysis": []
        }
        
        action1 = decision1.get("action_taken", "").upper()
        action2 = decision2.get("action_taken", "").upper()
        
        conf1 = decision1.get("confidence", 0.5)
        conf2 = decision2.get("confidence", 0.5)
        
        # Comparar acción
        if action1 == action2:
            comparison["same_action"] = True
            comparison["analysis"].append(f"✅ Misma acción: {action1}")
        else:
            comparison["same_action"] = False
            comparison["analysis"].append(f"❌ Acciones diferentes: {action1} vs {action2}")
            
            # Evaluar severidad
            critical_pairs = [
                ("FOLD", "RAISE"), ("FOLD", "BET"),
                ("RAISE", "FOLD"), ("BET", "FOLD")
            ]
            
            if (action1, action2) in critical_pairs or (action2, action1) in critical_pairs:
                comparison["analysis"].append("⚠️ CRÍTICO: Desviación extrema")
        
        # Comparar confianza
        comparison["confidence_diff"] = abs(conf1 - conf2)
        
        if comparison["confidence_diff"] > 0.3:
            comparison["analysis"].append(f"⚠️ Gran diferencia en confianza: {conf1:.1%} vs {conf2:.1%}")
        else:
            comparison["analysis"].append(f"ℹ️ Confianza similar: {conf1:.1%} vs {conf2:.1%}")
        
        return comparison

