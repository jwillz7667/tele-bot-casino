from .game_base import Game, GameResult
from .game_manager import game_manager
from .slots.ancient_treasures import AncientTreasures
from .slots.cosmic_fortune import CosmicFortune
from .slots.mystic_forest import MysticForest
from .slots.dragons_hoard import DragonsHoard
from .slots.pirates_bounty import PiratesBounty

# Register available games
game_manager.register_game("ancient_treasures", AncientTreasures)
game_manager.register_game("cosmic_fortune", CosmicFortune)
game_manager.register_game("mystic_forest", MysticForest)
game_manager.register_game("dragons_hoard", DragonsHoard)
game_manager.register_game("pirates_bounty", PiratesBounty)

__all__ = [
    'Game',
    'GameResult',
    'game_manager',
    'AncientTreasures',
    'CosmicFortune',
    'MysticForest',
    'DragonsHoard',
    'PiratesBounty'
] 