from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal

from ..user_service import Base

class Transaction(Base):
    """Model representing a transaction in the system."""
    
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)  # deposit, withdraw, win, loss, bonus
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    currency = Column(String(10), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    
    def __init__(
        self,
        user_id: int,
        type: str,
        amount: Decimal,
        currency: str,
        status: str = "pending"
    ):
        """
        Initialize a new transaction.
        
        Args:
            user_id: User ID
            type: Transaction type
            amount: Transaction amount
            currency: Currency type
            status: Transaction status
        """
        self.user_id = user_id
        self.type = type
        self.amount = amount
        self.currency = currency
        self.status = status
    
    def __repr__(self) -> str:
        """String representation of the transaction."""
        return (
            f"<Transaction(id={self.id}, "
            f"user_id={self.user_id}, "
            f"type='{self.type}', "
            f"amount={self.amount}, "
            f"currency='{self.currency}', "
            f"status='{self.status}')>"
        ) 