import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from typing import AsyncGenerator, Generator
from pytest import FixtureRequest
from _pytest.fixtures import FixtureFunction

from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

from src.handlers.start_handler import StartHandler
from src.handlers.wallet_handler import WalletHandler
from src.handlers.help_handler import HelpHandler

@pytest.fixture
def mock_user() -> User:
    """Create a mock Telegram user."""
    user = MagicMock(spec=User)
    user.id = 123456
    user.first_name = "Test"
    user.username = "testuser"
    return user

@pytest.fixture
def mock_chat() -> Chat:
    """Create a mock Telegram chat."""
    chat = MagicMock(spec=Chat)
    chat.id = 123456
    return chat

@pytest.fixture
def mock_message(mock_user: User, mock_chat: Chat) -> Message:
    """Create a mock Telegram message."""
    message = MagicMock(spec=Message)
    message.from_user = mock_user
    message.chat = mock_chat
    return message

@pytest.fixture
def mock_update(mock_message: Message) -> Update:
    """Create a mock Telegram update."""
    update = MagicMock(spec=Update)
    update.effective_user = mock_message.from_user
    update.effective_chat = mock_message.chat
    update.message = mock_message
    return update

@pytest.fixture
def mock_context() -> ContextTypes.DEFAULT_TYPE:
    """Create a mock context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = AsyncMock()
    return context

@pytest.fixture
def mock_user_service() -> AsyncMock:
    """Create a mock user service."""
    service = AsyncMock()
    service.is_user_registered = AsyncMock(return_value=False)
    service.register_user = AsyncMock(return_value=True)
    service.update_last_active = AsyncMock(return_value=True)
    return service

@pytest.fixture
def mock_wallet_service() -> AsyncMock:
    """Create a mock wallet service."""
    service = AsyncMock()
    service.create_transaction = AsyncMock(return_value=True)
    service.get_user_balance = AsyncMock(return_value=Decimal("100.00"))
    service.get_user_transactions = AsyncMock(return_value=[])
    return service

@pytest.mark.asyncio
async def test_start_handler_new_user(
    mock_update: Update,
    mock_context: ContextTypes.DEFAULT_TYPE,
    mock_user_service: AsyncMock,
    mock_wallet_service: AsyncMock
):
    """Test start handler with a new user."""
    handler = StartHandler(mock_user_service, mock_wallet_service)
    
    await handler.handle(mock_update, mock_context)
    
    # Verify user registration
    mock_user_service.is_user_registered.assert_called_once_with(123456)
    mock_user_service.register_user.assert_called_once_with(123456)
    
    # Verify welcome bonus transaction
    mock_wallet_service.create_transaction.assert_called_once_with(
        user_id=123456,
        type="bonus",
        amount=Decimal("10.00"),
        currency="USD"
    )
    
    # Verify welcome message
    mock_context.bot.send_message.assert_called_once()
    args = mock_context.bot.send_message.call_args[1]
    assert "Welcome to the Casino Bot" in args["text"]
    assert "$10.00 welcome bonus" in args["text"]

@pytest.mark.asyncio
async def test_start_handler_existing_user(
    mock_update: Update,
    mock_context: ContextTypes.DEFAULT_TYPE,
    mock_user_service: AsyncMock,
    mock_wallet_service: AsyncMock
):
    """Test start handler with an existing user."""
    mock_user_service.is_user_registered.return_value = True
    handler = StartHandler(mock_user_service, mock_wallet_service)
    
    await handler.handle(mock_update, mock_context)
    
    # Verify user service calls
    mock_user_service.is_user_registered.assert_called_once_with(123456)
    mock_user_service.register_user.assert_not_called()
    mock_user_service.update_last_active.assert_called_once_with(123456)
    
    # Verify balance check
    mock_wallet_service.get_user_balance.assert_called_once_with(123456, "USD")
    
    # Verify welcome back message
    mock_context.bot.send_message.assert_called_once()
    args = mock_context.bot.send_message.call_args[1]
    assert "Welcome back" in args["text"]
    assert "$100.00" in args["text"]

@pytest.mark.asyncio
async def test_help_handler(
    mock_update: Update,
    mock_context: ContextTypes.DEFAULT_TYPE
):
    """Test help handler."""
    handler = HelpHandler()
    
    await handler.handle(mock_update, mock_context)
    
    # Verify help message
    mock_context.bot.send_message.assert_called_once()
    args = mock_context.bot.send_message.call_args[1]
    assert "Available Commands" in args["text"]
    assert "/start" in args["text"]
    assert "/help" in args["text"]
    assert "/deposit" in args["text"]
    assert "/withdraw" in args["text"]
    assert "/balance" in args["text"]

@pytest.mark.asyncio
async def test_wallet_handler_deposit(
    mock_update: Update,
    mock_context: ContextTypes.DEFAULT_TYPE,
    mock_user_service: AsyncMock,
    mock_wallet_service: AsyncMock
):
    """Test wallet handler deposit command."""
    mock_user_service.is_user_registered.return_value = True
    handler = WalletHandler(mock_user_service, mock_wallet_service)
    
    # Set up deposit amount in context
    mock_context.args = ["50.00"]
    
    await handler.handle_deposit(mock_update, mock_context)
    
    # Verify transaction creation
    mock_wallet_service.create_transaction.assert_called_once_with(
        user_id=123456,
        type="deposit",
        amount=Decimal("50.00"),
        currency="USD"
    )
    
    # Verify balance check
    mock_wallet_service.get_user_balance.assert_called_once_with(123456, "USD")
    
    # Verify success message
    mock_context.bot.send_message.assert_called_once()
    args = mock_context.bot.send_message.call_args[1]
    assert "Deposited: $50.00" in args["text"]
    assert "Current balance: $100.00" in args["text"]

@pytest.mark.asyncio
async def test_wallet_handler_withdraw(
    mock_update: Update,
    mock_context: ContextTypes.DEFAULT_TYPE,
    mock_user_service: AsyncMock,
    mock_wallet_service: AsyncMock
):
    """Test wallet handler withdraw command."""
    mock_user_service.is_user_registered.return_value = True
    handler = WalletHandler(mock_user_service, mock_wallet_service)
    
    # Set up withdrawal amount in context
    mock_context.args = ["30.00"]
    
    await handler.handle_withdraw(mock_update, mock_context)
    
    # Verify transaction creation
    mock_wallet_service.create_transaction.assert_called_once_with(
        user_id=123456,
        type="withdraw",
        amount=Decimal("30.00"),
        currency="USD"
    )
    
    # Verify balance check
    mock_wallet_service.get_user_balance.assert_called()
    
    # Verify success message
    mock_context.bot.send_message.assert_called_once()
    args = mock_context.bot.send_message.call_args[1]
    assert "Withdrawn: $30.00" in args["text"]
    assert "Current balance: $100.00" in args["text"]

@pytest.mark.asyncio
async def test_wallet_handler_balance(
    mock_update: Update,
    mock_context: ContextTypes.DEFAULT_TYPE,
    mock_user_service: AsyncMock,
    mock_wallet_service: AsyncMock
):
    """Test wallet handler balance command."""
    mock_user_service.is_user_registered.return_value = True
    handler = WalletHandler(mock_user_service, mock_wallet_service)
    
    await handler.handle_balance(mock_update, mock_context)
    
    # Verify balance check
    mock_wallet_service.get_user_balance.assert_called_once_with(123456, "USD")
    
    # Verify transaction history check
    mock_wallet_service.get_user_transactions.assert_called_once_with(123456)
    
    # Verify balance message
    mock_context.bot.send_message.assert_called_once()
    args = mock_context.bot.send_message.call_args[1]
    assert "Current balance: $100.00" in args["text"] 