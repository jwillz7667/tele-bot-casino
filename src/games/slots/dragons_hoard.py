from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from ..game_base import Game, GameResult
from .utils import (
    SlotSymbol, PaylinePattern, MultiplyBonus,
    PAYLINE_PATTERNS, load_slot_config
)

class JackpotTier:
    """Class representing a progressive jackpot tier."""
    
    def __init__(self, name: str, base_amount: Decimal, increment_rate: float):
        self.name = name
        self.current_amount = base_amount
        self.base_amount = base_amount
        self.increment_rate = increment_rate
        self.last_won = None
    
    def increment(self, bet_amount: Decimal) -> None:
        """Increment jackpot amount based on bet."""
        self.current_amount += bet_amount * Decimal(str(self.increment_rate))
    
    def win(self) -> Decimal:
        """Win the jackpot and reset it."""
        amount = self.current_amount
        self.current_amount = self.base_amount
        self.last_won = datetime.utcnow()
        return amount

class StickyWild:
    """Class representing a sticky wild symbol."""
    
    def __init__(self, position: Tuple[int, int], duration: int):
        self.position = position
        self.remaining_spins = duration
        self.multiplier = 1
    
    def update(self) -> bool:
        """
        Update the sticky wild state.
        
        Returns:
            bool: True if wild is still active, False if expired
        """
        self.remaining_spins -= 1
        if self.remaining_spins > 0 and self.multiplier < 5:
            # 20% chance to increase multiplier
            if self.generate_random_float() < 0.2:
                self.multiplier += 1
        return self.remaining_spins > 0

class DragonsHoard(Game):
    """
    Asian-themed slot game with sticky wilds, progressive jackpots,
    and symbol collection features.
    """
    
    # Define symbols with Asian theme
    SYMBOLS = {
        'dragon': SlotSymbol('🐉', 'Dragon', 2),
        'phoenix': SlotSymbol('🦅', 'Phoenix', 3),
        'tiger': SlotSymbol('🐯', 'Tiger', 4),
        'koi': SlotSymbol('🐠', 'Koi Fish', 5),
        'lantern': SlotSymbol('🏮', 'Lantern', 4),
        'coin': SlotSymbol('🪙', 'Lucky Coin', 3),
        'pearl': SlotSymbol('🔮', 'Dragon Pearl', 1),  # Wild
        'yin_yang': SlotSymbol('☯️', 'Yin Yang', 1)    # Scatter
    }
    
    # Collection requirements for jackpots
    COLLECTIONS = {
        'dragon': 5,    # Collect 5 dragons for Mini jackpot
        'phoenix': 4,   # Collect 4 phoenixes for Minor jackpot
        'tiger': 3,     # Collect 3 tigers for Major jackpot
        'pearl': 3      # Collect 3 pearls for Grand jackpot
    }
    
    # Base payouts
    PAYOUTS = {
        3: 5,    # 3 matching symbols
        4: 15,   # 4 matching symbols
        5: 40    # 5 matching symbols
    }
    
    def __init__(self):
        """Initialize the Dragon's Hoard slot game."""
        super().__init__(
            game_type="dragons_hoard",
            min_bet=Decimal("1.00"),
            max_bet=Decimal("200.00")
        )
        
        # Initialize jackpots
        self.jackpots = {
            'mini': JackpotTier('Mini', Decimal("50.00"), 0.01),    # 1% contribution
            'minor': JackpotTier('Minor', Decimal("200.00"), 0.02), # 2% contribution
            'major': JackpotTier('Major', Decimal("1000.00"), 0.03),# 3% contribution
            'grand': JackpotTier('Grand', Decimal("5000.00"), 0.04) # 4% contribution
        }
        
        # Game state per player
        self._player_states: Dict[int, Dict[str, Any]] = {}
    
    def _initialize_player_state(self, player_id: int) -> None:
        """Initialize or reset a player's game state."""
        self._player_states[player_id] = {
            'sticky_wilds': [],           # List of active sticky wilds
            'symbol_collections': {       # Symbol collection progress
                symbol: 0 for symbol in self.COLLECTIONS
            },
            'last_grid': None,
            'total_win': Decimal("0"),
            'last_jackpot_win': None,
            'bonus_wheel_available': False
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
    
    def _apply_sticky_wilds(
        self,
        grid: List[List[SlotSymbol]],
        state: Dict[str, Any]
    ) -> Tuple[List[List[SlotSymbol]], List[str]]:
        """
        Apply sticky wilds to the grid.
        
        Args:
            grid: Current grid state
            state: Player's game state
            
        Returns:
            Tuple[List[List[SlotSymbol]], List[str]]: (modified grid, wild messages)
        """
        messages = []
        pearl = self.SYMBOLS['pearl']
        
        # Update existing sticky wilds
        active_wilds = []
        for wild in state['sticky_wilds']:
            if wild.update():
                active_wilds.append(wild)
                row, col = wild.position
                grid[row][col] = pearl
                if wild.multiplier > 1:
                    messages.append(
                        f"💫 Sticky Wild at ({row+1}, {col+1}) "
                        f"has {wild.multiplier}x multiplier!"
                    )
        
        # Check for new sticky wilds
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                if grid[row][col] == pearl and not any(
                    wild.position == (row, col) for wild in active_wilds
                ):
                    # 15% chance to become sticky
                    if self.generate_random_float() < 0.15:
                        duration = self.generate_random_int(2, 5)
                        new_wild = StickyWild((row, col), duration)
                        active_wilds.append(new_wild)
                        messages.append(
                            f"✨ New Sticky Wild at ({row+1}, {col+1}) "
                            f"for {duration} spins!"
                        )
        
        state['sticky_wilds'] = active_wilds
        return grid, messages
    
    def _update_collections(
        self,
        grid: List[List[SlotSymbol]],
        state: Dict[str, Any]
    ) -> List[str]:
        """
        Update symbol collections and check for jackpots.
        
        Args:
            grid: Current grid state
            state: Player's game state
            
        Returns:
            List[str]: Collection and jackpot messages
        """
        messages = []
        collections = state['symbol_collections']
        
        # Count symbols in grid
        for row in grid:
            for symbol in row:
                symbol_name = str(symbol)
                if symbol_name in collections:
                    collections[symbol_name] += 1
        
        # Check for completed collections
        for symbol, required in self.COLLECTIONS.items():
            if collections[symbol] >= required:
                # Award jackpot
                if symbol == 'dragon':
                    jackpot = self.jackpots['mini']
                elif symbol == 'phoenix':
                    jackpot = self.jackpots['minor']
                elif symbol == 'tiger':
                    jackpot = self.jackpots['major']
                elif symbol == 'pearl':
                    jackpot = self.jackpots['grand']
                
                win_amount = jackpot.win()
                state['total_win'] += win_amount
                state['last_jackpot_win'] = datetime.utcnow()
                
                messages.append(
                    f"🎊 JACKPOT! Collected {required} {symbol} symbols!\n"
                    f"Won {jackpot.name} Jackpot: {win_amount:.2f}!"
                )
                
                # Reset collection
                collections[symbol] = 0
                
                # Award bonus wheel spin
                state['bonus_wheel_available'] = True
        
        return messages
    
    async def play(self, player_id: int, bet_amount: Decimal, **kwargs) -> GameResult:
        """
        Play a round of Dragon's Hoard slots.
        
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
        
        # Increment jackpots
        for jackpot in self.jackpots.values():
            jackpot.increment(bet_amount)
        
        # Generate initial grid
        grid = self._generate_grid()
        
        # Apply sticky wilds
        grid, wild_messages = self._apply_sticky_wilds(grid, state)
        
        # Update collections and check for jackpots
        collection_messages = self._update_collections(grid, state)
        
        # Check for winners and calculate winnings
        winners = self._check_paylines(grid)
        win_amount, win_messages = self._calculate_win(winners, bet_amount, state)
        
        # Combine all messages
        all_messages = wild_messages + collection_messages + win_messages
        outcome = "\n".join(all_messages) if all_messages else "No winning combinations"
        
        # Update state
        state['last_grid'] = grid
        state['total_win'] += win_amount
        
        # Add current jackpot amounts to game data
        jackpot_amounts = {
            name: str(jackpot.current_amount)
            for name, jackpot in self.jackpots.items()
        }
        
        return GameResult(
            player_id=player_id,
            game_type=self.game_type,
            bet_amount=bet_amount,
            win_amount=win_amount,
            outcome=outcome,
            game_data={
                "grid": [[str(s) for s in row] for row in grid],
                "sticky_wilds": len(state['sticky_wilds']),
                "collections": state['symbol_collections'],
                "jackpots": jackpot_amounts,
                "total_win": state['total_win'],
                "bonus_wheel_available": state['bonus_wheel_available']
            }
        )
    
    def get_game_rules(self) -> str:
        """Get the rules and payouts for Dragon's Hoard slots."""
        rules = (
            "🐉 *Dragon's Hoard Slots*\n\n"
            "*Symbols:*\n"
            "🐉 Dragon - Highest value\n"
            "🦅 Phoenix - High value\n"
            "🐯 Tiger - High value\n"
            "🐠 Koi Fish - Medium value\n"
            "🏮 Lantern - Medium value\n"
            "🪙 Lucky Coin - Low value\n"
            "🔮 Dragon Pearl - Wild symbol\n"
            "☯️ Yin Yang - Scatter\n\n"
            "*Special Features:*\n"
            "- Sticky Wilds with Multipliers\n"
            "- Symbol Collection System\n"
            "- 4 Progressive Jackpots\n"
            "- Bonus Wheel Feature\n\n"
            "*Jackpots:*\n"
            "Mini (5 Dragons): 50.00+\n"
            "Minor (4 Phoenixes): 200.00+\n"
            "Major (3 Tigers): 1,000.00+\n"
            "Grand (3 Pearls): 5,000.00+\n\n"
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
            "sticky_wilds": len(state['sticky_wilds']),
            "collections": state['symbol_collections'],
            "total_win": state['total_win'],
            "bonus_wheel_available": state['bonus_wheel_available'],
            "min_bet": self.min_bet,
            "max_bet": self.max_bet,
            "jackpots": {
                name: str(jackpot.current_amount)
                for name, jackpot in self.jackpots.items()
            }
        } 