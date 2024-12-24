from decimal import Decimal
from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime

class CryptoType(Enum):
    """Supported cryptocurrency types."""
    BTC = "Bitcoin"
    ETH = "Ethereum"
    USDT = "Tether"
    BNB = "Binance Coin"
    USDC = "USD Coin"

@dataclass
class CryptoAmount:
    """Represents an amount in a specific cryptocurrency."""
    
    amount: Decimal
    currency: CryptoType
    
    @classmethod
    def from_string(cls, amount_str: str, currency: CryptoType) -> 'CryptoAmount':
        """Create CryptoAmount from string representation."""
        return cls(Decimal(amount_str), currency)
    
    def __str__(self) -> str:
        """String representation with appropriate decimal places."""
        decimal_places = {
            CryptoType.BTC: 8,   # Bitcoin uses 8 decimal places (satoshis)
            CryptoType.ETH: 18,  # Ethereum uses 18 decimal places (wei)
            CryptoType.USDT: 6,  # USDT typically uses 6 decimal places
            CryptoType.BNB: 8,   # BNB uses 8 decimal places
            CryptoType.USDC: 6   # USDC uses 6 decimal places
        }
        places = decimal_places[self.currency]
        return f"{self.amount:.{places}f}"
    
    def __add__(self, other: 'CryptoAmount') -> 'CryptoAmount':
        """Add two crypto amounts of the same currency."""
        if not isinstance(other, CryptoAmount):
            raise TypeError("Can only add CryptoAmount to CryptoAmount")
        if self.currency != other.currency:
            raise ValueError("Cannot add different cryptocurrencies")
        return CryptoAmount(self.amount + other.amount, self.currency)
    
    def __sub__(self, other: 'CryptoAmount') -> 'CryptoAmount':
        """Subtract two crypto amounts of the same currency."""
        if not isinstance(other, CryptoAmount):
            raise TypeError("Can only subtract CryptoAmount from CryptoAmount")
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different cryptocurrencies")
        return CryptoAmount(self.amount - other.amount, self.currency)
    
    def __mul__(self, factor: Decimal) -> 'CryptoAmount':
        """Multiply crypto amount by a factor."""
        return CryptoAmount(self.amount * factor, self.currency)
    
    def __gt__(self, other: 'CryptoAmount') -> bool:
        """Compare if this amount is greater than another."""
        self._validate_comparison(other)
        return self.amount > other.amount
    
    def __lt__(self, other: 'CryptoAmount') -> bool:
        """Compare if this amount is less than another."""
        self._validate_comparison(other)
        return self.amount < other.amount
    
    def __ge__(self, other: 'CryptoAmount') -> bool:
        """Compare if this amount is greater than or equal to another."""
        self._validate_comparison(other)
        return self.amount >= other.amount
    
    def __le__(self, other: 'CryptoAmount') -> bool:
        """Compare if this amount is less than or equal to another."""
        self._validate_comparison(other)
        return self.amount <= other.amount
    
    def _validate_comparison(self, other: 'CryptoAmount') -> None:
        """Validate that two amounts can be compared."""
        if not isinstance(other, CryptoAmount):
            raise TypeError("Can only compare CryptoAmount with CryptoAmount")
        if self.currency != other.currency:
            raise ValueError("Cannot compare different cryptocurrencies")

@dataclass
class CryptoBalance:
    """Represents a user's balance in multiple cryptocurrencies."""
    
    balances: Dict[CryptoType, CryptoAmount]
    last_updated: datetime
    
    @classmethod
    def create_empty(cls) -> 'CryptoBalance':
        """Create a new empty balance for all supported cryptocurrencies."""
        return cls(
            balances={
                crypto: CryptoAmount(Decimal("0"), crypto)
                for crypto in CryptoType
            },
            last_updated=datetime.utcnow()
        )
    
    def get_balance(self, currency: CryptoType) -> CryptoAmount:
        """Get balance for a specific cryptocurrency."""
        return self.balances.get(
            currency,
            CryptoAmount(Decimal("0"), currency)
        )
    
    def update_balance(self, amount: CryptoAmount) -> None:
        """Update balance for a specific cryptocurrency."""
        self.balances[amount.currency] = amount
        self.last_updated = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, str]:
        """Convert balances to dictionary for storage."""
        return {
            crypto.name: str(amount)
            for crypto, amount in self.balances.items()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'CryptoBalance':
        """Create balance from dictionary representation."""
        balances = {
            CryptoType[currency]: CryptoAmount.from_string(amount, CryptoType[currency])
            for currency, amount in data.items()
        }
        return cls(balances, datetime.utcnow())

# Minimum transaction amounts for each cryptocurrency
MIN_TRANSACTION_AMOUNTS = {
    CryptoType.BTC: CryptoAmount(Decimal("0.00001"), CryptoType.BTC),    # 1000 satoshis
    CryptoType.ETH: CryptoAmount(Decimal("0.00001"), CryptoType.ETH),    # 0.00001 ETH
    CryptoType.USDT: CryptoAmount(Decimal("1.00"), CryptoType.USDT),     # 1 USDT
    CryptoType.BNB: CryptoAmount(Decimal("0.00001"), CryptoType.BNB),    # 0.00001 BNB
    CryptoType.USDC: CryptoAmount(Decimal("1.00"), CryptoType.USDC)      # 1 USDC
}

# Maximum transaction amounts for each cryptocurrency
MAX_TRANSACTION_AMOUNTS = {
    CryptoType.BTC: CryptoAmount(Decimal("1.0"), CryptoType.BTC),      # 1 BTC
    CryptoType.ETH: CryptoAmount(Decimal("10.0"), CryptoType.ETH),     # 10 ETH
    CryptoType.USDT: CryptoAmount(Decimal("10000.0"), CryptoType.USDT),# 10000 USDT
    CryptoType.BNB: CryptoAmount(Decimal("100.0"), CryptoType.BNB),    # 100 BNB
    CryptoType.USDC: CryptoAmount(Decimal("10000.0"), CryptoType.USDC) # 10000 USDC
} 