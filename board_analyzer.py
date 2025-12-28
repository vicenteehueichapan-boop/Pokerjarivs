from typing import List
from collections import Counter

class BoardAnalyzer:
    """
    Analiza la textura del board (Rainbow, Monotone, Paired, etc.)
    Independiente del motor C# para enriquecer el contexto rápidamente.
    """

    @staticmethod
    def analyze_texture(board: List[str]) -> str:
        """
        Retorna una descripción textual del board.
        Ej: "Rainbow Paired High"
        """
        if not board:
            return "Unknown"

        # Separar rangos y palos
        ranks = [card[:-1] for card in board]
        suits = [card[-1] for card in board]
        
        features = []

        # 1. Análisis de Palos (Tone)
        suit_counts = Counter(suits).values()
        max_suit = max(suit_counts) if suit_counts else 0
        
        if max_suit >= 4:
            features.append("Monotone/4-Flush")
        elif max_suit == 3:
            features.append("3-Tone (Flush Possible)")
        elif max_suit == 2:
            features.append("2-Tone")
        else:
            features.append("Rainbow")

        # 2. Análisis de Rangos (Paired/Trips)
        rank_counts = Counter(ranks).values()
        max_rank_count = max(rank_counts) if rank_counts else 0
        pairs_count = list(rank_counts).count(2)

        if max_rank_count == 4:
            features.append("Quads")
        elif max_rank_count == 3:
            if pairs_count >= 1: # Full house on board
                 features.append("Full House")
            else:
                features.append("Trips")
        elif max_rank_count == 2:
            if pairs_count >= 2:
                features.append("Double Paired")
            else:
                features.append("Paired")
        else:
            features.append("Unpaired")

        # 3. Conectividad (Basic Check)
        # Convertir rangos a valores numéricos
        values = sorted([BoardAnalyzer._rank_to_int(r) for r in ranks])
        gaps = 0
        connected_cards = 0
        
        # Check simple connectivity (3+ cards in sequence)
        # Lógica simplificada
        if len(values) >= 3:
            seq_count = 1
            max_seq = 1
            for i in range(len(values)-1):
                if values[i+1] == values[i] + 1:
                    seq_count += 1
                elif values[i+1] != values[i]:
                    max_seq = max(max_seq, seq_count)
                    seq_count = 1
            max_seq = max(max_seq, seq_count)
            
            if max_seq >= 4:
                 features.append("4-Straight")
            elif max_seq == 3:
                 features.append("Connected")
            else:
                 features.append("Dry")
        
        return " ".join(features)

    @staticmethod
    def _rank_to_int(rank: str) -> int:
        mapping = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
            'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
        }
        return mapping.get(rank, 0)

