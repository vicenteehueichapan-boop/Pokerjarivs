import random
from treys import Card, Deck, Evaluator
from .model import GameContext, Decision, ActionType
from .evaluator import HandEvaluator

class StrategyEngine:
    def __init__(self):
        self.evaluator = HandEvaluator()

    def calculate_pot_odds(self, to_call: float, pot_total: float) -> float:
        """
        Calculates pot odds.
        Pot Odds = Amount To Call / (Total Pot + Amount To Call)
        Returns a float between 0 and 1.
        """
        if to_call <= 0:
            return 0.0
        return to_call / (pot_total + to_call)

    def estimate_equity(self, hero_hand: list[str], board: list[str], simulations=1000) -> float:
        """
        Estimates equity by simulating the remaining streets against a random hand.
        For a more advanced bot, we would simulate against a specific RANGE of hands.
        For this MVP, we simulate against a random hand (2 random cards).
        """
        # Convert hero cards and board to treys format
        hero_cards_int = [Card.new(c) for c in hero_hand]
        board_cards_int = [Card.new(c) for c in board]

        wins = 0
        ties = 0

        # Simple Monte Carlo
        for _ in range(simulations):
            deck = Deck()

            # Remove known cards from deck
            known_cards = hero_cards_int + board_cards_int
            # Treys Deck object handles removal if we draw, but to be safe/explicit:
            # We can't easily remove specific cards from treys.Deck without drawing them.
            # So we just draw until we get valid cards.
            # Efficient way: Get all cards, remove known, shuffle rest.

            # Actually, let's just use the Deck.draw() method and retry if collision (inefficient but simple)
            # OR better: Construct deck manually excluding known cards.

            full_deck = deck.GetFullDeck() # returns list of ints
            remaining_deck = [c for c in full_deck if c not in known_cards]
            random.shuffle(remaining_deck)

            # Villain Hand
            villain_hand = [remaining_deck.pop(), remaining_deck.pop()]

            # Run out the board
            # If flop (3 cards), we need turn and river (2 more)
            cards_needed = 5 - len(board_cards_int)
            runout = []
            if cards_needed > 0:
                for _ in range(cards_needed):
                    runout.append(remaining_deck.pop())

            final_board = board_cards_int + runout

            hero_score = self.evaluator.evaluator.evaluate(final_board, hero_cards_int)
            villain_score = self.evaluator.evaluator.evaluate(final_board, villain_hand)

            if hero_score < villain_score: # Lower is better in Treys
                wins += 1
            elif hero_score == villain_score:
                ties += 1

        equity = (wins + (ties * 0.5)) / simulations
        return equity

    def make_decision(self, context: GameContext) -> Decision:
        """
        Core decision logic.
        """
        # 1. Calculate Amount needed to Call
        # We need to look at context.current_bet vs hero.current_investment
        # The 'current_bet' in context usually means "the highest bet currently on the table for this street".
        # So amount_to_call = context.current_bet - context.hero.current_investment

        amount_to_call = context.current_bet - context.hero.current_investment
        if amount_to_call < 0: amount_to_call = 0 # Should not happen unless data error

        # 2. Check if we can check
        can_check = (amount_to_call <= 0)

        # 3. Calculate Pot Odds
        # Pot size includes money already in middle.
        # We need to add villain's current bets if they aren't fully in 'pot_size' yet depending on data source,
        # but usually 'pot_size' + 'current bets not swept' is the total.
        # Let's assume context.pot_size is the TOTAL pot including all current bets.
        pot_odds = self.calculate_pot_odds(amount_to_call, context.pot_size)

        # 4. Calculate Equity
        # Only if we have cards.
        equity = 0.0
        if context.hero.cards:
            if context.street == "PREFLOP":
                # Preflop simulation is slow. We might want a lookup table.
                # For MVP, we'll just run a smaller sim or use a high-card heuristic.
                # Let's run a small sim (500 iter) for preflop
                equity = self.estimate_equity(context.hero.cards, context.board, simulations=400)
            else:
                equity = self.estimate_equity(context.hero.cards, context.board, simulations=1000)

        # 5. Logic

        # EV Formula:
        # EV = (Equity * TotalPotAfterCall) - AmountToCall
        # If EV > 0, Call is profitable (ignoring implied odds and reverse implied odds).

        total_pot_after_call = context.pot_size + amount_to_call
        ev_call = (equity * total_pot_after_call) - amount_to_call

        reasoning = f"Equity: {equity:.2f}, Pot Odds: {pot_odds:.2f}, EV Call: {ev_call:.2f}"

        # Basic Strategy
        if can_check:
            # If we can check, we check unless we have very strong hand -> Bet
            # Bet if Equity > 0.7 (Value bet)
            if equity > 0.7:
                 # Bet sizing: 50% pot
                 bet_amount = context.pot_size * 0.5
                 # Ensure we don't bet more than stack
                 bet_amount = min(bet_amount, context.hero.stack)
                 return Decision(action="RAISE", amount=bet_amount, reasoning=f"Value Bet. {reasoning}", ev_estimation=ev_call)
            return Decision(action="CHECK", amount=0, reasoning=f"Checking weak/medium hand. {reasoning}", ev_estimation=ev_call)

        else:
            # Facing a bet
            if ev_call > 0:
                # If very strong, Raise
                if equity > 0.85: # Monster
                     raise_amount = amount_to_call * 3 # 3x raise
                     raise_amount = min(raise_amount, context.hero.stack)
                     return Decision(action="RAISE", amount=raise_amount, reasoning=f"Monster hand raise. {reasoning}", ev_estimation=ev_call)

                return Decision(action="CALL", amount=amount_to_call, reasoning=f"Positive EV Call. {reasoning}", ev_estimation=ev_call)
            else:
                # Negative EV to call -> Fold
                return Decision(action="FOLD", amount=0, reasoning=f"Negative EV Call. {reasoning}", ev_estimation=ev_call)
