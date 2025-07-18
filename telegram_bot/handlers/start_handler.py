"""
Start and Main Menu Handler
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from telegram_bot.config import settings, States
from telegram_bot.utils.keyboards import get_main_menu_keyboard

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    
    welcome_message = f"""
{settings.EMOJI_WELCOME} ¡Hola {user.first_name}!

Soy tu asistente nutricional personalizado. Puedo ayudarte a:

{settings.EMOJI_PLAN} **Crear un plan nutricional personalizado**
   Diseñado específicamente para tus necesidades y objetivos

{settings.EMOJI_FOOD} **Buscar alternativas de comidas**
   Si necesitas reemplazar alguna comida de tu plan

{settings.EMOJI_INFO} **Responder tus dudas**
   Sobre nutrición y tu plan alimenticio

¿Qué te gustaría hacer hoy?
"""
    
    keyboard = get_main_menu_keyboard()
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    return States.SELECTING_ACTION


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle button callbacks from inline keyboards."""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'new_plan':
        # Transition to new plan handler
        from telegram_bot.handlers.new_plan_handler import start_new_plan
        return await start_new_plan(update, context)
    
    elif query.data == 'replace_meal':
        # Transition to meal replacement handler
        from telegram_bot.handlers.meal_replacement_handler import start_meal_replacement
        return await start_meal_replacement(update, context)
    
    elif query.data == 'help':
        # Show help
        from telegram_bot.handlers.help_handler import help_command
        await help_command(update, context)
        return States.SELECTING_ACTION
    
    elif query.data == 'main_menu':
        # Return to main menu
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
            "¿Qué te gustaría hacer?",
            reply_markup=keyboard
        )
        return States.SELECTING_ACTION
    
    else:
        await query.edit_message_text("Opción no reconocida. Por favor, intenta de nuevo.")
        return States.SELECTING_ACTION


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and end the conversation."""
    user = update.effective_user
    
    await update.message.reply_text(
        f"{settings.EMOJI_INFO} Operación cancelada, {user.first_name}.\n\n"
        "Puedes comenzar de nuevo cuando quieras con /start",
        reply_markup=None
    )
    
    # Clear user data
    context.user_data.clear()
    
    return ConversationHandler.END