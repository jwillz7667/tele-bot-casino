from typing import List, Dict, Tuple, Any
from decimal import Decimal
import json
import os
from pathlib import Path

class SlotSymbol:
    """Class representing a slot machine symbol with its properties."""
    
    def __init__(self, emoji: str, name: str, weight: int = 1):
        self.emoji = emoji
        self.name = name
        self.weight = weight
    
    def __str__(self) -> str:
        return self.emoji
    
    def __eq__(self, other) -> bool:
        if isinstance(other, SlotSymbol):
            return self.emoji == other.emoji
        return False
    
    def __hash__(self) -> int:
        return hash(self.emoji)

class PaylinePattern:
    """Class representing a winning payline pattern."""
    
    def __init__(self, name: str, positions: List[Tuple[int, int]], multiplier: int):
        """
        Initialize a payline pattern.
        
        Args:
            name: Name of the pattern
            positions: List of (row, col) positions forming the pattern
            multiplier: Base multiplier for this pattern
        """
        self.name = name
        self.positions = positions
        self.multiplier = multiplier
    
    def check_win(self, grid: List[List[SlotSymbol]]) -> Tuple[bool, List[SlotSymbol]]:
        """
        Check if this payline is a winner.
        
        Args:
            grid: The slot grid to check
            
        Returns:
            Tuple[bool, List[SlotSymbol]]: (is_winner, symbols_in_payline)
        """
        symbols = []
        for row, col in self.positions:
            if 0 <= row < len(grid) and 0 <= col < len(grid[0]):
                symbols.append(grid[row][col])
            else:
                return False, []
        
        # Check if all symbols in the payline are the same
        return len(set(symbols)) == 1, symbols

def load_slot_config(game_name: str) -> Dict[str, Any]:
    """
    Load slot configuration from JSON file.
    
    Args:
        game_name: Name of the slot game
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    config_path = Path(__file__).parent / "configs" / f"{game_name}.json"
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise ValueError(f"Error loading slot config for {game_name}: {str(e)}")

# Common payline patterns
PAYLINE_PATTERNS = {
    "horizontal": [
        PaylinePattern("Top Row", [(0, i) for i in range(5)], 1),
        PaylinePattern("Middle Row", [(1, i) for i in range(5)], 1),
        PaylinePattern("Bottom Row", [(2, i) for i in range(5)], 1)
    ],
    "diagonal": [
        PaylinePattern("Diagonal Down", [(i, i) for i in range(5)], 2),
        PaylinePattern("Diagonal Up", [(2-i, i) for i in range(3)], 2)
    ],
    "zigzag": [
        PaylinePattern("Zigzag", [(1,0), (0,1), (1,2), (2,3), (1,4)], 3)
    ]
}

# Common bonus features
class BonusFeature:
    """Base class for bonus features in slot games."""
    
    def __init__(self, trigger_probability: float):
        self.trigger_probability = trigger_probability
    
    def should_trigger(self, rng) -> bool:
        """Check if bonus should trigger based on RNG."""
        return rng.generate_random_float() < self.trigger_probability
    
    def apply_bonus(self, base_win: Decimal) -> Tuple[Decimal, str]:
        """
        Apply bonus to base win amount.
        
        Args:
            base_win: Base winning amount
            
        Returns:
            Tuple[Decimal, str]: (modified_win_amount, bonus_description)
        """
        return base_win, "No bonus applied"

class MultiplyBonus(BonusFeature):
    """Multiplies winnings by a random factor."""
    
    def __init__(self, trigger_probability: float, multiplier_range: Tuple[int, int]):
        super().__init__(trigger_probability)
        self.min_mult, self.max_mult = multiplier_range
    
    def apply_bonus(self, base_win: Decimal, rng) -> Tuple[Decimal, str]:
        multiplier = rng.generate_random_int(self.min_mult, self.max_mult)
        return base_win * multiplier, f"🎉 {multiplier}x Multiplier Bonus!"

class FreeSpinsBonus(BonusFeature):
    """Awards free spins with potential multipliers."""
    
    def __init__(self, trigger_probability: float, spins_range: Tuple[int, int]):
        super().__init__(trigger_probability)
        self.min_spins, self.max_spins = spins_range
    
    def get_free_spins(self, rng) -> int:
        """Get number of free spins awarded."""
        return rng.generate_random_int(self.min_spins, self.max_spins)

class ReskinBonus(BonusFeature):
    """Temporarily changes symbols to higher-value ones."""
    
    def __init__(self, trigger_probability: float, duration: int):
        super().__init__(trigger_probability)
        self.duration = duration  # Number of spins the reskin lasts
    
    def get_reskin_duration(self) -> int:
        """Get duration of reskin bonus."""
        return self.duration 