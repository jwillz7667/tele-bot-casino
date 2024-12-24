"""Unit tests for the game handler."""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from src.handlers.game_handler import GameHandler
from src.wallet.crypto_types import CryptoType, CryptoAmount
from src.games.game_base import GameResult

@pytest.mark.asyncio
async def test_games_command_registered_user(
    mock_telegram_update,
    mock_telegram_context,
    mock_wallet_service,
    mock_user_service,
    mock_game_manager
):
    """Test games command with registered user."""
    handler = GameHandler(mock_wallet_service, mock_user_service)
    mock_user_service.is_registered.return_value = True
    
    await handler.games_command(mock_telegram_update, mock_telegram_context)
    
    mock_telegram_update.message.reply_text.assert_called_once()

@pytest.mark.asyncio
async def test_games_command_unregistered_user(
    mock_telegram_update,
    mock_telegram_context,
    mock_wallet_service,
    mock_user_service,
    mock_game_manager
):
    """Test games command with unregistered user."""
    handler = GameHandler(mock_wallet_service, mock_user_service)
    mock_user_service.is_registered.return_value = False
    
    await handler.games_command(mock_telegram_update, mock_telegram_context)
    
    mock_telegram_update.message.reply_text.assert_called_once()

@pytest.mark.asyncio
async def test_show_game_menu(
    mock_telegram_update,
    mock_telegram_context,
    mock_wallet_service,
    mock_user_service,
    mock_game_manager
):
    """Test showing game menu."""
    handler = GameHandler(mock_wallet_service, mock_user_service)
    game_type = "slots"
    mock_game_manager.get_game.return_value = AsyncMock()
    
    await handler.show_game_menu(
        mock_telegram_update,
        mock_telegram_context,
        game_type
    )
    
    mock_telegram_update.message.reply_text.assert_called_once()

@pytest.mark.asyncio
async def test_show_game_rules(
    mock_telegram_update,
    mock_telegram_context,
    mock_wallet_service,
    mock_user_service,
    mock_game_manager
):
    """Test showing game rules."""
    handler = GameHandler(mock_wallet_service, mock_user_service)
    game_type = "slots"
    mock_game_manager.get_game.return_value = AsyncMock()
    mock_game_manager.get_game_rules.return_value = "Game rules"
    
    await handler.show_game_rules(
        mock_telegram_update,
        mock_telegram_context,
        game_type
    )
    
    mock_telegram_update.message.reply_text.assert_called_once()

@pytest.mark.asyncio
async def test_handle_bet_amount_valid(
    mock_telegram_update,
    mock_telegram_context,
    mock_wallet_service,
    mock_user_service,
    mock_game_manager
):
    """Test handling valid bet amount."""
    handler = GameHandler(mock_wallet_service, mock_user_service)
    game_type = "slots"
    crypto_type = CryptoType.USDT
    mock_telegram_update.message.text = "10.00"
    
    # Mock game result
    mock_game = AsyncMock()
    mock_game.play.return_value = GameResult(
        player_id=123456789,
        game_type=game_type,
        bet_amount=CryptoAmount(Decimal('10.00'), crypto_type),
        win_amount=CryptoAmount(Decimal('20.00'), crypto_type),
        outcome="You won!",
        game_data={'grid': [['🍎', '🍎', '🍎']]}
    )
    mock_game_manager.get_game.return_value = mock_game
    
    await handler.handle_bet_amount(
        mock_telegram_update,
        mock_telegram_context,
        game_type,
        crypto_type
    )
    
    mock_telegram_update.message.reply_text.assert_called_once()

@pytest.mark.asyncio
async def test_handle_bet_amount_invalid(
    mock_telegram_update,
    mock_telegram_context,
    mock_wallet_service,
    mock_user_service,
    mock_game_manager
):
    """Test handling invalid bet amount."""
    handler = GameHandler(mock_wallet_service, mock_user_service)
    game_type = "slots"
    crypto_type = CryptoType.USDT
    mock_telegram_update.message.text = "invalid"
    
    await handler.handle_bet_amount(
        mock_telegram_update,
        mock_telegram_context,
        game_type,
        crypto_type
    )
    
    mock_telegram_update.message.reply_text.assert_called_once() 