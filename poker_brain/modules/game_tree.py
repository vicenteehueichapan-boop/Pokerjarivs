from typing import List, Optional
from dataclasses import dataclass
from ..model import GameContext, Decision

@dataclass
class Node:
    action_type: str # "CHECK", "BET", "FOLD"
    amount: float
    ev: float = 0.0
    children: List['Node'] = None

class GameTree:
    """
    A simplified search tree for looking ahead 1 street.
    """
    def __init__(self):
        pass

    def generate_candidate_actions(self, context: GameContext) -> List[Decision]:
        """
        Generates a list of possible root actions for the Hero.
        """
        candidates = []

        amount_to_call = context.current_bet - context.hero.current_investment

        # 1. Fold (always an option if facing bet)
        if amount_to_call > 0:
            candidates.append(Decision(action="FOLD", amount=0))

        # 2. Check/Call
        if amount_to_call == 0:
            candidates.append(Decision(action="CHECK", amount=0))
        else:
            candidates.append(Decision(action="CALL", amount=amount_to_call))

        # 3. Raise / Bet (Small, Medium, All-in)
        # Only if we have stack
        min_raise = max(context.current_bet * 2, 2.0) # Simplified min raise rule
        if context.hero.stack > min_raise:
            # Bet Sizing Strategies
            pot = context.pot_size

            sizes = [0.33, 0.66, 1.0] # 1/3 pot, 2/3 pot, Pot

            for s in sizes:
                amt = pot * s
                if amt >= min_raise and amt < context.hero.stack:
                    candidates.append(Decision(action="RAISE", amount=amt))

            # All-in
            candidates.append(Decision(action="ALLIN", amount=context.hero.stack))

        return candidates

    def evaluate_node(self, decision: Decision, context: GameContext, equity: float) -> float:
        """
        Assigns an EV to a decision node based on immediate info.
        For a full tree, we would recursively evaluate children.
        """
        # Simple EV Calculation (same as StrategyEngine MVP but structured)

        amount_to_call = context.current_bet - context.hero.current_investment
        pot_total = context.pot_size

        if decision.action == "FOLD":
            return 0.0 # EV of folding is 0 relative to current state (money in pot is sunk cost)

        if decision.action == "CALL" or decision.action == "CHECK":
            # EV = (Win% * FinalPot) - Cost
            # If we check, Cost is 0.
            cost = decision.amount
            final_pot = pot_total + cost + (cost if context.current_bet > 0 else 0) # Assumes villain matched or we match villain
            # Actually, Pot Odds formula is simpler:
            # EV = (Equity * (Pot + VillainBet + HeroCall)) - HeroCall

            # Let's be precise:
            # Pot currently has P. Villain bets B. Hero calls B. Total pot P+B+B.
            # Hero puts in B.
            # EV = Equity * (P + 2B) - B

            # Using the inputs:
            # context.pot_size includes everything committed so far?
            # Standard: pot_size usually includes bets on table.
            # Let's assume pot_size is EVERYTHING in the middle.
            # So if we Call X:
            # Final Pot = pot_size + X
            # EV = (Equity * FinalPot) - X

            final_pot = pot_total + decision.amount
            return (equity * final_pot) - decision.amount

        if decision.action == "RAISE" or decision.action == "ALLIN":
            # Fold Equity becomes important here.
            # EV = (%VillainFolds * PotNow) + (%VillainCalls * EV_of_Call)

            # Simple assumption for MVP Tree:
            # Villain folds 40% of time to a raise?
            fold_prob = 0.4
            # If we are very strong, maybe they fold less?
            # Or if we bet huge?

            # Heuristic Fold Equity
            bet_size_ratio = decision.amount / pot_total
            if bet_size_ratio > 1.0: fold_prob = 0.6
            elif bet_size_ratio < 0.4: fold_prob = 0.2

            ev_when_called = (equity * (pot_total + decision.amount + decision.amount)) - decision.amount

            ev = (fold_prob * pot_total) + ((1 - fold_prob) * ev_when_called)
            return ev

        return 0.0
