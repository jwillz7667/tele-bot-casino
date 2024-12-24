from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from .transaction import Transaction
from ..user_service import Base

logger = logging.getLogger(__name__)

class WalletService:
    """Service for managing user wallets and transactions."""
    
    def __init__(self, session_factory: sessionmaker):
        """
        Initialize wallet service.
        
        Args:
            session_factory: SQLAlchemy session factory
        """
        self.session_factory = session_factory
        logger.info("WalletService initialized")
    
    async def create_transaction(self, user_id: int, type: str, amount: Decimal, currency: str) -> bool:
        """
        Create a new transaction.
        
        Args:
            user_id: User ID
            type: Transaction type
            amount: Transaction amount
            currency: Currency type
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            transaction = Transaction(
                user_id=user_id,
                type=type,
                amount=amount,
                currency=currency
            )
            
            with self.session_factory() as session:
                session.add(transaction)
                session.commit()
                
                logger.info(
                    "Transaction created successfully",
                    extra={
                        "user_id": user_id,
                        "type": type,
                        "amount": str(amount),
                        "currency": currency
                    }
                )
                return True
                
        except SQLAlchemyError as e:
            logger.error(
                f"Error creating transaction: {str(e)}",
                exc_info=True,
                extra={
                    "user_id": user_id,
                    "type": type,
                    "amount": str(amount),
                    "currency": currency
                }
            )
            return False
    
    async def get_user_transactions(self, user_id: int) -> List[Transaction]:
        """
        Get all transactions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List[Transaction]: List of transactions
        """
        try:
            with self.session_factory() as session:
                stmt = select(Transaction).where(Transaction.user_id == user_id)
                result = session.execute(stmt)
                return list(result.scalars().all())
                
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting user transactions: {str(e)}",
                exc_info=True,
                extra={"user_id": user_id}
            )
            return []
    
    async def get_user_balance(self, user_id: int, currency: str) -> Decimal:
        """
        Calculate user's balance for a specific currency.
        
        Args:
            user_id: User ID
            currency: Currency type
            
        Returns:
            Decimal: Current balance
        """
        try:
            with self.session_factory() as session:
                # Get all completed transactions for the user and currency
                stmt = select(Transaction).where(
                    Transaction.user_id == user_id,
                    Transaction.currency == currency,
                    Transaction.status == "completed"
                )
                transactions = session.execute(stmt).scalars().all()
                
                # Calculate balance
                balance = Decimal("0")
                for tx in transactions:
                    if tx.type in ["deposit", "win", "bonus"]:
                        balance += tx.amount
                    else:
                        balance -= tx.amount
                
                return balance
                
        except SQLAlchemyError as e:
            logger.error(
                f"Error calculating user balance: {str(e)}",
                exc_info=True,
                extra={
                    "user_id": user_id,
                    "currency": currency
                }
            )
            return Decimal("0")
    
    async def update_transaction_status(self, transaction_id: int, status: str) -> bool:
        """
        Update transaction status.
        
        Args:
            transaction_id: Transaction ID
            status: New status
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.session_factory() as session:
                stmt = select(Transaction).where(Transaction.id == transaction_id)
                transaction = session.execute(stmt).scalar_one_or_none()
                
                if transaction:
                    transaction.status = status
                    transaction.updated_at = datetime.utcnow()
                    session.commit()
                    
                    logger.info(
                        f"Transaction {transaction_id} status updated to {status}",
                        extra={
                            "transaction_id": transaction_id,
                            "status": status
                        }
                    )
                    return True
                    
                logger.warning(
                    f"Transaction {transaction_id} not found",
                    extra={"transaction_id": transaction_id}
                )
                return False
                
        except SQLAlchemyError as e:
            logger.error(
                f"Error updating transaction status: {str(e)}",
                exc_info=True,
                extra={
                    "transaction_id": transaction_id,
                    "status": status
                }
            )
            return False 