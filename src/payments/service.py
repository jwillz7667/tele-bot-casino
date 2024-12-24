from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
import logging
import os
from decimal import Decimal

from .provider import (
    PaymentProvider, PaymentIntent, PaymentStatus,
    StripeProvider
)
from ..wallet import CryptoAmount, CryptoType
from ..wallet.transaction import Transaction, TransactionType

logger = logging.getLogger(__name__)

class PaymentService:
    """Service for managing payments and payment providers."""
    
    def __init__(self, wallet_service):
        """Initialize payment service with configured providers."""
        self.wallet_service = wallet_service
        self.providers: Dict[str, PaymentProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Initialize configured payment providers."""
        # Initialize Stripe if configured
        stripe_key = os.getenv("STRIPE_API_KEY")
        stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if stripe_key:
            self.providers["stripe"] = StripeProvider(
                api_key=stripe_key,
                webhook_secret=stripe_webhook_secret
            )
        
        # Add more providers here as needed
        
        if not self.providers:
            logger.warning("No payment providers configured!")
    
    async def create_deposit(
        self,
        user_id: int,
        amount: CryptoAmount,
        provider_id: str = "stripe"
    ) -> Tuple[PaymentIntent, str]:
        """
        Create a new deposit request.
        
        Args:
            user_id: User ID
            amount: Amount to deposit
            provider_id: Payment provider to use
            
        Returns:
            Tuple of (PaymentIntent, payment_url)
        
        Raises:
            PaymentError: If payment creation fails
        """
        provider = self.providers.get(provider_id)
        if not provider:
            raise ValueError(f"Payment provider {provider_id} not configured")
        
        # Create payment intent with provider
        payment_intent, payment_url = await provider.create_payment(
            amount=amount,
            metadata={'user_id': user_id}
        )
        
        # Create pending deposit transaction
        transaction = Transaction.create(
            user_id=user_id,
            type=TransactionType.DEPOSIT,
            amount=amount,
            metadata={
                'payment_intent_id': payment_intent.id,
                'provider_id': provider_id
            }
        )
        
        # Store transaction (implementation depends on your storage solution)
        await self.wallet_service.store_pending_transaction(transaction)
        
        return payment_intent, payment_url
    
    async def process_webhook(
        self,
        provider_id: str,
        data: Dict
    ) -> None:
        """
        Process payment provider webhook.
        
        Args:
            provider_id: Payment provider ID
            data: Webhook payload
        """
        provider = self.providers.get(provider_id)
        if not provider:
            logger.error(f"Webhook received for unknown provider: {provider_id}")
            return
        
        try:
            # Process webhook data
            payment_intent = await provider.process_webhook(data)
            if not payment_intent:
                return
            
            # Find corresponding transaction
            transaction = await self.wallet_service.get_pending_transaction(
                payment_intent.id
            )
            if not transaction:
                logger.error(f"No transaction found for payment {payment_intent.id}")
                return
            
            if payment_intent.status == PaymentStatus.COMPLETED:
                # Complete the deposit
                await self.wallet_service.process_transaction(transaction)
                logger.info(
                    f"Deposit completed: {transaction.amount} "
                    f"for user {transaction.user_id}"
                )
                
            elif payment_intent.status == PaymentStatus.FAILED:
                # Mark transaction as failed
                await self.wallet_service.fail_transaction(
                    transaction,
                    error=payment_intent.error_message
                )
                logger.warning(
                    f"Deposit failed: {transaction.amount} "
                    f"for user {transaction.user_id}"
                )
            
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
    
    async def check_pending_payments(self) -> None:
        """Check status of pending payments and update as needed."""
        pending_transactions = await self.wallet_service.get_pending_transactions()
        
        for transaction in pending_transactions:
            provider_id = transaction.metadata.get('provider_id')
            payment_intent_id = transaction.metadata.get('payment_intent_id')
            
            if not provider_id or not payment_intent_id:
                continue
            
            provider = self.providers.get(provider_id)
            if not provider:
                continue
            
            try:
                # Check payment status
                status = await provider.check_payment_status(PaymentIntent(
                    id=payment_intent_id,
                    amount=transaction.amount,
                    status=PaymentStatus.PENDING,
                    provider_id=provider_id,
                    provider_data={'payment_intent_id': payment_intent_id},
                    created_at=transaction.timestamp
                ))
                
                if status == PaymentStatus.COMPLETED:
                    # Complete the deposit
                    await self.wallet_service.process_transaction(transaction)
                    logger.info(
                        f"Deposit completed: {transaction.amount} "
                        f"for user {transaction.user_id}"
                    )
                    
                elif status == PaymentStatus.FAILED:
                    # Mark transaction as failed
                    await self.wallet_service.fail_transaction(
                        transaction,
                        error="Payment failed or expired"
                    )
                    logger.warning(
                        f"Deposit failed: {transaction.amount} "
                        f"for user {transaction.user_id}"
                    )
                
            except Exception as e:
                logger.error(
                    f"Error checking payment status for {payment_intent_id}: {str(e)}"
                ) 