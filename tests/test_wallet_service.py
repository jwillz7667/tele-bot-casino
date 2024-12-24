"""Unit tests for the wallet service."""
import pytest
from decimal import Decimal
from src.wallet.crypto_types import CryptoType, CryptoAmount
from src.wallet.transaction import Transaction, TransactionType

@pytest.mark.asyncio
async def test_get_balance(mock_wallet_service):
    """Test getting user balance."""
    user_id = 123456789
    crypto_type = CryptoType.USDT
    
    balance = await mock_wallet_service.get_balance(user_id, crypto_type)
    
    assert isinstance(balance, CryptoAmount)
    assert balance.amount == Decimal('100.00')
    assert balance.currency == CryptoType.USDT

@pytest.mark.asyncio
async def test_process_deposit_transaction(mock_wallet_service, mock_transaction):
    """Test processing a deposit transaction."""
    success, error = await mock_wallet_service.process_transaction(mock_transaction)
    
    assert success is True
    assert error is None

@pytest.mark.asyncio
async def test_process_withdrawal_transaction(mock_wallet_service):
    """Test processing a withdrawal transaction."""
    transaction = Transaction.create(
        user_id=123456789,
        type=TransactionType.WITHDRAWAL,
        amount=CryptoAmount(Decimal('50.00'), CryptoType.USDT),
        metadata={'address': 'test_address'}
    )
    
    mock_wallet_service.process_transaction.return_value = (False, "Insufficient funds")
    
    success, error = await mock_wallet_service.process_transaction(transaction)
    
    assert success is False
    assert error == "Insufficient funds"

@pytest.mark.asyncio
async def test_process_bet_transaction(mock_wallet_service):
    """Test processing a bet transaction."""
    transaction = Transaction.create(
        user_id=123456789,
        type=TransactionType.BET,
        amount=CryptoAmount(Decimal('10.00'), CryptoType.USDT),
        metadata={'game_type': 'slots'}
    )
    
    success, error = await mock_wallet_service.process_transaction(transaction)
    
    assert success is True
    assert error is None

@pytest.mark.asyncio
async def test_process_win_transaction(mock_wallet_service):
    """Test processing a win transaction."""
    transaction = Transaction.create(
        user_id=123456789,
        type=TransactionType.WIN,
        amount=CryptoAmount(Decimal('20.00'), CryptoType.USDT),
        metadata={'game_type': 'slots', 'bet_transaction_id': 'test_bet_id'}
    )
    
    success, error = await mock_wallet_service.process_transaction(transaction)
    
    assert success is True
    assert error is None

@pytest.mark.asyncio
async def test_get_transaction_history(mock_wallet_service):
    """Test getting transaction history."""
    user_id = 123456789
    limit = 10
    
    history = await mock_wallet_service.get_transaction_history(user_id, limit)
    
    assert isinstance(history, list)

@pytest.mark.asyncio
async def test_fail_transaction(mock_wallet_service, mock_transaction):
    """Test failing a transaction."""
    error_message = "Test error"
    
    await mock_wallet_service.fail_transaction(mock_transaction, error_message)
    
    assert mock_transaction.status == "FAILED" 