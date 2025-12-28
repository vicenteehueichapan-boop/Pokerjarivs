"""
Action History Tracker - Memoria multistreet para el Bot de Poker

Mantiene un registro de todas las acciones en cada calle (preflop/flop/turn/river)
para permitir decisiones coherentes y construir lines estratégicas.
"""

from typing import List, Dict, Optional

class ActionHistory:
    """
    Rastrea acciones a través de múltiples calles de poker.
    """
    
    def __init__(self):
        self.history = {
            "preflop": [],
            "flop": [],
            "turn": [],
            "river": []
        }
        self.pot_history = {
            "preflop": 0,
            "flop": 0,
            "turn": 0,
            "river": 0
        }
    
    def add_action(self, street: str, player: str, action: str, amount: Optional[float] = None):
        """
        Registra una acción en una calle específica.
        
        Args:
            street: "preflop", "flop", "turn", "river"
            player: "hero", "villain", "villain2" (para multiway)
            action: "bet", "call", "raise", "check", "fold", "3bet", "4bet"
            amount: tamaño de la apuesta en bb (None para check/fold)
        """
        if street not in self.history:
            raise ValueError(f"Calle inválida: {street}")
        
        self.history[street].append({
            "player": player.lower(),
            "action": action.lower(),
            "amount": amount
        })
    
    def add_pot_size(self, street: str, pot_size: float):
        """Registra el tamaño del pot al inicio de una calle"""
        if street in self.pot_history:
            self.pot_history[street] = pot_size
    
    def get_formatted_history(self, up_to_street: str = "river") -> str:
        """
        Genera un resumen legible del historial hasta una calle específica.
        
        Args:
            up_to_street: Incluir acciones hasta esta calle (inclusive)
        
        Returns:
            String formateado para incluir en el prompt del LLM
        """
        streets_order = ["preflop", "flop", "turn", "river"]
        
        try:
            end_index = streets_order.index(up_to_street) + 1
        except ValueError:
            end_index = len(streets_order)
        
        formatted = ""
        
        for street in streets_order[:end_index]:
            actions = self.history[street]
            pot = self.pot_history.get(street, 0)
            
            if not actions and pot == 0:
                continue
            
            formatted += f"\n   🃏 {street.upper()}:"
            
            if pot > 0:
                formatted += f" (Pot: {pot} bb)"
            
            formatted += "\n"
            
            if not actions:
                formatted += "      (Sin acciones registradas)\n"
            else:
                for act in actions:
                    player = act['player'].capitalize()
                    action = act['action'].upper()
                    amount = f" {act['amount']} bb" if act['amount'] else ""
                    formatted += f"      {player} {action}{amount}\n"
        
        return formatted if formatted else "   (No hay historial disponible)"
    
    def analyze_villain_pattern(self) -> Dict:
        """
        Analiza el patrón de juego del villain para generar insights.
        
        Returns:
            Dict con características del patrón de villain:
            - aggression_freq: Frecuencia de acciones agresivas (bet/raise)
            - passive_freq: Frecuencia de acciones pasivas (check/call)
            - showed_weakness: Boolean si hizo check en algún momento
            - showed_strength: Boolean si raised en algún momento
            - description: Texto descriptivo del patrón
        """
        villain_actions = []
        
        for street in self.history.values():
            villain_actions.extend([a for a in street if a['player'] in ['villain', 'villain2']])
        
        if not villain_actions:
            return {
                "aggression_freq": 0.0,
                "passive_freq": 0.0,
                "showed_weakness": False,
                "showed_strength": False,
                "description": "Sin acciones de villain registradas"
            }
        
        # Contar tipos de acciones
        action_counts = {
            "aggressive": 0,  # bet, raise, 3bet, 4bet
            "passive": 0,     # call, check
            "fold": 0
        }
        
        for act in villain_actions:
            action_type = act['action']
            
            if action_type in ['bet', 'raise', '3bet', '4bet']:
                action_counts["aggressive"] += 1
            elif action_type in ['call', 'check']:
                action_counts["passive"] += 1
            elif action_type == 'fold':
                action_counts["fold"] += 1
        
        total_actions = len(villain_actions)
        
        # Calcular frecuencias
        aggression_freq = action_counts["aggressive"] / total_actions if total_actions > 0 else 0
        passive_freq = action_counts["passive"] / total_actions if total_actions > 0 else 0
        
        # Detectar patrones específicos
        showed_weakness = any(a['action'] in ['check', 'call'] for a in villain_actions)
        showed_strength = any(a['action'] in ['raise', '3bet', '4bet'] for a in villain_actions)
        
        # Generar descripción verbal
        if aggression_freq > 0.6:
            description = "🔥 Villain AGRESIVO (multiple bets/raises) - Puede estar faroleando o tiene mano fuerte"
        elif passive_freq > 0.7:
            description = "💤 Villain PASIVO (mostly checks/calls) - Explotable con bluffs, probablemente weak/marginal"
        elif showed_weakness and not showed_strength:
            description = "⚠️ Villain mostró DEBILIDAD (checked) - Alta fold equity disponible"
        elif showed_strength and not showed_weakness:
            description = "💪 Villain mostró FUERZA (raised) - Respeta su rango"
        else:
            description = "🤔 Patrón MIXTO - Juega estándar, sin tells claros"
        
        return {
            "aggression_freq": aggression_freq,
            "passive_freq": passive_freq,
            "showed_weakness": showed_weakness,
            "showed_strength": showed_strength,
            "description": description,
            "total_actions": total_actions
        }
    
    def get_hero_line(self) -> str:
        """
        Resume la línea de juego de Hero (útil para coherencia).
        
        Returns:
            String describiendo la línea de Hero
        """
        hero_actions = []
        
        for street in ["preflop", "flop", "turn", "river"]:
            actions = [a for a in self.history[street] if a['player'] == 'hero']
            if actions:
                # Tomar la acción más significativa de la calle
                for act in actions:
                    if act['action'] in ['bet', 'raise', '3bet', '4bet']:
                        hero_actions.append(f"{street.capitalize()}: {act['action'].upper()}")
                        break
                else:
                    # Si no hubo acción agresiva, tomar la primera
                    hero_actions.append(f"{street.capitalize()}: {actions[0]['action'].upper()}")
        
        if not hero_actions:
            return "Línea de Hero: Sin acciones registradas"
        
        line = " → ".join(hero_actions)
        
        # Detectar lines comunes
        if "BET" in line and line.count("BET") >= 2:
            line += " (DOUBLE/TRIPLE BARREL - Línea agresiva)"
        elif "CHECK" in line and line.count("CHECK") >= 2:
            line += " (POT CONTROL - Línea conservadora)"
        
        return f"Línea de Hero: {line}"
    
    def get_street_summary(self, street: str) -> Dict:
        """
        Obtiene un resumen de una calle específica.
        
        Returns:
            Dict con información de la calle:
            - who_initiated: "hero" o "villain"
            - aggressor: quién apostó primero
            - was_raised: si hubo raise
            - pot_growth: crecimiento del pot
        """
        actions = self.history.get(street, [])
        
        if not actions:
            return {
                "who_initiated": None,
                "aggressor": None,
                "was_raised": False,
                "pot_growth": 0
            }
        
        # Quién inició la acción (primer bet/raise)
        aggressor = None
        for act in actions:
            if act['action'] in ['bet', 'raise', '3bet']:
                aggressor = act['player']
                break
        
        # Si hubo raise
        was_raised = any(a['action'] in ['raise', '3bet', '4bet'] for a in actions)
        
        # Crecimiento del pot (suma de amounts)
        pot_growth = sum(a.get('amount', 0) for a in actions if a['amount'] is not None)
        
        return {
            "who_initiated": actions[0]['player'] if actions else None,
            "aggressor": aggressor,
            "was_raised": was_raised,
            "pot_growth": pot_growth
        }
    
    def should_continue_aggression(self, current_street: str) -> Dict:
        """
        Analiza si Hero debería continuar con agresión (barrels).
        
        Returns:
            Dict con recomendación:
            - should_barrel: Boolean
            - reasoning: String explicando por qué
            - fold_equity_estimate: Float (0.0-1.0)
        """
        # Analizar si Hero ha sido agresivo en calles previas
        streets_order = ["preflop", "flop", "turn", "river"]
        current_idx = streets_order.index(current_street) if current_street in streets_order else 0
        
        hero_was_aggressor_before = False
        streets_bet = []
        
        for street in streets_order[:current_idx]:
            summary = self.get_street_summary(street)
            if summary["aggressor"] == "hero":
                hero_was_aggressor_before = True
                streets_bet.append(street)
        
        if not hero_was_aggressor_before:
            return {
                "should_barrel": False,
                "reasoning": "Hero no inició agresión en calles previas - No es barrel, es nueva línea",
                "fold_equity_estimate": 0.5
            }
        
        # Analizar respuesta de villain
        villain_pattern = self.analyze_villain_pattern()
        
        # Si villain solo ha hecho call (no raised), tenemos fold equity
        if villain_pattern["passive_freq"] > 0.7:
            fold_equity = 0.6  # Alta fold equity
            should_barrel = True
            reasoning = f"Villain pasivo ({villain_pattern['passive_freq']:.0%} calls/checks) - Alta fold equity para barrel"
        
        elif villain_pattern["showed_strength"]:
            fold_equity = 0.2  # Baja fold equity
            should_barrel = False
            reasoning = "Villain mostró fuerza (raise) - Baja fold equity, necesitas mano real"
        
        else:
            fold_equity = 0.45  # Moderada
            should_barrel = True
            reasoning = "Patrón mixto - Fold equity moderada, barrel con draws/equity"
        
        # Ajustar por número de calles ya apostadas
        if len(streets_bet) >= 2:
            fold_equity *= 0.8  # Reducir estimate en triple barrels
            reasoning += f" | ⚠️ Ya apostaste en {len(streets_bet)} calles (harder to continue)"
        
        return {
            "should_barrel": should_barrel,
            "reasoning": reasoning,
            "fold_equity_estimate": fold_equity,
            "streets_bet": streets_bet
        }
    
    def clear(self):
        """Limpia todo el historial (para nueva mano)"""
        self.history = {
            "preflop": [],
            "flop": [],
            "turn": [],
            "river": []
        }
        self.pot_history = {
            "preflop": 0,
            "flop": 0,
            "turn": 0,
            "river": 0
        }

