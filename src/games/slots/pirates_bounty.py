from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
import math
from ..game_base import Game, GameResult
from .utils import (
    SlotSymbol, PaylinePattern, MultiplyBonus,
    PAYLINE_PATTERNS, load_slot_config
)

class TreasureMap:
    """Class representing a treasure map with explorable locations."""
    
    def __init__(self, size: int = 5):
        self.size = size
        self.discovered = set()  # Set of discovered coordinates
        self.treasures = {}      # Map of coordinates to treasure values
        self.current_position = (0, 0)
        self._generate_treasures()
    
    def _generate_treasures(self) -> None:
        """Generate random treasure locations and values."""
        for x in range(self.size):
            for y in range(self.size):
                if (x, y) != (0, 0) and self._rng.random() < 0.4:  # 40% chance
                    value = self._rng.randint(5, 50)
                    self.treasures[(x, y)] = value
    
    def move(self, direction: str) -> Tuple[bool, Optional[int]]:
        """
        Move in the specified direction and discover treasures.
        
        Args:
            direction: Direction to move ('N', 'S', 'E', 'W')
            
        Returns:
            Tuple[bool, Optional[int]]: (move_successful, treasure_found)
        """
        x, y = self.current_position
        if direction == 'N' and y < self.size - 1:
            y += 1
        elif direction == 'S' and y > 0:
            y -= 1
        elif direction == 'E' and x < self.size - 1:
            x += 1
        elif direction == 'W' and x > 0:
            x -= 1
        else:
            return False, None
            
        self.current_position = (x, y)
        self.discovered.add((x, y))
        
        treasure = self.treasures.get((x, y))
        if treasure is not None:
            del self.treasures[(x, y)]
            return True, treasure
            
        return True, None

class QuestProgress:
    """Class representing a pirate quest progress."""
    
    def __init__(self, name: str, target: int, reward_multiplier: float):
        self.name = name
        self.target = target
        self.current = 0
        self.reward_multiplier = reward_multiplier
        self.completed = False
    
    def update(self, amount: int) -> bool:
        """
        Update quest progress.
        
        Args:
            amount: Amount to add to progress
            
        Returns:
            bool: True if quest completed this update
        """
        if self.completed:
            return False
            
        self.current += amount
        if self.current >= self.target:
            self.completed = True
            return True
        return False

class PiratesBounty(Game):
    """
    Pirate-themed slot game with treasure map exploration,
    multiplier storms, and progressive quest system.
    """
    
    # Define symbols with pirate theme
    SYMBOLS = {
        'ship': SlotSymbol('🏴‍☠️', 'Pirate Ship', 2),
        'chest': SlotSymbol('💎', 'Treasure Chest', 3),
        'map': SlotSymbol('🗺️', 'Map', 4),
        'compass': SlotSymbol('🧭', 'Compass', 5),
        'parrot': SlotSymbol('🦜', 'Parrot', 4),
        'sword': SlotSymbol('⚔️', 'Sword', 3),
        'wheel': SlotSymbol('🎡', 'Ship Wheel', 1),  # Wild
        'skull': SlotSymbol('💀', 'Skull', 1)        # Scatter
    }
    
    # Quest definitions
    QUESTS = {
        'collector': ('Treasure Hunter', 50, 2.0),    # Collect 50 chests
        'explorer': ('Map Master', 25, 3.0),         # Discover 25 map locations
        'warrior': ('Storm Chaser', 30, 2.5),        # Survive 30 storms
        'captain': ('Fleet Admiral', 100, 5.0)       # Win 100 times
    }
    
    # Base payouts
    PAYOUTS = {
        3: 5,    # 3 matching symbols
        4: 12,   # 4 matching symbols
        5: 30    # 5 matching symbols
    }
    
    def __init__(self):
        """Initialize the Pirate's Bounty slot game."""
        super().__init__(
            game_type="pirates_bounty",
            min_bet=Decimal("1.00"),
            max_bet=Decimal("150.00")
        )
        
        # Initialize bonus features
        self.multiply_bonus = MultiplyBonus(0.2, (2, 10))  # 20% chance, 2-10x multiplier
        
        # Game state per player
        self._player_states: Dict[int, Dict[str, Any]] = {}
    
    def _initialize_player_state(self, player_id: int) -> None:
        """Initialize or reset a player's game state."""
        self._player_states[player_id] = {
            'treasure_map': TreasureMap(),
            'quests': {
                name: QuestProgress(desc, target, mult)
                for name, (desc, target, mult) in self.QUESTS.items()
            },
            'storm_multiplier': 1,
            'storm_duration': 0,
            'last_grid': None,
            'total_win': Decimal("0"),
            'exploration_moves': 3,  # Moves available for map exploration
            'crew_members': set()    # Collected crew members
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
    
    def _handle_storm(self, state: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Handle multiplier storm mechanics.
        
        Args:
            state: Player's game state
            
        Returns:
            Tuple[float, List[str]]: (storm_multiplier, storm_messages)
        """
        messages = []
        
        # Check for new storm
        if state['storm_duration'] <= 0 and self.generate_random_float() < 0.15:
            state['storm_duration'] = self.generate_random_int(3, 7)
            state['storm_multiplier'] = round(1 + self.generate_random_float() * 4, 1)
            messages.append(
                f"🌊 Multiplier Storm brewing! x{state['storm_multiplier']} "
                f"for {state['storm_duration']} spins!"
            )
        
        # Update existing storm
        if state['storm_duration'] > 0:
            state['storm_duration'] -= 1
            if state['storm_duration'] == 0:
                messages.append("🌅 The storm has passed!")
                state['storm_multiplier'] = 1
            else:
                messages.append(
                    f"⛈️ Storm continues! {state['storm_duration']} spins remaining "
                    f"at x{state['storm_multiplier']}"
                )
        
        return state['storm_multiplier'], messages
    
    def _explore_map(
        self,
        state: Dict[str, Any],
        moves: Optional[List[str]] = None
    ) -> List[str]:
        """
        Handle treasure map exploration.
        
        Args:
            state: Player's game state
            moves: Optional list of directions to move
            
        Returns:
            List[str]: Exploration messages
        """
        messages = []
        treasure_map = state['treasure_map']
        
        if moves and state['exploration_moves'] > 0:
            for direction in moves:
                if state['exploration_moves'] <= 0:
                    break
                    
                success, treasure = treasure_map.move(direction)
                if success:
                    state['exploration_moves'] -= 1
                    messages.append(
                        f"🗺️ Moved {direction}! "
                        f"{state['exploration_moves']} moves remaining."
                    )
                    
                    if treasure:
                        bonus_win = Decimal(str(treasure))
                        state['total_win'] += bonus_win
                        messages.append(f"💎 Found treasure worth {bonus_win}!")
                        
                        # Update quest progress
                        state['quests']['explorer'].update(1)
        
        # Replenish moves on map completion
        if len(treasure_map.discovered) == treasure_map.size * treasure_map.size:
            state['exploration_moves'] = 3
            treasure_map = TreasureMap()  # Generate new map
            messages.append("🗺️ Map completed! New map generated with 3 moves!")
        
        return messages
    
    def _update_quests(
        self,
        state: Dict[str, Any],
        win_amount: Decimal
    ) -> Tuple[Decimal, List[str]]:
        """
        Update quest progress and check for completions.
        
        Args:
            state: Player's game state
            win_amount: Base win amount
            
        Returns:
            Tuple[Decimal, List[str]]: (modified_win, quest_messages)
        """
        messages = []
        modified_win = win_amount
        
        # Update various quest progresses
        if win_amount > 0:
            state['quests']['captain'].update(1)
        
        if state['storm_duration'] > 0:
            state['quests']['warrior'].update(1)
        
        # Check for quest completions
        for quest_name, quest in state['quests'].items():
            if quest.update(0):  # Check if just completed
                bonus = win_amount * Decimal(str(quest.reward_multiplier))
                modified_win += bonus
                messages.append(
                    f"🎯 Quest Complete: {quest.name}!\n"
                    f"Bonus: {bonus:.2f} (x{quest.reward_multiplier})"
                )
        
        return modified_win, messages
    
    async def play(self, player_id: int, bet_amount: Decimal, **kwargs) -> GameResult:
        """
        Play a round of Pirate's Bounty slots.
        
        Args:
            player_id: ID of the player
            bet_amount: Amount being bet
            **kwargs: Additional parameters (moves: List[str] for map exploration)
            
        Returns:
            GameResult: Result of the slot game
        """
        # Initialize player state if needed
        if player_id not in self._player_states:
            self._initialize_player_state(player_id)
        
        state = self._player_states[player_id]
        
        # Handle storm multiplier
        storm_multiplier, storm_messages = self._handle_storm(state)
        
        # Generate grid and calculate base wins
        grid = self._generate_grid()
        winners = self._check_paylines(grid)
        base_win, win_messages = self._calculate_win(winners, bet_amount)
        
        # Apply storm multiplier
        win_amount = base_win * Decimal(str(storm_multiplier))
        if storm_multiplier > 1 and base_win > 0:
            win_messages.append(f"⚡ Storm Multiplier: x{storm_multiplier}")
        
        # Handle map exploration if moves provided
        explore_messages = self._explore_map(state, kwargs.get('moves'))
        
        # Update quests and apply bonuses
        win_amount, quest_messages = self._update_quests(state, win_amount)
        
        # Combine all messages
        all_messages = (
            storm_messages +
            win_messages +
            explore_messages +
            quest_messages
        )
        outcome = "\n".join(all_messages) if all_messages else "No winning combinations"
        
        # Update state
        state['last_grid'] = grid
        state['total_win'] += win_amount
        
        return GameResult(
            player_id=player_id,
            game_type=self.game_type,
            bet_amount=bet_amount,
            win_amount=win_amount,
            outcome=outcome,
            game_data={
                "grid": [[str(s) for s in row] for row in grid],
                "storm": {
                    "active": state['storm_duration'] > 0,
                    "multiplier": state['storm_multiplier'],
                    "duration": state['storm_duration']
                },
                "map": {
                    "discovered": len(state['treasure_map'].discovered),
                    "total": state['treasure_map'].size * state['treasure_map'].size,
                    "moves_remaining": state['exploration_moves']
                },
                "quests": {
                    name: {
                        "progress": quest.current,
                        "target": quest.target,
                        "completed": quest.completed
                    }
                    for name, quest in state['quests'].items()
                },
                "total_win": state['total_win']
            }
        )
    
    def get_game_rules(self) -> str:
        """Get the rules and payouts for Pirate's Bounty slots."""
        rules = (
            "🏴‍☠️ *Pirate's Bounty Slots*\n\n"
            "*Symbols:*\n"
            "🏴‍☠️ Pirate Ship - Highest value\n"
            "💎 Treasure Chest - High value\n"
            "🗺️ Map - High value\n"
            "🧭 Compass - Medium value\n"
            "🦜 Parrot - Medium value\n"
            "⚔️ Sword - Low value\n"
            "🎡 Ship Wheel - Wild symbol\n"
            "💀 Skull - Scatter\n\n"
            "*Special Features:*\n"
            "- Multiplier Storms (up to x5)\n"
            "- Treasure Map Exploration\n"
            "- Progressive Quest System\n"
            "- Hidden Treasures\n\n"
            "*Quests:*\n"
            "Treasure Hunter: Collect 50 chests (x2)\n"
            "Map Master: Discover 25 locations (x3)\n"
            "Storm Chaser: Survive 30 storms (x2.5)\n"
            "Fleet Admiral: Win 100 times (x5)\n\n"
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
            "storm_active": state['storm_duration'] > 0,
            "storm_multiplier": state['storm_multiplier'],
            "exploration_moves": state['exploration_moves'],
            "map_progress": len(state['treasure_map'].discovered),
            "quests": {
                name: {
                    "progress": quest.current,
                    "target": quest.target,
                    "completed": quest.completed
                }
                for name, quest in state['quests'].items()
            },
            "total_win": state['total_win'],
            "min_bet": self.min_bet,
            "max_bet": self.max_bet
        } 