"""Pytest configuration and shared fixtures."""
import os
import pytest
import pytest_asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.wallet import CryptoType, CryptoAmount
from src.wallet.wallet_service import WalletService
from src.wallet.transaction import Transaction, TransactionType
from src.games.game_manager import GameManager
from src.payments.service import PaymentService
from src.user_service import UserService, Base

@pytest.fixture
def mock_user_data() -> Dict[str, Any]:
    """Fixture providing mock user data."""
    return {
        'id': 123456789,
        'telegram_id': 123456789,
        'username': 'test_user',
        'is_active': True,
        'created_at': '2024-01-01T00:00:00Z',
        'last_active': '2024-01-01T00:00:00Z'
    }

@pytest.fixture
def mock_wallet_data() -> Dict[str, Any]:
    """Fixture providing mock wallet data."""
    return {
        'user_id': 123456789,
        'balances': {
            CryptoType.BTC.value: '0.001',
            CryptoType.ETH.value: '0.1',
            CryptoType.USDT.value: '100.00'
        }
    }

@pytest_asyncio.fixture
async def mock_wallet_service():
    """Create a mock wallet service."""
    mock = AsyncMock()
    mock.get_balance.return_value = CryptoAmount(Decimal('100.00'), CryptoType.USDT)
    mock.process_transaction.return_value = (True, None)
    mock.get_transaction_history.return_value = []
    return mock

@pytest_asyncio.fixture
async def mock_user_service():
    """Create a mock user service."""
    mock = AsyncMock()
    mock.is_registered.return_value = True
    mock.register_user.return_value = True
    mock.update_last_active.return_value = None
    return mock

@pytest_asyncio.fixture
async def mock_game_manager():
    """Create a mock game manager."""
    mock = AsyncMock()
    mock.get_game.return_value = AsyncMock()
    mock.get_game_rules.return_value = "Game rules"
    return mock

@pytest_asyncio.fixture
async def mock_payment_service() -> PaymentService:
    """Fixture providing a mocked payment service."""
    service = AsyncMock(spec=PaymentService)
    
    # Mock methods
    service.create_deposit.return_value = (
        MagicMock(id='test_intent_id'),
        'https://test.payment.url'
    )
    service.process_webhook.return_value = None
    
    return service

@pytest.fixture
def mock_telegram_update():
    """Create a mock telegram update."""
    mock = MagicMock()
    mock.effective_user.id = 123456789
    mock.effective_user.username = "test_user"
    mock.message.text = "10.00"
    mock.message.reply_text = AsyncMock()
    mock.callback_query.message.reply_text = AsyncMock()
    mock.callback_query.message.edit_text = AsyncMock()
    return mock

@pytest.fixture
def mock_telegram_context():
    """Create a mock telegram context."""
    return MagicMock()

@pytest.fixture
def mock_transaction():
    """Create a mock transaction."""
    return Transaction.create(
        user_id=123456789,
        type=TransactionType.DEPOSIT,
        amount=CryptoAmount(Decimal('100.00'), CryptoType.USDT),
        metadata={'payment_intent_id': 'test_intent_id'}
    ) 

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture(scope="session")
def session_factory(engine):
    """Create a test session factory."""
    return sessionmaker(bind=engine)

@pytest.fixture(autouse=True)
def cleanup_database(session_factory):
    """Clean up database after each test."""
    yield
    with session_factory() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete()) 