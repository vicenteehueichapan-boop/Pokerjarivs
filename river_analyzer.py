"""
River Analyzer - Análisis avanzado de decisiones en River

El river es la calle más compleja y crítica. Este módulo ayuda al LLM
a tomar decisiones óptimas sobre thin value, bluff catching, y sizing.
"""

from typing import Dict, List, Optional, Tuple

class RiverAnalyzer:
    """
    Analiza situaciones de river y genera recomendaciones estratégicas.
    """
    
    def __init__(self, hero_cards: List[str], board: List[str], hand_strength: Dict, 
                 action_history, pot: float, stack: float):
        """
        Args:
            hero_cards: ['Ah', 'Kd']
            board: ['Ks', '9h', '3d', '2c', '7s'] (5 cartas en river)
            hand_strength: Dict del poker engine con categoría de mano
            action_history: Instancia de ActionHistory
            pot: Tamaño del pot actual (bb)
            stack: Stack efectivo restante (bb)
        """
        self.hero_cards = hero_cards
        self.board = board
        self.hand_strength = hand_strength
        self.history = action_history
        self.pot = pot
        self.stack = stack
    
    def classify_hand_type(self) -> str:
        """
        Clasifica la mano de hero en river según su fuerza relativa.
        
        Returns:
            "nuts", "value", "marginal", "bluff_catcher", "air"
        """
        category = self.hand_strength.get('handValue', {}).get('category', 'HighCard')
        
        # NUTS: Straight, Flush, Full House, Quads
        if category in ["Straight", "Flush", "FullHouse", "FourOfAKind"]:
            # Verificar si realmente es nuts (no hay nada mejor posible)
            board_ranks = [card[0] for card in self.board]
            board_has_pair = len(board_ranks) != len(set(board_ranks))
            
            if category == "Flush" and board_has_pair:
                return "value"  # Flush con board paired no es nuts (puede haber full)
            
            if category == "Straight":
                # Verificar si es nut straight o low straight
                rank = self.hand_strength.get('handValue', {}).get('rank', '')
                if 'Ace' in rank or 'King' in rank:
                    return "nuts"
                else:
                    return "value"  # Low straight
            
            return "nuts"
        
        # VALUE: Sets, Two Pair, Top Pair fuerte
        if category in ["ThreeOfAKind", "TwoPair"]:
            return "value"
        
        # PAIR: Clasificar según posición del par
        if category == "Pair":
            rank = self.hand_strength.get('handValue', {}).get('rank', '')
            uses_pocket = self.hand_strength.get('usesPocketCards', True)
            
            # Si es board pair, es weak
            if not uses_pocket:
                return "bluff_catcher"
            
            # Determinar si es top pair, middle, o bottom
            rank_order = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
            board_ranks = [card[0] for card in self.board]
            board_ranks_sorted = sorted(board_ranks, key=lambda x: rank_order.index(x))
            
            pair_rank = rank[0] if rank else 'X'
            
            if pair_rank == board_ranks_sorted[0]:
                # Top pair
                kickers = self.hand_strength.get('handValue', {}).get('kickers', [])
                if kickers and kickers[0] in ['Ace', 'King', 'Queen']:
                    return "value"  # Top pair good kicker
                else:
                    return "marginal"  # Top pair weak kicker
            elif pair_rank == board_ranks_sorted[1]:
                return "marginal"  # Middle pair
            else:
                return "bluff_catcher"  # Bottom pair
        
        # AIR: High Card
        return "air"
    
    def recommend_sizing(self, action: str = "bet") -> Dict:
        """
        Recomienda sizing basado en la situación y tipo de mano.
        
        Args:
            action: "bet" o "call"
        
        Returns:
            Dict con:
            - size_pct: Porcentaje del pot recomendado
            - size_bb: Tamaño en bb
            - reason: Explicación
        """
        hand_type = self.classify_hand_type()
        
        if action == "bet":
            if hand_type == "nuts":
                # Polarizar: Bet grande (75-150% pot)
                size_pct = 100
                reason = "Nuts - Maximize value with large polarized bet"
            
            elif hand_type == "value":
                # Bet medio-grande (60-80% pot)
                size_pct = 66
                reason = "Value hand - Extract value from worse hands (2nd/3rd pair, bluff-catchers)"
            
            elif hand_type == "marginal":
                # Bet pequeño (30-50% pot) o check
                size_pct = 40
                reason = "Marginal hand - Small bet for thin value, easy to fold if raised"
            
            elif hand_type == "air":
                # Bluff: Bet grande (70-100% pot) para max fold equity
                size_pct = 75
                reason = "Bluff - Large bet to maximize fold equity (represents strong hand)"
            
            else:  # bluff_catcher
                size_pct = 0
                reason = "Bluff-catcher - Should CHECK, not bet (no value, no fold equity)"
            
            size_bb = round((self.pot * size_pct / 100) * 2) / 2  # Redondear a 0.5 bb
            
            return {
                "size_pct": size_pct,
                "size_bb": size_bb,
                "reason": reason
            }
        
        elif action == "call":
            # Análisis de MDF (Minimum Defense Frequency) y pot odds
            # Asumimos que villain apostó, necesitamos calcular odds
            
            # Esta es una aproximación, en producción se pasaría el bet de villain
            villain_bet_size = self.pot * 0.75  # Asumir 75% pot bet
            pot_odds = villain_bet_size / (self.pot + villain_bet_size)
            
            # MDF = Pot / (Pot + Bet) - Frecuencia mínima para no ser explotado
            mdf = self.pot / (self.pot + villain_bet_size)
            
            # Determinar si nuestra mano debería llamar
            if hand_type in ["nuts", "value"]:
                should_call = "YES (Consider RAISE)"
            elif hand_type == "marginal":
                should_call = "MAYBE (Depends on villain's bluff frequency)"
            elif hand_type == "bluff_catcher":
                should_call = f"YES if villain can bluff >{pot_odds:.1%}"
            else:  # air
                should_call = "NO (No showdown value)"
            
            return {
                "pot_odds": f"{pot_odds:.1%}",
                "mdf": f"{mdf:.1%}",
                "should_call": should_call,
                "reason": f"Need equity/bluff-catching frequency based on pot odds"
            }
    
    def get_river_advice(self) -> str:
        """
        Genera consejo específico y detallado para river.
        
        Returns:
            String formateado con análisis completo
        """
        hand_type = self.classify_hand_type()
        
        # Analizar patrón del villain
        villain_pattern = self.history.analyze_villain_pattern()
        villain_aggressive = villain_pattern.get('aggression_freq', 0) > 0.5
        villain_showed_weakness = villain_pattern.get('showed_weakness', False)
        
        # SPR (Stack to Pot Ratio)
        spr = self.stack / self.pot if self.pot > 0 else 999
        
        advice = f"""
🎯 RIVER DECISION FRAMEWORK:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 SITUACIÓN:
   Pot: {self.pot} bb
   Stack efectivo: {self.stack} bb
   SPR: {spr:.2f}

🃏 CLASIFICACIÓN DE MANO: {hand_type.upper().replace('_', ' ')}

"""
        
        # RECOMENDACIONES SEGÚN TIPO DE MANO
        if hand_type == "nuts":
            advice += """
✅ ACCIÓN PRINCIPAL: BET/RAISE for VALUE

Razonamiento:
- Tienes la mejor mano (o muy cercana)
- OBJETIVO: Extraer máximo valor

Estrategia:
"""
            sizing = self.recommend_sizing("bet")
            advice += f"""   • SIZING: {sizing['size_pct']}% pot ({sizing['size_bb']} bb)
   • RAZÓN: {sizing['reason']}
   
⚠️ Si villain te raise:
   → CALL o RE-RAISE (tienes nuts, no puedes foldear)

"""
        
        elif hand_type == "value":
            advice += """
✅ ACCIÓN PRINCIPAL: BET for THIN VALUE

Razonamiento:
- Tienes una mano fuerte que beats muchas manos peores
- Villain puede pagar con pairs débiles, draws fallidos convertidos en bluff-catchers

Estrategia:
"""
            sizing = self.recommend_sizing("bet")
            advice += f"""   • SIZING: {sizing['size_pct']}% pot ({sizing['size_bb']} bb)
   • RAZÓN: {sizing['reason']}
   
⚠️ Si villain te raise:
   → Reevaluar - Puede ser bluff o mano mejor
   → Si villain es aggresivo: Considera call
   → Si villain es passive: Probablemente tiene monster → FOLD

"""
        
        elif hand_type == "marginal":
            if spr < 1.5:
                advice += """
⚠️ ACCIÓN PRINCIPAL: BET SMALL o CHECK/CALL

Razonamiento:
- Mano marginal (Top Pair débil o Middle Pair)
- SPR bajo → Pot committed si apostamos mucho

Estrategia:
"""
                sizing = self.recommend_sizing("bet")
                advice += f"""   • SIZING SUGERIDO: {sizing['size_pct']}% pot ({sizing['size_bb']} bb)
   • Alternativa: CHECK/CALL (pot control)
   
Si villain apuesta:
   → SPR bajo = Difficult to fold
   → Considera CALL si es < 50% pot

"""
            else:
                advice += """
⚠️ ACCIÓN PRINCIPAL: CHECK

Razonamiento:
- Mano marginal con SPR alto
- Difícil extraer valor, fácil perder más si villain tiene mejor

Estrategia:
   • CHECK/FOLD si villain apuesta grande
   • CHECK/CALL si villain apuesta pequeño (<33% pot)

"""
        
        elif hand_type == "bluff_catcher":
            if villain_aggressive:
                advice += f"""
🎲 ACCIÓN PRINCIPAL: CHECK (Induce Bluffs)

Razonamiento:
- Tienes bluff-catcher (beats bluffs, lose to value)
- Villain es AGRESIVO ({villain_pattern['aggression_freq']:.0%} aggression) → Puede bluffear

Estrategia:
   • CHECK/CALL si villain apuesta razonablemente
   • Usar pot odds para decidir:
     - Villain bet 75% pot → Necesitas 30% equity (bluff freq > 30%)
   
Patrón de Villain: {villain_pattern['description']}

"""
            else:
                advice += f"""
❌ ACCIÓN PRINCIPAL: CHECK/FOLD

Razonamiento:
- Tienes bluff-catcher
- Villain es PASIVO ({villain_pattern['passive_freq']:.0%} passive) → Rara vez bluffea

Estrategia:
   • CHECK con intención de FOLD si apuesta
   • Si villain checks back → Win at showdown ocasionalmente
   
Patrón de Villain: {villain_pattern['description']}

"""
        
        else:  # air
            fold_equity_analysis = self.history.should_continue_aggression("river")
            
            if villain_showed_weakness and fold_equity_analysis.get("fold_equity_estimate", 0) > 0.35:
                advice += f"""
🎲 ACCIÓN PRINCIPAL: Consider BLUFF

Razonamiento:
- Tienes aire (no showdown value)
- Villain mostró debilidad previamente
- Fold Equity estimada: {fold_equity_analysis['fold_equity_estimate']:.1%}

Estrategia:
"""
                sizing = self.recommend_sizing("bet")
                advice += f"""   • SIZING: {sizing['size_pct']}% pot ({sizing['size_bb']} bb)
   • RAZÓN: {sizing['reason']}
   
⚠️ CONSIDERACIONES:
   - Tu historia (line) debe ser creíble
   - {fold_equity_analysis['reasoning']}
   
Si villain te paga o raise → Has perdido (tenías aire)

"""
            else:
                advice += f"""
❌ ACCIÓN PRINCIPAL: CHECK/FOLD (Give Up)

Razonamiento:
- Tienes aire (no showdown value)
- Fold equity insuficiente: {fold_equity_analysis.get('fold_equity_estimate', 0):.1%}
- Villain no mostró debilidad clara

Estrategia:
   • CHECK con intención de FOLD si apuesta
   • Si villain checks back → Pierdes en showdown
   • SAVE CHIPS para mejores spots

"""
        
        # BLOQUE FINAL: CONCEPTOS CRÍTICOS
        advice += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 CONCEPTOS CRÍTICOS DE RIVER:

1. POLARIZACIÓN:
   - Con nuts o aire → BET GRANDE (75-150% pot)
   - Con manos medias → BET PEQUEÑO (40-60% pot) o CHECK

2. POT CONTROL:
   - Con bluff-catchers → No construyas el pot
   - CHECK para inducir bluffs

3. THIN VALUE:
   - Si villain puede pagar con peor → BET (aunque sea marginal)
   - Ejemplo: Tu Top Pair vs su Middle Pair

4. BLUFF CATCHING:
   - Necesitas que villain bluffee con frecuencia suficiente
   - Formula: Call si Villain_Bluff_Freq > Pot_Odds

5. MDF (Minimum Defense Frequency):
   - Vs 75% pot bet → Debes defender 57% del tiempo
   - No foldees tanto que seas explotable

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        return advice
    
    def get_sizing_table(self) -> str:
        """
        Genera una tabla de referencia de sizings según tipo de mano.
        
        Returns:
            String con tabla formateada
        """
        table = """
┌─────────────────────┬──────────────┬─────────────────────────────────────┐
│ Tipo de Mano        │ Sizing       │ Objetivo                            │
├─────────────────────┼──────────────┼─────────────────────────────────────┤
│ Nuts                │ 75-150% pot  │ Max value (polarized)               │
│ Value (Strong)      │ 60-80% pot   │ Extract value from 2nd best hands   │
│ Marginal (Thin Val) │ 30-50% pot   │ Get called by worse, fold if raised │
│ Bluff-Catcher       │ 0% (CHECK)   │ Induce bluffs, don't build pot      │
│ Air (Bluff)         │ 75-100% pot  │ Max fold equity                     │
└─────────────────────┴──────────────┴─────────────────────────────────────┘
"""
        return table

