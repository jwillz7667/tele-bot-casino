from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import logging
import re
from decimal import Decimal
from typing import Optional, List, Sequence, Callable
from datetime import datetime

from ..wallet.transaction import Transaction
from ..wallet.wallet_service import WalletService
from ..user_service import UserService
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)

class WalletHandler(BaseHandler):
    """Handler for wallet-related commands and callbacks."""
    
    def __init__(self, user_service: UserService, wallet_service: WalletService):
        """
        Initialize wallet handler.
        
        Args:
            user_service: User service instance
            wallet_service: Wallet service instance
        """
        self.user_service = user_service
        self.wallet_service = wallet_service
        logger.info("WalletHandler initialized")
    
    @staticmethod
    def _get_transaction_sort_key(tx: Transaction) -> datetime:
        """Get the sort key for a transaction."""
        return tx.created_at
    
    async def handle_deposit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle deposit command.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        try:
            user_id = update.effective_user.id
            
            # Check if user is registered
            if not await self.user_service.is_user_registered(user_id):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Please use /start to register first."
                )
                return
            
            # Extract amount from command
            if not context.args or not re.match(r'^\d+(\.\d{1,2})?$', context.args[0]):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Please specify a valid amount: /deposit <amount>"
                )
                return
            
            amount = Decimal(context.args[0])
            if amount <= 0:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Amount must be greater than 0"
                )
                return
            
            # Create deposit transaction
            if await self.wallet_service.create_transaction(
                user_id=user_id,
                type="deposit",
                amount=amount,
                currency="USD"
            ):
                # Get updated balance
                balance = await self.wallet_service.get_user_balance(user_id, "USD")
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        f"✅ Deposited: ${amount:.2f}\n"
                        f"Current balance: ${balance:.2f}"
                    ),
                    parse_mode=ParseMode.HTML
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Failed to process deposit. Please try again later."
                )
        
        except Exception as e:
            logger.error(
                f"Error in deposit handler: {str(e)}",
                exc_info=True,
                extra={"user_id": update.effective_user.id}
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ An error occurred. Please try again later."
            )
    
    async def handle_withdraw(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle withdraw command.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        try:
            user_id = update.effective_user.id
            
            # Check if user is registered
            if not await self.user_service.is_user_registered(user_id):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Please use /start to register first."
                )
                return
            
            # Extract amount from command
            if not context.args or not re.match(r'^\d+(\.\d{1,2})?$', context.args[0]):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Please specify a valid amount: /withdraw <amount>"
                )
                return
            
            amount = Decimal(context.args[0])
            if amount <= 0:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Amount must be greater than 0"
                )
                return
            
            # Check balance
            balance = await self.wallet_service.get_user_balance(user_id, "USD")
            if balance < amount:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"❌ Insufficient balance. Current balance: ${balance:.2f}"
                )
                return
            
            # Create withdrawal transaction
            if await self.wallet_service.create_transaction(
                user_id=user_id,
                type="withdraw",
                amount=amount,
                currency="USD"
            ):
                # Get updated balance
                new_balance = await self.wallet_service.get_user_balance(user_id, "USD")
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        f"✅ Withdrawn: ${amount:.2f}\n"
                        f"Current balance: ${new_balance:.2f}"
                    ),
                    parse_mode=ParseMode.HTML
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Failed to process withdrawal. Please try again later."
                )
        
        except Exception as e:
            logger.error(
                f"Error in withdraw handler: {str(e)}",
                exc_info=True,
                extra={"user_id": update.effective_user.id}
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ An error occurred. Please try again later."
            )
    
    async def handle_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle balance command.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        try:
            user_id = update.effective_user.id
            
            # Check if user is registered
            if not await self.user_service.is_user_registered(user_id):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Please use /start to register first."
                )
                return
            
            # Get balance
            balance = await self.wallet_service.get_user_balance(user_id, "USD")
            
            # Get recent transactions
            transactions: List[Transaction] = await self.wallet_service.get_user_transactions(user_id)
            recent_txs: List[Transaction] = sorted(
                transactions,
                key=self._get_transaction_sort_key,
                reverse=True
            )[:5]
            
            # Format message
            msg = f"💰 Current balance: ${balance:.2f}\n\n"
            
            if recent_txs:
                msg += "Recent transactions:\n"
                for tx in recent_txs:
                    symbol = "+" if tx.type in ["deposit", "win", "bonus"] else "-"
                    msg += (
                        f"{tx.created_at.strftime('%Y-%m-%d %H:%M')} "
                        f"{symbol}${abs(tx.amount):.2f} "
                        f"({tx.type})\n"
                    )
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=msg,
                parse_mode=ParseMode.HTML
            )
        
        except Exception as e:
            logger.error(
                f"Error in balance handler: {str(e)}",
                exc_info=True,
                extra={"user_id": update.effective_user.id}
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ An error occurred. Please try again later."
            ) 