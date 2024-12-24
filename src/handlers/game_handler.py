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
from ..games import game_manager, GameResult

logger = logging.getLogger(__name__)

class GameHandler(BaseHandler):
    """Handler for game-related commands and operations."""
    
    async def games_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /games command."""
        if not await self.ensure_registered(update, context):
            return
        
        await self.show_games_menu(update, context)
    
    async def show_game_menu(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        game_type: str
    ) -> None:
        """
        Show the menu for a specific game.
        
        Args:
            update: Telegram update
            context: Callback context
            game_type: Type of game to show
        """
        game = game_manager.get_game_instance(game_type, update.effective_user.id)
        if not game:
            await self.send_error(update, context, "Game not found.")
            return
        
        text = (
            f"🎮 *{game_type.title()}*\n\n"
            "Select an option:"
        )
        
        keyboard = self.get_game_keyboard(game_type)
        
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
    
    async def show_game_rules(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        game_type: str
    ) -> None:
        """
        Show rules for a specific game.
        
        Args:
            update: Telegram update
            context: Callback context
            game_type: Type of game
        """
        game = game_manager.get_game_instance(game_type, update.effective_user.id)
        if not game:
            await self.send_error(update, context, "Game not found.")
            return
        
        rules_text = game.get_game_rules()
        buttons = [{'text': '🔙 Back', 'callback_data': f'game_{game_type}'}]
        keyboard = self.create_menu_keyboard(buttons)
        
        await update.callback_query.message.edit_text(
            rules_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
    
    async def start_game(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        game_type: str
    ) -> None:
        """
        Start a game session.
        
        Args:
            update: Telegram update
            context: Callback context
            game_type: Type of game to start
        """
        text = (
            f"🎮 *Play {game_type.title()}*\n\n"
            "Select your betting currency:"
        )
        
        keyboard = self.get_currency_keyboard('bet', game_type)
        
        await update.callback_query.message.edit_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
    
    async def handle_bet_amount(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        game_type: str,
        crypto_type: CryptoType
    ) -> None:
        """
        Handle bet amount input for a game.
        
        Args:
            update: Telegram update
            context: Callback context
            game_type: Type of game
            crypto_type: Selected cryptocurrency
        """
        if not update.message or not update.message.text:
            return
        
        try:
            amount = Decimal(update.message.text.strip())
            crypto_amount = CryptoAmount(amount, crypto_type)
            
            # Get game instance
            game = game_manager.get_game_instance(game_type, update.effective_user.id)
            if not game:
                await self.send_error(update, context, "Game not found.")
                return
            
            # Create bet transaction
            bet_transaction = Transaction.create(
                user_id=update.effective_user.id,
                type=TransactionType.BET,
                amount=crypto_amount,
                metadata={'game_type': game_type}
            )
            
            # Process bet
            success, error = await self.wallet_service.process_transaction(
                bet_transaction
            )
            
            if not success:
                await self.send_error(update, context, error or "Failed to place bet.")
                return
            
            # Play game
            result = await game.play(
                player_id=update.effective_user.id,
                bet_amount=crypto_amount
            )
            
            # Process win if any
            if result.win_amount > 0:
                win_transaction = Transaction.create(
                    user_id=update.effective_user.id,
                    type=TransactionType.WIN,
                    amount=result.win_amount,
                    metadata={
                        'game_type': game_type,
                        'bet_transaction_id': bet_transaction.id
                    }
                )
                await self.wallet_service.process_transaction(win_transaction)
            
            # Show result
            await self._show_game_result(
                update,
                context,
                result,
                game_type,
                crypto_type
            )
            
        except (ValueError, InvalidAmountError) as e:
            await self.send_error(
                update,
                context,
                f"Invalid bet amount: {str(e)}"
            )
    
    async def _show_game_result(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        result: GameResult,
        game_type: str,
        crypto_type: CryptoType
    ) -> None:
        """
        Show game result to the user.
        
        Args:
            update: Telegram update
            context: Callback context
            result: Game result
            game_type: Type of game
            crypto_type: Cryptocurrency used
        """
        # Format result message based on game type and outcome
        if game_type == "slots":
            text = self._format_slots_result(result)
        else:
            text = (
                f"🎮 *Game Result*\n\n"
                f"Bet: {result.bet_amount}\n"
                f"Win: {result.win_amount}\n\n"
                f"{result.outcome}"
            )
        
        # Add buttons for next action
        buttons = [
            {'text': '🎮 Play Again', 'callback_data': f'bet_{crypto_type.name}_{game_type}'},
            {'text': '💰 Balance', 'callback_data': 'balance'},
            {'text': '🔙 Back', 'callback_data': f'game_{game_type}'}
        ]
        keyboard = self.create_menu_keyboard(buttons)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
    
    def _format_slots_result(self, result: GameResult) -> str:
        """Format slots game result message."""
        grid = result.game_data.get("grid", [])
        
        # Format grid display
        grid_display = "\n".join(
            " ".join(symbol for symbol in row)
            for row in grid
        )
        
        return (
            f"🎰 *Slots Result*\n\n"
            f"{grid_display}\n\n"
            f"Bet: {result.bet_amount}\n"
            f"Win: {result.win_amount}\n\n"
            f"{result.outcome}"
        ) 