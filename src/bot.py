from dotenv import load_dotenv
from functools import wraps
import logging
import os

from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram import Update
from telegram.ext import ContextTypes

from user_service import UserService
from wallet.wallet_service import WalletService
from handlers.start_handler import StartHandler
from handlers.wallet_handler import WalletHandler
from handlers.help_handler import HelpHandler
from init_db import init_db

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def require_registered(func):
    """Decorator to ensure user is registered before handling command."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user:
            return
        
        user_id = update.effective_user.id
        if not await user_service.is_user_registered(user_id):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Please use /start to register first."
            )
            return
        
        await user_service.update_last_active(user_id)
        return await func(update, context)
    
    return wrapper

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the dispatcher."""
    logger.error(
        f"Error handling update: {context.error}",
        exc_info=context.error
    )
    
    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ An error occurred. Please try again later."
        )

def main():
    """Initialize and run the bot."""
    try:
        # Initialize database and create session factory
        Session = init_db()
        
        # Initialize services
        global user_service, wallet_service
        user_service = UserService(Session)
        wallet_service = WalletService(Session)
        
        # Initialize handlers
        start_handler = StartHandler(user_service, wallet_service)
        wallet_handler = WalletHandler(user_service, wallet_service)
        help_handler = HelpHandler()
        
        # Create application
        app = ApplicationBuilder().token(os.getenv('TELEGRAM_TOKEN')).build()
        
        # Add handlers
        app.add_handler(CommandHandler('start', start_handler.handle))
        app.add_handler(CommandHandler('help', help_handler.handle))
        
        app.add_handler(CommandHandler('deposit', wallet_handler.handle_deposit))
        app.add_handler(CommandHandler('withdraw', wallet_handler.handle_withdraw))
        app.add_handler(CommandHandler('balance', wallet_handler.handle_balance))
        
        # Add error handler
        app.add_error_handler(error_handler)
        
        # Start the bot
        logger.info("Starting bot...")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main() 