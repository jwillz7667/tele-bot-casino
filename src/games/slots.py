from decimal import Decimal
from typing import Dict, Any, List, Tuple
from .game_base import Game, GameResult

class Slots(Game):
    """Implementation of a slot machine game."""
    
    SYMBOLS = ['🍒', '🍊', '🍋', '🍇', '💎', '7️⃣']
    PAYOUTS = {
        ('🍒', '🍒', '🍒'): 3,    # Triple cherries
        ('🍊', '🍊', '🍊'): 4,    # Triple oranges
        ('🍋', '🍋', '🍋'): 5,    # Triple lemons
        ('🍇', '🍇', '🍇'): 8,    # Triple grapes
        ('💎', '💎', '💎'): 15,   # Triple diamonds
        ('7️⃣', '7️⃣', '7️⃣'): 25,  # Triple sevens
    }
    
    def __init__(self):
        """Initialize the slots game with specific betting limits."""
        super().__init__(
            game_type="slots",
            min_bet=Decimal("1.00"),
            max_bet=Decimal("100.00")
        )
        self._last_spins: Dict[int, List[str]] = {}
    
    def _spin_reels(self) -> List[str]:
        """
        Generate random symbols for each reel.
        
        Returns:
            List[str]: List of three symbols
        """
        return [
            self.SYMBOLS[self.generate_random_int(0, len(self.SYMBOLS) - 1)]
            for _ in range(3)
        ]
    
    def _calculate_winnings(self, symbols: List[str], bet_amount: Decimal) -> Tuple[Decimal, str]:
        """
        Calculate winnings based on symbols and bet amount.
        
        Args:
            symbols: List of symbols from the spin
            bet_amount: Amount that was bet
            
        Returns:
            Tuple[Decimal, str]: Tuple of (winnings, outcome description)
        """
        symbol_tuple = tuple(symbols)
        multiplier = self.PAYOUTS.get(symbol_tuple, 0)
        winnings = bet_amount * multiplier
        
        if multiplier > 0:
            outcome = f"Winner! {' '.join(symbols)} - {multiplier}x multiplier"
        else:
            outcome = f"No win. {' '.join(symbols)}"
            
        return Decimal(str(winnings)), outcome
    
    async def play(self, player_id: int, bet_amount: Decimal, **kwargs) -> GameResult:
        """
        Play a round of slots.
        
        Args:
            player_id: ID of the player
            bet_amount: Amount being bet
            **kwargs: Additional parameters (unused)
            
        Returns:
            GameResult: Result of the slot game
        """
        symbols = self._spin_reels()
        self._last_spins[player_id] = symbols
        
        winnings, outcome = self._calculate_winnings(symbols, bet_amount)
        
        return GameResult(
            player_id=player_id,
            game_type=self.game_type,
            bet_amount=bet_amount,
            win_amount=winnings,
            outcome=outcome,
            game_data={"symbols": symbols}
        )
    
    def get_game_rules(self) -> str:
        """
        Get the rules and payouts for slots.
        
        Returns:
            str: Formatted string of rules and payouts
        """
        rules = (
            "🎰 *Slots Game Rules*\n\n"
            "Bet and spin to match three symbols:\n\n"
            "*Payouts:*\n"
            "🍒🍒🍒 - 3x\n"
            "🍊🍊🍊 - 4x\n"
            "🍋🍋🍋 - 5x\n"
            "🍇🍇🍇 - 8x\n"
            "💎💎💎 - 15x\n"
            "7️⃣7️⃣7️⃣ - 25x\n\n"
            f"Min bet: {self.min_bet}\n"
            f"Max bet: {self.max_bet}"
        )
        return rules
    
    def get_game_state(self, player_id: int) -> Dict[str, Any]:
        """
        Get the current state of the slots game for a player.
        
        Args:
            player_id: ID of the player
            
        Returns:
            Dict[str, Any]: Current game state
        """
        return {
            "last_spin": self._last_spins.get(player_id, []),
            "min_bet": self.min_bet,
            "max_bet": self.max_bet
        } 