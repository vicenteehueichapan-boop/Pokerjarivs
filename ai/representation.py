# import torch
# Commented out to avoid dependency issues in this env, but defining structure.
import numpy as np

class PokerStateEncoder:
    """
    Encodes the poker game state into a Tensor for Deep Learning models (AlphaHoldem style).
    Shape: (Batch, Channels, Ranks, Suits) -> (B, C, 4, 13)
    """

    def __init__(self):
        self.num_ranks = 13
        self.num_suits = 4
        # Channels:
        # 0-1: Hero Cards (2 cards)
        # 2-4: Board Cards (Flop, Turn, River)
        # 5-X: Betting History / Pot Size representation
        self.num_channels = 8

    def encode_state(self, hero_cards: list, board_cards: list, pot_size: float) -> np.ndarray:
        """
        Input:
          hero_cards: List of tuples (rank_idx, suit_idx)
          board_cards: List of tuples
          pot_size: Normalized pot size (0-1)

        Output:
          Numpy array of shape (8, 4, 13)
        """
        tensor = np.zeros((self.num_channels, self.num_suits, self.num_ranks), dtype=np.float32)

        # Channel 0: Hero Card 1
        if len(hero_cards) > 0:
            r, s = hero_cards[0]
            tensor[0, s, r] = 1.0

        # Channel 1: Hero Card 2
        if len(hero_cards) > 1:
            r, s = hero_cards[1]
            tensor[1, s, r] = 1.0

        # Channel 2: Flop
        for i in range(min(3, len(board_cards))):
            r, s = board_cards[i]
            tensor[2, s, r] = 1.0

        # Channel 3: Turn
        if len(board_cards) >= 4:
            r, s = board_cards[3]
            tensor[3, s, r] = 1.0

        # Channel 4: River
        if len(board_cards) >= 5:
            r, s = board_cards[4]
            tensor[4, s, r] = 1.0

        # Channel 5: Pot Size (Spatial Filling or Plane)
        # Fill the entire channel with the scalar value
        tensor[5, :, :] = pot_size

        return tensor

# Example Usage:
# encoder = PokerStateEncoder()
# tensor = encoder.encode_state([(12, 0), (12, 1)], [(10, 2), (9, 2), (8, 2)], 0.5)
