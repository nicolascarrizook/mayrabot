"""
Meal Replacement Handler (Motor 3)
"""

import logging
from typing import Dict, Any, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from telegram_bot.config import settings, States
from telegram_bot.utils import keyboards, formatters, validators
from telegram_bot.utils.api_client import api_client, APIError

logger = logging.getLogger(__name__)


async def start_meal_replacement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start meal replacement process."""
    query = update.callback_query
    if query:
        await query.answer()
        keyboard = keyboards.get_meal_type_keyboard()
        await query.edit_message_text(
            f"{settings.EMOJI_FOOD} ¿Qué comida necesitas reemplazar?",
            reply_markup=keyboard
        )
    else:
        keyboard = keyboards.get_meal_type_keyboard()
        await update.message.reply_text(
            f"{settings.EMOJI_FOOD} ¿Qué comida necesitas reemplazar?",
            reply_markup=keyboard
        )
    
    # Initialize replacement data
    context.user_data['replacement_data'] = {}
    
    return States.MEAL_TYPE


async def receive_meal_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive meal type selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract meal type from callback data
    meal_type = query.data.split('_', 1)[1]  # meal_desayuno
    context.user_data['replacement_data']['meal_type'] = meal_type
    
    await query.edit_message_text(
        "¿Por qué necesitas reemplazar esta comida?\n\n"
        "(Ej: no me gusta, alergia, no consigo ingredientes, quiero variar)"
    )
    
    return States.REASON


async def receive_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive replacement reason."""
    reason = update.message.text
    
    # Validate
    is_valid, error_msg = validators.validate_text_list(reason, "razón", max_length=200)
    if not is_valid:
        await update.message.reply_text(
            f"{settings.EMOJI_ERROR} {error_msg}\n\n"
            "Por favor, describe brevemente la razón:"
        )
        return States.REASON
    
    # Store and continue
    context.user_data['replacement_data']['reason'] = validators.sanitize_input(reason)
    
    await update.message.reply_text(
        "¿Hay algún ingrediente específico que debas evitar?\n\n"
        "(Ej: gluten, lácteos, huevo. Si no hay ninguno, escribe 'no')"
    )
    
    return States.AVOID_INGREDIENTS


async def receive_avoid_ingredients(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive ingredients to avoid."""
    ingredients_text = update.message.text
    
    # Validate
    is_valid, error_msg = validators.validate_text_list(ingredients_text, "ingredientes")
    if not is_valid:
        await update.message.reply_text(
            f"{settings.EMOJI_ERROR} {error_msg}\n\n"
            "Por favor, lista los ingredientes a evitar o escribe 'no':"
        )
        return States.AVOID_INGREDIENTS
    
    # Process ingredients
    if ingredients_text.lower() in ['no', 'ninguno', 'ninguna', 'n/a']:
        avoid_ingredients = []
    else:
        avoid_ingredients = [ing.strip() for ing in ingredients_text.split(',')]
    
    context.user_data['replacement_data']['avoid_ingredients'] = avoid_ingredients
    
    # Show economic level selection
    keyboard = keyboards.get_economic_level_keyboard()
    await update.message.reply_text(
        "¿Qué nivel económico prefieres para las alternativas?",
        reply_markup=keyboard
    )
    
    return States.SEARCHING


async def handle_economic_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle economic level selection and search for alternatives."""
    query = update.callback_query
    await query.answer()
    
    # Extract economic level
    economic_level = query.data.split('_')[1]
    
    # Show searching message
    await query.edit_message_text(
        formatters.format_progress_message('searching_alternatives')
    )
    
    try:
        # Get meal type from context
        meal_type = context.user_data['replacement_data']['meal_type']
        avoid_ingredients = context.user_data['replacement_data']['avoid_ingredients']
        
        # Search for alternatives
        alternatives = await api_client.find_meal_alternatives(
            meal_type=meal_type,
            avoid_ingredients=avoid_ingredients,
            economic_level=economic_level,
            limit=5
        )
        
        if not alternatives:
            await query.edit_message_text(
                f"{settings.EMOJI_INFO} No encontré alternativas que cumplan con tus criterios.\n\n"
                "Intenta con menos restricciones o consulta con tu nutricionista.",
                reply_markup=keyboards.get_back_to_menu_keyboard()
            )
            context.user_data.clear()
            return ConversationHandler.END
        
        # Store alternatives in context
        context.user_data['alternatives'] = alternatives
        
        # Format and show alternatives
        message = formatters.format_meal_alternatives(alternatives, meal_type)
        keyboard = keyboards.get_alternative_selection_keyboard(alternatives)
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        return States.SELECTING_ACTION
        
    except APIError as e:
        logger.error(f"API error searching alternatives: {str(e)}")
        error_msg = formatters.format_error_message('api_error', str(e))
        
        keyboard = keyboards.get_back_to_menu_keyboard()
        await query.edit_message_text(
            error_msg,
            reply_markup=keyboard
        )
        context.user_data.clear()
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Unexpected error searching alternatives: {str(e)}")
        error_msg = formatters.format_error_message('unknown')
        
        keyboard = keyboards.get_back_to_menu_keyboard()
        await query.edit_message_text(
            error_msg,
            reply_markup=keyboard
        )
        context.user_data.clear()
        return ConversationHandler.END


async def handle_alternative_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle selection of a specific alternative."""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'search_again':
        # Start over
        keyboard = keyboards.get_meal_type_keyboard()
        await query.edit_message_text(
            f"{settings.EMOJI_FOOD} ¿Qué comida necesitas reemplazar?",
            reply_markup=keyboard
        )
        context.user_data['replacement_data'] = {}
        return States.MEAL_TYPE
    
    elif query.data == 'cancel':
        await query.edit_message_text(
            f"{settings.EMOJI_INFO} Búsqueda cancelada.",
            reply_markup=keyboards.get_back_to_menu_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    elif query.data.startswith('select_alt_'):
        # Extract alternative index
        alt_index = int(query.data.split('_')[2])
        alternatives = context.user_data.get('alternatives', [])
        
        if alt_index < len(alternatives):
            selected = alternatives[alt_index]
            
            # Format detailed recipe info
            detail_message = formatters.format_recipe_detail(selected)
            
            await query.edit_message_text(
                detail_message,
                parse_mode='Markdown',
                reply_markup=keyboards.get_back_to_menu_keyboard()
            )
            
            # Send additional success message
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"{settings.EMOJI_SUCCESS} ¡Excelente elección! Esta receta tiene un valor nutricional "
                     f"equivalente y se ajusta a tus necesidades.\n\n"
                     f"Recuerda seguir las cantidades indicadas para mantener el balance de tu plan."
            )
        
        context.user_data.clear()
        return ConversationHandler.END
    
    return States.SELECTING_ACTION


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text(
        f"{settings.EMOJI_INFO} Búsqueda cancelada. Puedes comenzar de nuevo cuando quieras con /start"
    )
    context.user_data.clear()
    return ConversationHandler.END


def get_meal_replacement_handler() -> ConversationHandler:
    """Get the conversation handler for meal replacement."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_meal_replacement, pattern='^replace_meal$'),
            CommandHandler('reemplazar', start_meal_replacement)
        ],
        states={
            States.MEAL_TYPE: [
                CallbackQueryHandler(receive_meal_type, pattern='^meal_')
            ],
            States.REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_reason)
            ],
            States.AVOID_INGREDIENTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_avoid_ingredients)
            ],
            States.SEARCHING: [
                CallbackQueryHandler(handle_economic_selection, pattern='^economic_')
            ],
            States.SELECTING_ACTION: [
                CallbackQueryHandler(handle_alternative_selection)
            ]
        },
        fallbacks=[
            CommandHandler('cancelar', cancel),
            CommandHandler('cancel', cancel)
        ],
        conversation_timeout=settings.CONVERSATION_TIMEOUT
    )