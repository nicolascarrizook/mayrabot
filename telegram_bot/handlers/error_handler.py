"""
Error Handler
"""

import logging
import traceback
from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.config import settings

logger = logging.getLogger(__name__)


async def error_callback(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify users of problems."""
    # Log the error before we do anything else
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    # Collect error information
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)
    
    # Build the error message
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    
    error_message = (
        f'An exception was raised while handling an update\n'
        f'<pre>update = {update_str}</pre>\n\n'
        f'<pre>context.error = {str(context.error)}</pre>'
    )
    
    # Log detailed error
    logger.error(f"{error_message}\n\nTraceback:\n{tb_string}")
    
    # Notify user of error
    if update and isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                f"{settings.EMOJI_ERROR} Lo siento, ocurrió un error procesando tu solicitud.\n\n"
                "Por favor, intenta nuevamente. Si el problema persiste, contacta al administrador.",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Failed to send error message to user: {str(e)}")


async def handle_timeout_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle conversation timeout errors."""
    await update.message.reply_text(
        f"{settings.EMOJI_INFO} La conversación ha expirado por inactividad.\n\n"
        "Por favor, usa /start para comenzar de nuevo."
    )


async def handle_api_error(update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception) -> None:
    """Handle API connection errors."""
    logger.error(f"API Error: {str(error)}")
    
    await update.effective_message.reply_text(
        f"{settings.EMOJI_ERROR} Error al conectar con el servidor.\n\n"
        "Por favor, intenta más tarde o contacta al administrador si el problema persiste."
    )


async def handle_validation_error(update: Update, context: ContextTypes.DEFAULT_TYPE, field: str, error: str) -> None:
    """Handle input validation errors."""
    await update.message.reply_text(
        f"{settings.EMOJI_ERROR} Error en {field}:\n{error}\n\n"
        "Por favor, verifica tu entrada e intenta nuevamente."
    )