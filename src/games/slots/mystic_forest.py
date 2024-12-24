from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple, Set
from ..game_base import Game, GameResult
from .utils import (
    SlotSymbol, PaylinePattern, MultiplyBonus, ReskinBonus,
    PAYLINE_PATTERNS, load_slot_config
)

class GrowingWild:
    """Class representing a growing wild feature."""
    
    def __init__(self, position: Tuple[int, int]):
        self.position = position
        self.size = 1  # Starts as 1x1
        self.growth_direction = None  # Will be randomly chosen
    
    def get_covered_positions(self) -> Set[Tuple[int, int]]:
        """Get all positions covered by this wild."""
        positions = {self.position}
        row, col = self.position
        
        if self.growth_direction == 'vertical':
            for i in range(1, self.size):
                if row + i < 3:  # Stay within grid bounds
                    positions.add((row + i, col))
        elif self.growth_direction == 'horizontal':
            for i in range(1, self.size):
                if col + i < 5:  # Stay within grid bounds
                    positions.add((row, col + i))
        elif self.growth_direction == 'both':
            for i in range(1, self.size):
                if row + i < 3:
                    positions.add((row + i, col))
                if col + i < 5:
                    positions.add((row, col + i))
        
        return positions

class MysticForest(Game):
    """
    Nature-themed slot game with transforming symbols and growing wilds.
    Features dynamic symbol transformations and expanding wild symbols.
    """
    
    # Define symbols with nature theme
    SYMBOLS = {
        'tree': SlotSymbol('🌳', 'Ancient Tree', 3),
        'flower': SlotSymbol('🌸', 'Magic Flower', 4),
        'mushroom': SlotSymbol('🍄', 'Mystic Mushroom', 2),
        'leaf': SlotSymbol('🍃', 'Enchanted Leaf', 5),
        'butterfly': SlotSymbol('🦋', 'Spirit Butterfly', 4),
        'deer': SlotSymbol('🦌', 'Forest Guardian', 3),
        'crystal': SlotSymbol('💎', 'Nature Crystal', 1),  # Wild
        'moon': SlotSymbol('🌕', 'Full Moon', 1)  # Scatter
    }
    
    # Symbol transformation chains
    TRANSFORMATIONS = {
        'leaf': 'flower',      # Leaves transform into flowers
        'flower': 'tree',      # Flowers grow into trees
        'mushroom': 'crystal'  # Mushrooms become crystals
    }
    
    # Winning combinations and their multipliers
    PAYOUTS = {
        3: 4,    # 3 matching symbols
        4: 10,   # 4 matching symbols
        5: 25,   # 5 matching symbols
        6: 50,   # 6 matching symbols (possible with growing wilds)
        7: 100   # 7 matching symbols (maximum with growing wilds)
    }
    
    def __init__(self):
        """Initialize the Mystic Forest slot game."""
        super().__init__(
            game_type="mystic_forest",
            min_bet=Decimal("1.00"),
            max_bet=Decimal("150.00")
        )
        
        # Initialize bonus features
        self.multiply_bonus = MultiplyBonus(0.15, (2, 6))  # 15% chance, 2-6x multiplier
        self.reskin_bonus = ReskinBonus(0.1, 4)  # 10% chance, lasts 4 spins
        
        # Game state per player
        self._player_states: Dict[int, Dict[str, Any]] = {}
    
    def _initialize_player_state(self, player_id: int) -> None:
        """Initialize or reset a player's game state."""
        self._player_states[player_id] = {
            'growing_wilds': [],  # List of active growing wilds
            'transformed_positions': set(),  # Positions with transformed symbols
            'reskin_spins': 0,
            'last_grid': None,
            'total_win': Decimal("0"),
            'bonus_multiplier': 1
        }
    
    def _generate_grid(self) -> List[List[SlotSymbol]]:
        """Generate a random 5x3 grid of symbols."""
        grid = []
        for _ in range(3):  # 3 rows
            row = []
            for _ in range(5):  # 5 columns
                weights = [s.weight for s in self.SYMBOLS.values()]
                symbol = list(self.SYMBOLS.values())[
                    self.generate_random_int(0, len(self.SYMBOLS) - 1)
                ]
                row.append(symbol)
            grid.append(row)
        return grid
    
    def _handle_transformations(
        self,
        grid: List[List[SlotSymbol]],
        state: Dict[str, Any]
    ) -> Tuple[List[List[SlotSymbol]], List[str]]:
        """
        Handle symbol transformations.
        
        Args:
            grid: Current grid state
            state: Player's game state
            
        Returns:
            Tuple[List[List[SlotSymbol]], List[str]]: (transformed grid, transformation messages)
        """
        messages = []
        transformed = set()
        
        # Check each position for possible transformations
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                symbol = grid[row][col]
                if str(symbol) in self.TRANSFORMATIONS and (row, col) not in state['transformed_positions']:
                    # 20% chance to transform
                    if self.generate_random_float() < 0.2:
                        new_symbol = self.SYMBOLS[self.TRANSFORMATIONS[str(symbol)]]
                        grid[row][col] = new_symbol
                        transformed.add((row, col))
                        messages.append(
                            f"✨ {symbol} transformed into {new_symbol} at position ({row+1}, {col+1})"
                        )
        
        state['transformed_positions'].update(transformed)
        return grid, messages
    
    def _handle_growing_wilds(
        self,
        grid: List[List[SlotSymbol]],
        state: Dict[str, Any]
    ) -> Tuple[List[List[SlotSymbol]], List[str]]:
        """
        Handle growing wild symbols.
        
        Args:
            grid: Current grid state
            state: Player's game state
            
        Returns:
            Tuple[List[List[SlotSymbol]], List[str]]: (modified grid, wild messages)
        """
        messages = []
        crystal = self.SYMBOLS['crystal']
        
        # Check for new wild symbols
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                if grid[row][col] == crystal and not any(
                    (row, col) in wild.get_covered_positions()
                    for wild in state['growing_wilds']
                ):
                    # 30% chance to become a growing wild
                    if self.generate_random_float() < 0.3:
                        new_wild = GrowingWild((row, col))
                        directions = ['vertical', 'horizontal', 'both']
                        new_wild.growth_direction = directions[
                            self.generate_random_int(0, len(directions) - 1)
                        ]
                        state['growing_wilds'].append(new_wild)
                        messages.append(
                            f"🌟 Growing Wild appeared at position ({row+1}, {col+1})"
                        )
        
        # Grow existing wilds
        for wild in state['growing_wilds']:
            if wild.size < 3 and self.generate_random_float() < 0.4:  # 40% chance to grow
                wild.size += 1
                messages.append(
                    f"🌱 Growing Wild at ({wild.position[0]+1}, {wild.position[1]+1}) "
                    f"expanded to size {wild.size}"
                )
        
        # Apply wilds to grid
        for wild in state['growing_wilds']:
            for pos in wild.get_covered_positions():
                row, col = pos
                grid[row][col] = crystal
        
        return grid, messages
    
    async def play(self, player_id: int, bet_amount: Decimal, **kwargs) -> GameResult:
        """
        Play a round of Mystic Forest slots.
        
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
        grid = self._generate_grid()
        
        # Handle transformations
        grid, transform_messages = self._handle_transformations(grid, state)
        
        # Handle growing wilds
        grid, wild_messages = self._handle_growing_wilds(grid, state)
        
        # Check for winners and calculate winnings
        winners = self._check_paylines(grid)
        win_amount, win_messages = self._calculate_win(winners, bet_amount, state)
        
        # Combine all messages
        all_messages = transform_messages + wild_messages + win_messages
        outcome = "\n".join(all_messages) if all_messages else "No winning combinations"
        
        # Update state
        state['last_grid'] = grid
        state['total_win'] += win_amount
        
        # Clean up old growing wilds (25% chance each)
        state['growing_wilds'] = [
            wild for wild in state['growing_wilds']
            if self.generate_random_float() > 0.25
        ]
        
        return GameResult(
            player_id=player_id,
            game_type=self.game_type,
            bet_amount=bet_amount,
            win_amount=win_amount,
            outcome=outcome,
            game_data={
                "grid": [[str(s) for s in row] for row in grid],
                "growing_wilds": len(state['growing_wilds']),
                "transformed_positions": len(state['transformed_positions']),
                "total_win": state['total_win']
            }
        )
    
    def get_game_rules(self) -> str:
        """Get the rules and payouts for Mystic Forest slots."""
        rules = (
            "🌳 *Mystic Forest Slots*\n\n"
            "*Symbols:*\n"
            "🌳 Ancient Tree - High value\n"
            "🌸 Magic Flower - High value\n"
            "🍄 Mystic Mushroom - Medium value\n"
            "🍃 Enchanted Leaf - Medium value\n"
            "🦋 Spirit Butterfly - Low value\n"
            "🦌 Forest Guardian - Low value\n"
            "💎 Nature Crystal - Wild symbol\n"
            "🌕 Full Moon - Scatter\n\n"
            "*Special Features:*\n"
            "- Symbol Transformations\n"
            "- Growing Wilds (up to 3x3)\n"
            "- Multiple Growth Directions\n"
            "- Dynamic Paylines\n\n"
            "*Transformations:*\n"
            "🍃 → 🌸 → 🌳 (Leaf to Tree)\n"
            "🍄 → 💎 (Mushroom to Crystal)\n\n"
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
            "growing_wilds": len(state['growing_wilds']),
            "transformed_positions": len(state['transformed_positions']),
            "total_win": state['total_win'],
            "min_bet": self.min_bet,
            "max_bet": self.max_bet
        } 