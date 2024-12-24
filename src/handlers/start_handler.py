from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import logging
from typing import Optional, List
from decimal import Decimal

from ..wallet.transaction import Transaction
from ..wallet.wallet_service import WalletService
from ..user_service import UserService
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)

class StartHandler(BaseHandler):
    """Handler for /start command and initial user registration."""
    
    def __init__(self, user_service: UserService, wallet_service: WalletService):
        """
        Initialize start handler.
        
        Args:
            user_service: User service instance
            wallet_service: Wallet service instance
        """
        self.user_service = user_service
        self.wallet_service = wallet_service
        logger.info("StartHandler initialized")
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /start command.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        try:
            user_id = update.effective_user.id
            
            # Check if user is registered
            if not await self.user_service.is_user_registered(user_id):
                # Register new user
                if not await self.user_service.register_user(user_id):
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="❌ Failed to register user. Please try again later."
                    )
                    return
                
                # Create welcome transaction (bonus)
                welcome_bonus = Decimal("10.00")
                if await self.wallet_service.create_transaction(
                    user_id=user_id,
                    type="bonus",
                    amount=welcome_bonus,
                    currency="USD"
                ):
                    welcome_msg = (
                        "🎉 Welcome to the Casino Bot!\n\n"
                        f"You've received a ${welcome_bonus:.2f} welcome bonus!\n\n"
                        "Use /help to see available commands."
                    )
                else:
                    welcome_msg = (
                        "🎉 Welcome to the Casino Bot!\n\n"
                        "Use /help to see available commands."
                    )
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=welcome_msg,
                    parse_mode=ParseMode.HTML
                )
            else:
                # Update last active timestamp
                await self.user_service.update_last_active(user_id)
                
                # Get user's balance
                balance = await self.wallet_service.get_user_balance(user_id, "USD")
                
                welcome_back_msg = (
                    "👋 Welcome back!\n\n"
                    f"Your current balance: ${balance:.2f}\n\n"
                    "Use /help to see available commands."
                )
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=welcome_back_msg,
                    parse_mode=ParseMode.HTML
                )
        
        except Exception as e:
            logger.error(
                f"Error in start handler: {str(e)}",
                exc_info=True,
                extra={"user_id": update.effective_user.id}
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ An error occurred. Please try again later."
            ) 