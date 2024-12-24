from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import logging

from .base_handler import BaseHandler

logger = logging.getLogger(__name__)

class HelpHandler(BaseHandler):
    """Handler for help-related commands."""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /help command.
        
        Args:
            update: Telegram update
            context: Callback context
        """
        try:
            help_text = (
                "🎮 *Available Commands*\n\n"
                "/start - Start the bot and register\n"
                "/help - Show this help message\n"
                "/deposit - Deposit funds\n"
                "/withdraw - Withdraw funds\n"
                "/balance - Check your balance\n\n"
                "💰 *Managing Your Wallet*\n"
                "• Use /deposit <amount> to add funds\n"
                "• Use /withdraw <amount> to withdraw funds\n"
                "• Use /balance to check your current balance\n\n"
                "❓ Need help? Contact support: @support"
            )
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=help_text,
                parse_mode=ParseMode.MARKDOWN
            )
        
        except Exception as e:
            logger.error(
                f"Error in help handler: {str(e)}",
                exc_info=True,
                extra={"user_id": update.effective_user.id}
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ An error occurred. Please try again later."
            ) 