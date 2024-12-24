from typing import Dict, Type, Optional
from decimal import Decimal
import logging
from .game_base import Game, GameResult

logger = logging.getLogger(__name__)

class GameManager:
    """Manages game instances and handles game operations."""
    
    def __init__(self):
        """Initialize the game manager."""
        self._games: Dict[str, Type[Game]] = {}
        self._active_games: Dict[int, Dict[str, Game]] = {}
        
    def register_game(self, game_type: str, game_class: Type[Game]) -> None:
        """
        Register a new game type.
        
        Args:
            game_type: Identifier for the game type
            game_class: The game class to register
        """
        if game_type in self._games:
            logger.warning(f"Game type {game_type} already registered, overwriting")
        self._games[game_type] = game_class
        logger.info(f"Registered game type: {game_type}")
    
    def get_game_instance(self, game_type: str, player_id: int) -> Optional[Game]:
        """
        Get or create a game instance for a player.
        
        Args:
            game_type: Type of game to get/create
            player_id: ID of the player
            
        Returns:
            Optional[Game]: Game instance or None if game type not found
        """
        if game_type not in self._games:
            logger.error(f"Unknown game type: {game_type}")
            return None
            
        # Create player's game dictionary if it doesn't exist
        if player_id not in self._active_games:
            self._active_games[player_id] = {}
            
        # Create new game instance if it doesn't exist
        if game_type not in self._active_games[player_id]:
            game_class = self._games[game_type]
            self._active_games[player_id][game_type] = game_class()
            
        return self._active_games[player_id][game_type]
    
    async def play_game(
        self,
        game_type: str,
        player_id: int,
        bet_amount: Decimal,
        **kwargs
    ) -> Optional[GameResult]:
        """
        Play a game for a player.
        
        Args:
            game_type: Type of game to play
            player_id: ID of the player
            bet_amount: Amount being bet
            **kwargs: Additional game-specific parameters
            
        Returns:
            Optional[GameResult]: Result of the game or None if error
        """
        try:
            game = self.get_game_instance(game_type, player_id)
            if not game:
                return None
                
            result = await game.play(player_id, bet_amount, **kwargs)
            logger.info(
                f"Game {game_type} played by player {player_id}. "
                f"Bet: {bet_amount}, Won: {result.win_amount}"
            )
            return result
            
        except Exception as e:
            logger.error(f"Error playing game {game_type}: {str(e)}", exc_info=True)
            return None
    
    def get_available_games(self) -> Dict[str, str]:
        """
        Get list of available games and their descriptions.
        
        Returns:
            Dict[str, str]: Dictionary of game types and their descriptions
        """
        return {
            game_type: game_class().get_game_rules()
            for game_type, game_class in self._games.items()
        }
        
    def cleanup_player_games(self, player_id: int) -> None:
        """
        Clean up game instances for a player.
        
        Args:
            player_id: ID of the player
        """
        if player_id in self._active_games:
            del self._active_games[player_id]
            logger.info(f"Cleaned up games for player {player_id}")
            
# Create a global instance of the game manager
game_manager = GameManager() 