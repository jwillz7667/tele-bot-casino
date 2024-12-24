from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from ..game_base import Game, GameResult
from .utils import (
    SlotSymbol, PaylinePattern, MultiplyBonus, FreeSpinsBonus,
    PAYLINE_PATTERNS, load_slot_config
)

class AncientTreasures(Game):
    """
    Ancient Egyptian themed slot game with pyramid bonus features.
    5x3 grid with multiple paylines and special features.
    """
    
    # Define symbols
    SYMBOLS = {
        'ankh': SlotSymbol('☥', 'Ankh', 3),
        'eye': SlotSymbol('👁️', 'Eye of Horus', 4),
        'pyramid': SlotSymbol('🏛️', 'Pyramid', 2),
        'sphinx': SlotSymbol('🗿', 'Sphinx', 2),
        'scarab': SlotSymbol('🪲', 'Scarab', 5),
        'cat': SlotSymbol('😺', 'Bastet', 4),
        'wild': SlotSymbol('⭐', 'Wild', 1),
        'scatter': SlotSymbol('🌟', 'Scatter', 1)
    }
    
    # Winning combinations and their multipliers
    PAYOUTS = {
        3: 5,   # 3 matching symbols
        4: 15,  # 4 matching symbols
        5: 50   # 5 matching symbols
    }
    
    def __init__(self):
        """Initialize the Ancient Treasures slot game."""
        super().__init__(
            game_type="ancient_treasures",
            min_bet=Decimal("1.00"),
            max_bet=Decimal("100.00")
        )
        
        # Initialize bonus features
        self.multiply_bonus = MultiplyBonus(0.1, (2, 5))  # 10% chance, 2-5x multiplier
        self.free_spins_bonus = FreeSpinsBonus(0.05, (3, 10))  # 5% chance, 3-10 free spins
        
        # Game state per player
        self._player_states: Dict[int, Dict[str, Any]] = {}
    
    def _initialize_player_state(self, player_id: int) -> None:
        """Initialize or reset a player's game state."""
        self._player_states[player_id] = {
            'free_spins': 0,
            'multiplier': 1,
            'last_grid': None,
            'bonus_active': False,
            'total_win': Decimal("0")
        }
    
    def _generate_grid(self) -> List[List[SlotSymbol]]:
        """Generate a random 5x3 grid of symbols."""
        grid = []
        for _ in range(3):  # 3 rows
            row = []
            for _ in range(5):  # 5 columns
                # Weighted random selection of symbols
                weights = [s.weight for s in self.SYMBOLS.values()]
                symbol = list(self.SYMBOLS.values())[
                    self.generate_random_int(0, len(self.SYMBOLS) - 1)
                ]
                row.append(symbol)
            grid.append(row)
        return grid
    
    def _check_paylines(
        self,
        grid: List[List[SlotSymbol]]
    ) -> List[Tuple[PaylinePattern, List[SlotSymbol]]]:
        """Check all paylines for winning combinations."""
        winners = []
        for pattern_list in PAYLINE_PATTERNS.values():
            for pattern in pattern_list:
                is_winner, symbols = pattern.check_win(grid)
                if is_winner:
                    winners.append((pattern, symbols))
        return winners
    
    def _calculate_win(
        self,
        winners: List[Tuple[PaylinePattern, List[SlotSymbol]]],
        bet_amount: Decimal,
        player_id: int
    ) -> Tuple[Decimal, str]:
        """Calculate total win amount and generate outcome message."""
        total_win = Decimal("0")
        outcome_parts = []
        
        state = self._player_states[player_id]
        multiplier = state['multiplier']
        
        for pattern, symbols in winners:
            symbol_count = len(symbols)
            if symbol_count >= 3:
                win = bet_amount * self.PAYOUTS[symbol_count] * pattern.multiplier
                win *= multiplier  # Apply any active multiplier
                total_win += win
                outcome_parts.append(
                    f"{pattern.name}: {' '.join(str(s) for s in symbols)} - {win:.2f}"
                )
        
        # Check for bonus triggers
        if self.multiply_bonus.should_trigger(self):
            bonus_win, bonus_msg = self.multiply_bonus.apply_bonus(total_win, self)
            total_win = bonus_win
            outcome_parts.append(bonus_msg)
        
        if self.free_spins_bonus.should_trigger(self):
            free_spins = self.free_spins_bonus.get_free_spins(self)
            state['free_spins'] += free_spins
            outcome_parts.append(f"🎰 Won {free_spins} Free Spins!")
        
        outcome = "\n".join(outcome_parts) if outcome_parts else "No winning combinations"
        return total_win, outcome
    
    async def play(self, player_id: int, bet_amount: Decimal, **kwargs) -> GameResult:
        """
        Play a round of Ancient Treasures slots.
        
        Args:
            player_id: ID of the player
            bet_amount: Amount being bet
            **kwargs: Additional parameters (unused)
            
        Returns:
            GameResult: Result of the slot game
        """
        # Initialize player state if needed
        if player_id not in self._player_states:
            self._initialize_player_state(player_id)
        
        state = self._player_states[player_id]
        is_free_spin = state['free_spins'] > 0
        
        # Generate new grid
        grid = self._generate_grid()
        state['last_grid'] = grid
        
        # Check for winners and calculate winnings
        winners = self._check_paylines(grid)
        win_amount, outcome = self._calculate_win(winners, bet_amount, player_id)
        
        # Update free spins if active
        if is_free_spin:
            state['free_spins'] -= 1
            outcome = f"🎰 Free Spin! {outcome}"
        
        # Update total win
        state['total_win'] += win_amount
        
        return GameResult(
            player_id=player_id,
            game_type=self.game_type,
            bet_amount=Decimal("0") if is_free_spin else bet_amount,
            win_amount=win_amount,
            outcome=outcome,
            game_data={
                "grid": [[str(s) for s in row] for row in grid],
                "free_spins_remaining": state['free_spins'],
                "total_win": state['total_win']
            }
        )
    
    def get_game_rules(self) -> str:
        """Get the rules and payouts for Ancient Treasures slots."""
        rules = (
            "🏛️ *Ancient Treasures Slots*\n\n"
            "*Symbols:*\n"
            "☥ Ankh - High value\n"
            "👁️ Eye of Horus - High value\n"
            "🏛️ Pyramid - Medium value\n"
            "🗿 Sphinx - Medium value\n"
            "🪲 Scarab - Low value\n"
            "😺 Bastet - Low value\n"
            "⭐ Wild - Substitutes any symbol\n"
            "🌟 Scatter - Triggers bonuses\n\n"
            "*Special Features:*\n"
            "- Multiplier Bonus (2x-5x)\n"
            "- Free Spins (3-10 spins)\n"
            "- Multiple paylines\n\n"
            f"Min bet: {self.min_bet}\n"
            f"Max bet: {self.max_bet}"
        )
        return rules
    
    def get_game_state(self, player_id: int) -> Dict[str, Any]:
        """Get the current state of the game for a player."""
        if player_id not in self._player_states:
            self._initialize_player_state(player_id)
        
        state = self._player_states[player_id]
        return {
            "last_grid": state['last_grid'],
            "free_spins": state['free_spins'],
            "multiplier": state['multiplier'],
            "total_win": state['total_win'],
            "min_bet": self.min_bet,
            "max_bet": self.max_bet
        } 