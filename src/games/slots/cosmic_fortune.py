from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from ..game_base import Game, GameResult
from .utils import (
    SlotSymbol, PaylinePattern, MultiplyBonus, ReskinBonus,
    PAYLINE_PATTERNS, load_slot_config
)

class CosmicFortune(Game):
    """
    Space-themed slot game with expanding reels and cascading wins.
    Features a unique expanding grid system and gravity-based symbol drops.
    """
    
    # Define symbols with space theme
    SYMBOLS = {
        'planet': SlotSymbol('🪐', 'Planet', 3),
        'star': SlotSymbol('⭐', 'Star', 4),
        'rocket': SlotSymbol('🚀', 'Rocket', 2),
        'alien': SlotSymbol('👾', 'Alien', 2),
        'satellite': SlotSymbol('🛸', 'Satellite', 5),
        'comet': SlotSymbol('☄️', 'Comet', 4),
        'blackhole': SlotSymbol('🌌', 'Black Hole', 1),  # Wild
        'galaxy': SlotSymbol('🌠', 'Galaxy', 1)  # Scatter
    }
    
    # Base payouts for different grid sizes
    BASE_PAYOUTS = {
        'normal': {3: 3, 4: 8, 5: 15},      # 5x3 grid
        'expanded': {3: 5, 4: 12, 5: 25},    # 5x4 grid
        'mega': {3: 8, 4: 18, 5: 40}         # 5x5 grid
    }
    
    def __init__(self):
        """Initialize the Cosmic Fortune slot game."""
        super().__init__(
            game_type="cosmic_fortune",
            min_bet=Decimal("1.00"),
            max_bet=Decimal("200.00")
        )
        
        # Initialize bonus features
        self.reskin_bonus = ReskinBonus(0.08, 3)  # 8% chance, lasts 3 spins
        self.multiply_bonus = MultiplyBonus(0.12, (2, 8))  # 12% chance, 2-8x multiplier
        
        # Game state per player
        self._player_states: Dict[int, Dict[str, Any]] = {}
    
    def _initialize_player_state(self, player_id: int) -> None:
        """Initialize or reset a player's game state."""
        self._player_states[player_id] = {
            'grid_size': 3,  # Start with 3 rows
            'cascade_multiplier': 1,
            'reskin_spins': 0,
            'last_grid': None,
            'total_win': Decimal("0"),
            'consecutive_wins': 0
        }
    
    def _generate_grid(self, rows: int) -> List[List[SlotSymbol]]:
        """
        Generate a random grid with specified number of rows.
        
        Args:
            rows: Number of rows in the grid
        """
        grid = []
        for _ in range(rows):
            row = []
            for _ in range(5):  # Always 5 columns
                weights = [s.weight for s in self.SYMBOLS.values()]
                symbol = list(self.SYMBOLS.values())[
                    self.generate_random_int(0, len(self.SYMBOLS) - 1)
                ]
                row.append(symbol)
            grid.append(row)
        return grid
    
    def _apply_gravity(self, grid: List[List[SlotSymbol]]) -> List[List[SlotSymbol]]:
        """
        Apply gravity to make symbols fall into empty spaces.
        
        Args:
            grid: Current grid state
            
        Returns:
            List[List[SlotSymbol]]: Grid after gravity applied
        """
        rows, cols = len(grid), len(grid[0])
        new_grid = [[None for _ in range(cols)] for _ in range(rows)]
        
        for col in range(cols):
            write_pos = rows - 1
            for row in range(rows - 1, -1, -1):
                if grid[row][col] is not None:
                    new_grid[write_pos][col] = grid[row][col]
                    write_pos -= 1
        
        return new_grid
    
    def _handle_cascading_wins(
        self,
        grid: List[List[SlotSymbol]],
        bet_amount: Decimal,
        state: Dict[str, Any]
    ) -> Tuple[Decimal, str, List[List[SlotSymbol]]]:
        """
        Handle cascading wins mechanic.
        
        Args:
            grid: Current grid state
            bet_amount: Current bet amount
            state: Player's game state
            
        Returns:
            Tuple[Decimal, str, List[List[SlotSymbol]]]: (total_win, outcome, final_grid)
        """
        total_win = Decimal("0")
        outcome_parts = []
        current_grid = grid
        cascade_count = 0
        
        while True:
            # Check for winners
            winners = self._check_paylines(current_grid)
            if not winners:
                break
                
            # Calculate wins with increasing multiplier
            cascade_multiplier = 1 + (cascade_count * 0.5)  # Increases by 50% each cascade
            win_amount = self._calculate_win_amount(
                winners, bet_amount, state, cascade_multiplier
            )
            total_win += win_amount
            
            outcome_parts.append(
                f"Cascade {cascade_count + 1}: {win_amount:.2f} "
                f"(x{cascade_multiplier:.1f} multiplier)"
            )
            
            # Remove winning symbols and apply gravity
            current_grid = self._remove_winning_symbols(current_grid, winners)
            current_grid = self._apply_gravity(current_grid)
            
            # Fill empty spaces
            current_grid = self._fill_empty_spaces(current_grid)
            
            cascade_count += 1
            if cascade_count >= 5:  # Maximum 5 cascades
                break
        
        outcome = "\n".join(outcome_parts) if outcome_parts else "No winning combinations"
        return total_win, outcome, current_grid
    
    def _calculate_win_amount(
        self,
        winners: List[Tuple[PaylinePattern, List[SlotSymbol]]],
        bet_amount: Decimal,
        state: Dict[str, Any],
        cascade_multiplier: float = 1.0
    ) -> Decimal:
        """Calculate win amount for current winners."""
        grid_size = 'normal' if state['grid_size'] == 3 else (
            'expanded' if state['grid_size'] == 4 else 'mega'
        )
        
        total_win = Decimal("0")
        for pattern, symbols in winners:
            symbol_count = len(symbols)
            if symbol_count >= 3:
                win = (
                    bet_amount *
                    self.BASE_PAYOUTS[grid_size][symbol_count] *
                    pattern.multiplier *
                    Decimal(str(cascade_multiplier))
                )
                total_win += win
        
        return total_win
    
    async def play(self, player_id: int, bet_amount: Decimal, **kwargs) -> GameResult:
        """
        Play a round of Cosmic Fortune slots.
        
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
        
        # Generate initial grid
        grid = self._generate_grid(state['grid_size'])
        
        # Handle cascading wins
        total_win, outcome, final_grid = self._handle_cascading_wins(
            grid, bet_amount, state
        )
        
        # Update state based on win
        if total_win > Decimal("0"):
            state['consecutive_wins'] += 1
            if state['consecutive_wins'] >= 3 and state['grid_size'] < 5:
                state['grid_size'] += 1
                outcome += f"\n🚀 Grid expanded to {state['grid_size']} rows!"
        else:
            state['consecutive_wins'] = 0
            if state['grid_size'] > 3:
                state['grid_size'] -= 1
        
        # Store final state
        state['last_grid'] = final_grid
        state['total_win'] += total_win
        
        return GameResult(
            player_id=player_id,
            game_type=self.game_type,
            bet_amount=bet_amount,
            win_amount=total_win,
            outcome=outcome,
            game_data={
                "grid": [[str(s) for s in row] for row in final_grid],
                "grid_size": state['grid_size'],
                "consecutive_wins": state['consecutive_wins'],
                "total_win": state['total_win']
            }
        )
    
    def get_game_rules(self) -> str:
        """Get the rules and payouts for Cosmic Fortune slots."""
        rules = (
            "🚀 *Cosmic Fortune Slots*\n\n"
            "*Symbols:*\n"
            "🪐 Planet - High value\n"
            "⭐ Star - High value\n"
            "🚀 Rocket - Medium value\n"
            "👾 Alien - Medium value\n"
            "🛸 Satellite - Low value\n"
            "☄️ Comet - Low value\n"
            "🌌 Black Hole - Wild symbol\n"
            "🌠 Galaxy - Scatter\n\n"
            "*Special Features:*\n"
            "- Cascading Wins\n"
            "- Expanding Grid (up to 5x5)\n"
            "- Increasing Multipliers\n"
            "- Consecutive Win Bonuses\n\n"
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
            "grid_size": state['grid_size'],
            "consecutive_wins": state['consecutive_wins'],
            "total_win": state['total_win'],
            "min_bet": self.min_bet,
            "max_bet": self.max_bet
        } 