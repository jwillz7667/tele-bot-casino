from typing import Optional, Any, Dict, List
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import logging

from ..wallet import WalletService, CryptoType, CryptoAmount
from ..user_service import UserService
from ..games import game_manager

logger = logging.getLogger(__name__)

class BaseHandler:
    """Base class for all command handlers with common functionality."""
    
    def __init__(
        self,
        wallet_service: WalletService,
        user_service: UserService
    ):
        """
        Initialize the handler.
        
        Args:
            wallet_service: Service for managing user wallets
            user_service: Service for managing user data
        """
        self.wallet_service = wallet_service
        self.user_service = user_service
    
    async def ensure_registered(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """
        Ensure user is registered before proceeding.
        
        Args:
            update: Telegram update
            context: Callback context
            
        Returns:
            bool: True if user is registered, False otherwise
        """
        user = update.effective_user
        if not user:
            await update.message.reply_text(
                "Error: Could not identify user. Please try again."
            )
            return False
        
        if not await self.user_service.is_registered(user.id):
            await update.message.reply_text(
                "You need to register first. Use /start to register."
            )
            return False
            
        return True
    
    async def get_balances_text(self, user_id: int) -> str:
        """
        Get formatted balance text for all cryptocurrencies.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            str: Formatted balance text
        """
        balance = await self.wallet_service.get_balance(user_id)
        
        balance_lines = []
        for crypto_type in CryptoType:
            amount = balance.get_balance(crypto_type)
            balance_lines.append(f"{crypto_type.value}: {amount}")
        
        return "💰 *Your Balances:*\n" + "\n".join(balance_lines)
    
    def create_menu_keyboard(self, buttons: List[Dict[str, str]]) -> InlineKeyboardMarkup:
        """
        Create an inline keyboard markup from a list of button definitions.
        
        Args:
            buttons: List of button definitions, each with 'text' and 'callback_data'
            
        Returns:
            InlineKeyboardMarkup: The created keyboard markup
        """
        keyboard = []
        row = []
        
        for button in buttons:
            row.append(
                InlineKeyboardButton(
                    text=button['text'],
                    callback_data=button['callback_data']
                )
            )
            
            if len(row) == 2:  # Two buttons per row
                keyboard.append(row)
                row = []
        
        if row:  # Add any remaining buttons
            keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)
    
    async def send_error(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        message: str
    ) -> None:
        """
        Send an error message to the user.
        
        Args:
            update: Telegram update
            context: Callback context
            message: Error message to send
        """
        try:
            error_text = f"❌ Error: {message}"
            
            if update.callback_query:
                await update.callback_query.message.edit_text(
                    text=error_text,
                    parse_mode=ParseMode.HTML
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=error_text,
                    parse_mode=ParseMode.HTML
                )
        
        except Exception as e:
            logger.error(
                f"Error sending error message: {str(e)}",
                exc_info=True,
                extra={
                    "user_id": update.effective_user.id,
                    "error_message": message
                }
            )
    
    async def send_success(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        message: str,
        keyboard: Optional[InlineKeyboardMarkup] = None
    ) -> None:
        """
        Send a success message to the user.
        
        Args:
            update: Telegram update
            context: Callback context
            message: Success message
            keyboard: Optional inline keyboard
        """
        if update.callback_query:
            await update.callback_query.message.reply_text(
                f"✅ {message}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                f"✅ {message}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
    
    def get_game_keyboard(self, game_type: str) -> InlineKeyboardMarkup:
        """
        Get the game control keyboard.
        
        Args:
            game_type: Type of game
            
        Returns:
            InlineKeyboardMarkup: Game control keyboard
        """
        game = game_manager.get_game_instance(game_type, 0)  # Temp instance for rules
        
        buttons = [
            {'text': '🎮 Play', 'callback_data': f'play_{game_type}'},
            {'text': '📋 Rules', 'callback_data': f'rules_{game_type}'},
            {'text': '💰 Balance', 'callback_data': 'balance'},
            {'text': '🏠 Main Menu', 'callback_data': 'menu'}
        ]
        
        return self.create_menu_keyboard(buttons)
    
    def get_currency_keyboard(
        self,
        action: str,
        game_type: Optional[str] = None
    ) -> InlineKeyboardMarkup:
        """
        Get cryptocurrency selection keyboard.
        
        Args:
            action: Action to perform with selected currency
            game_type: Optional game type for context
            
        Returns:
            InlineKeyboardMarkup: Currency selection keyboard
        """
        buttons = []
        for crypto in CryptoType:
            callback_data = f"{action}_{crypto.name}"
            if game_type:
                callback_data += f"_{game_type}"
            buttons.append({
                'text': f"{crypto.value}",
                'callback_data': callback_data
            })
        
        buttons.append({
            'text': '🔙 Back',
            'callback_data': 'menu' if not game_type else f'game_{game_type}'
        })
        
        return self.create_menu_keyboard(buttons, columns=2) 