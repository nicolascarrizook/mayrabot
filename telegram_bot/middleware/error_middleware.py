"""
Error Middleware for Telegram Bot
"""

import logging
import traceback
from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.config import settings
from telegram_bot.utils import formatters

logger = logging.getLogger(__name__)


async def error_callback(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler for the bot."""
    # Log the error
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    # Collect error information
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)
    
    # Log detailed error for debugging
    if update:
        update_str = update.to_dict() if isinstance(update, Update) else str(update)
        logger.error(f"Update: {update_str}")
    logger.error(f"Traceback:\n{tb_string}")
    
    # Determine error type and send appropriate message to user
    if update and isinstance(update, Update) and update.effective_message:
        error = context.error
        
        # Handle specific error types
        if isinstance(error, TimeoutError):
            error_msg = formatters.format_error_message('timeout')
        elif "API" in str(error):
            error_msg = formatters.format_error_message('api_error')
        elif "validation" in str(error).lower():
            error_msg = formatters.format_error_message('validation_error')
        else:
            error_msg = formatters.format_error_message('unknown')
        
        try:
            # Try to send error message to user
            if update.callback_query:
                await update.callback_query.answer(
                    "Ocurrió un error. Por favor, intenta nuevamente.",
                    show_alert=True
                )
                await update.callback_query.edit_message_text(error_msg)
            else:
                await update.effective_message.reply_text(error_msg)
                
        except Exception as e:
            logger.error(f"Failed to send error message to user: {str(e)}")