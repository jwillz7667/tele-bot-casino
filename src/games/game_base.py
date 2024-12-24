from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from decimal import Decimal
import secrets
import logging

logger = logging.getLogger(__name__)

@dataclass
class GameResult:
    """Data class to store the result of a game round."""
    player_id: int
    game_type: str
    bet_amount: Decimal
    win_amount: Decimal
    outcome: str
    timestamp: datetime = datetime.utcnow()
    game_data: Optional[Dict[str, Any]] = None

class Game(ABC):
    """Abstract base class for all casino games."""
    
    def __init__(self, game_type: str, min_bet: Decimal, max_bet: Decimal):
        """
        Initialize a new game instance.
        
        Args:
            game_type: Identifier for the type of game
            min_bet: Minimum allowed bet amount
            max_bet: Maximum allowed bet amount
        """
        self.game_type = game_type
        self.min_bet = min_bet
        self.max_bet = max_bet
        self._rng = secrets.SystemRandom()  # Cryptographically secure RNG
    
    def validate_bet(self, amount: Decimal, player_balance: Decimal) -> bool:
        """
        Validate if a bet amount is acceptable.
        
        Args:
            amount: The bet amount to validate
            player_balance: Current balance of the player
            
        Returns:
            bool: True if bet is valid, False otherwise
        """
        try:
            if not isinstance(amount, Decimal):
                amount = Decimal(str(amount))
            
            if amount < self.min_bet:
                logger.warning(f"Bet amount {amount} below minimum {self.min_bet}")
                return False
            if amount > self.max_bet:
                logger.warning(f"Bet amount {amount} above maximum {self.max_bet}")
                return False
            if amount > player_balance:
                logger.warning(f"Insufficient balance: {player_balance} < {amount}")
                return False
                
            return True
        except (ValueError, TypeError) as e:
            logger.error(f"Error validating bet: {str(e)}")
            return False
    
    def generate_random_float(self, start: float = 0.0, end: float = 1.0) -> float:
        """
        Generate a cryptographically secure random float in range [start, end].
        
        Args:
            start: Start of range (inclusive)
            end: End of range (inclusive)
            
        Returns:
            float: Random float in specified range
        """
        return start + (self._rng.random() * (end - start))
    
    def generate_random_int(self, start: int, end: int) -> int:
        """
        Generate a cryptographically secure random integer in range [start, end].
        
        Args:
            start: Start of range (inclusive)
            end: End of range (inclusive)
            
        Returns:
            int: Random integer in specified range
        """
        return self._rng.randint(start, end)
    
    @abstractmethod
    async def play(self, player_id: int, bet_amount: Decimal, **kwargs) -> GameResult:
        """
        Play a round of the game.
        
        Args:
            player_id: ID of the player
            bet_amount: Amount being bet
            **kwargs: Additional game-specific parameters
            
        Returns:
            GameResult: The result of the game round
        """
        pass
    
    @abstractmethod
    def get_game_rules(self) -> str:
        """
        Get the rules and instructions for the game.
        
        Returns:
            str: Formatted string containing game rules
        """
        pass
    
    @abstractmethod
    def get_game_state(self, player_id: int) -> Dict[str, Any]:
        """
        Get the current state of the game for a player.
        
        Args:
            player_id: ID of the player
            
        Returns:
            Dict[str, Any]: Current game state
        """
        pass 