from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any, Tuple
import logging
from datetime import datetime, timedelta

try:
    import stripe
except ImportError:
    stripe = None

from ..wallet import CryptoType, CryptoAmount

logger = logging.getLogger(__name__)

class PaymentError(Exception):
    """Exception raised for payment-related errors."""
    pass

class PaymentStatus(Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"

@dataclass
class PaymentIntent:
    """Represents a payment intent with provider-specific details."""
    id: str
    amount: CryptoAmount
    status: PaymentStatus
    provider_id: str
    provider_data: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class PaymentProvider(ABC):
    """Abstract base class for payment providers."""
    
    def __init__(self, api_key: str, **kwargs):
        """Initialize the payment provider with API credentials."""
        self.api_key = api_key
        self._configure(**kwargs)
    
    @abstractmethod
    def _configure(self, **kwargs) -> None:
        """Configure the payment provider with additional settings."""
        pass
    
    @abstractmethod
    async def create_payment(
        self,
        amount: CryptoAmount,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[PaymentIntent, str]:
        """
        Create a new payment intent.
        
        Args:
            amount: Amount to charge
            metadata: Additional payment metadata
            
        Returns:
            Tuple of (PaymentIntent, payment_url)
            payment_url is where the user should be directed to complete payment
        """
        pass
    
    @abstractmethod
    async def check_payment_status(
        self,
        payment_intent: PaymentIntent
    ) -> PaymentStatus:
        """
        Check the current status of a payment.
        
        Args:
            payment_intent: Payment intent to check
            
        Returns:
            Current payment status
        """
        pass
    
    @abstractmethod
    async def process_webhook(
        self,
        data: Dict[str, Any]
    ) -> Optional[PaymentIntent]:
        """
        Process a webhook notification from the payment provider.
        
        Args:
            data: Webhook payload
            
        Returns:
            Updated PaymentIntent if relevant, None otherwise
        """
        pass

class StripeProvider(PaymentProvider):
    """Stripe payment provider implementation."""
    
    def _configure(self, **kwargs) -> None:
        """Configure Stripe-specific settings."""
        if stripe is None:
            raise ImportError(
                "The 'stripe' package is required to use the Stripe payment provider. "
                "Please install it with 'pip install stripe'"
            )
        stripe.api_key = self.api_key
        self.client = stripe
        self.webhook_secret = kwargs.get("webhook_secret")
    
    async def create_payment(
        self,
        amount: CryptoAmount,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[PaymentIntent, str]:
        """Create a Stripe payment intent."""
        try:
            # Convert crypto amount to fiat (USD cents)
            amount_usd = self._convert_to_usd_cents(amount)
            
            # Create Stripe session
            session = await self.client.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'Deposit {amount}',
                        },
                        'unit_amount': amount_usd,
                    },
                    'quantity': 1,
                }],
                metadata=metadata or {},
                mode='payment',
                expires_at=int((datetime.now() + timedelta(minutes=30)).timestamp())
            )
            
            # Create payment intent
            intent = PaymentIntent(
                id=session.id,
                amount=amount,
                status=PaymentStatus.PENDING,
                provider_id='stripe',
                provider_data={'session_id': session.id},
                created_at=datetime.fromtimestamp(session.created),
                expires_at=datetime.fromtimestamp(session.expires_at)
            )
            
            return intent, session.url
            
        except Exception as e:
            logger.error(f"Failed to create Stripe payment: {str(e)}")
            raise PaymentError(f"Failed to create payment: {str(e)}")
    
    async def check_payment_status(
        self,
        payment_intent: PaymentIntent
    ) -> PaymentStatus:
        """Check Stripe payment status."""
        try:
            session = await self.client.checkout.Session.retrieve(
                payment_intent.provider_data['session_id']
            )
            
            status_map = {
                'open': PaymentStatus.PENDING,
                'complete': PaymentStatus.COMPLETED,
                'expired': PaymentStatus.EXPIRED
            }
            
            return status_map.get(session.status, PaymentStatus.FAILED)
            
        except Exception as e:
            logger.error(f"Failed to check Stripe payment status: {str(e)}")
            return PaymentStatus.FAILED
    
    async def process_webhook(
        self,
        data: Dict[str, Any]
    ) -> Optional[PaymentIntent]:
        """Process Stripe webhook."""
        try:
            event = self.client.Webhook.construct_event(
                data['payload'],
                data['signature'],
                self.webhook_secret
            )
            
            if event.type == 'checkout.session.completed':
                session = event.data.object
                return PaymentIntent(
                    id=session.id,
                    amount=self._convert_from_usd_cents(session.amount_total),
                    status=PaymentStatus.COMPLETED,
                    provider_id='stripe',
                    provider_data={'session_id': session.id},
                    created_at=datetime.fromtimestamp(session.created),
                    completed_at=datetime.now()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to process Stripe webhook: {str(e)}")
            return None
    
    def _convert_to_usd_cents(self, amount: CryptoAmount) -> int:
        """Convert crypto amount to USD cents."""
        # In a real implementation, this would use current exchange rates
        # For now, using simple conversion for demonstration
        if amount.currency == CryptoType.BTC:
            return int(amount.amount * 30000 * 100)  # $30,000 per BTC
        elif amount.currency == CryptoType.ETH:
            return int(amount.amount * 2000 * 100)   # $2,000 per ETH
        else:
            return int(amount.amount * 100)  # Assume stablecoins

    def _convert_from_usd_cents(self, cents: int) -> CryptoAmount:
        """Convert USD cents to crypto amount."""
        # This is a simplified conversion
        # Real implementation would use current exchange rates
        return CryptoAmount(
            amount=Decimal(cents) / Decimal(100),
            currency=CryptoType.USDT
        ) 