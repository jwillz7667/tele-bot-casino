from decimal import Decimal
from typing import Optional, Dict, Any
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import logging

from .base_handler import BaseHandler
from ..wallet import (
    CryptoType, CryptoAmount, WalletError,
    InsufficientFundsError, InvalidAmountError
)
from ..wallet.transaction import TransactionType, Transaction
from ..payments.service import PaymentService
from ..payments.provider import PaymentStatus

logger = logging.getLogger(__name__)

class PaymentHandler(BaseHandler):
    """Handler for payment-related commands and operations."""
    
    def __init__(self, payment_service: PaymentService, *args, **kwargs):
        """Initialize payment handler."""
        super().__init__(*args, **kwargs)
        self.payment_service = payment_service
    
    async def deposit_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /deposit command."""
        if not await self.ensure_registered(update, context):
            return
        
        text = (
            "💰 *Deposit Funds*\n\n"
            "Select the cryptocurrency you want to deposit:"
        )
        
        keyboard = self.get_currency_keyboard('deposit')
        
        if update.callback_query:
            await update.callback_query.message.edit_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
    
    async def handle_deposit_amount(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        crypto_type: CryptoType
    ) -> None:
        """
        Handle deposit amount input.
        
        Args:
            update: Telegram update
            context: Callback context
            crypto_type: Selected cryptocurrency
        """
        if not update.message or not update.message.text:
            return
        
        try:
            amount = Decimal(update.message.text.strip())
            crypto_amount = CryptoAmount(amount, crypto_type)
            
            # Create deposit request
            payment_intent, payment_url = await self.payment_service.create_deposit(
                user_id=update.effective_user.id,
                amount=crypto_amount
            )
            
            text = (
                f"💳 *Deposit {crypto_amount}*\n\n"
                "Click the button below to complete your deposit using our secure payment processor.\n\n"
                "⚠️ *Important:*\n"
                "• The payment link will expire in 30 minutes\n"
                "• Your balance will be updated automatically after payment is confirmed\n"
                "• Minimum deposit: {MIN_DEPOSIT}\n"
                "• Maximum deposit: {MAX_DEPOSIT}"
            )
            
            buttons = [
                {
                    'text': '💳 Pay Now',
                    'url': payment_url
                },
                {
                    'text': '🔄 Check Status',
                    'callback_data': f'check_deposit_{payment_intent.id}'
                },
                {
                    'text': '❌ Cancel',
                    'callback_data': 'wallet_menu'
                }
            ]
            keyboard = self.create_menu_keyboard(buttons)
            
            await update.message.reply_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
            
        except ValueError:
            await self.send_error(
                update,
                context,
                "Please enter a valid number for the deposit amount."
            )
    
    async def check_deposit_status(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        payment_id: str
    ) -> None:
        """
        Check status of a deposit.
        
        Args:
            update: Telegram update
            context: Callback context
            payment_id: Payment intent ID to check
        """
        # Get transaction status
        transaction = await self.wallet_service.get_pending_transaction(payment_id)
        if not transaction:
            await self.send_error(
                update,
                context,
                "Deposit not found or already processed."
            )
            return
        
        provider_id = transaction.metadata.get('provider_id')
        if not provider_id:
            await self.send_error(
                update,
                context,
                "Invalid deposit data."
            )
            return
        
        # Check payment status
        provider = self.payment_service.providers.get(provider_id)
        if not provider:
            await self.send_error(
                update,
                context,
                "Payment provider not available."
            )
            return
        
        status = await provider.check_payment_status(payment_id)
        
        status_messages = {
            PaymentStatus.PENDING: "⏳ Your deposit is pending...",
            PaymentStatus.COMPLETED: "✅ Deposit completed! Your balance has been updated.",
            PaymentStatus.FAILED: "❌ Deposit failed. Please try again.",
            PaymentStatus.EXPIRED: "⚠️ Deposit expired. Please create a new deposit request."
        }
        
        text = (
            f"💰 *Deposit Status*\n\n"
            f"Amount: {transaction.amount}\n"
            f"Status: {status_messages.get(status, 'Unknown')}"
        )
        
        buttons = []
        if status == PaymentStatus.PENDING:
            buttons.extend([
                {
                    'text': '🔄 Refresh',
                    'callback_data': f'check_deposit_{payment_id}'
                },
                {
                    'text': '❌ Cancel',
                    'callback_data': 'wallet_menu'
                }
            ])
        else:
            buttons.append({
                'text': '🔙 Back to Wallet',
                'callback_data': 'wallet_menu'
            })
        
        keyboard = self.create_menu_keyboard(buttons)
        
        await update.callback_query.message.edit_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        ) 