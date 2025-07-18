"""
New Plan Generation Handler (Motor 1)
"""

import logging
from typing import Dict, Any
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


async def start_new_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start new plan generation process."""
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            f"{settings.EMOJI_PLAN} ¡Excelente! Vamos a crear tu plan nutricional personalizado.\n\n"
            "Necesitaré algunos datos sobre ti. Puedes cancelar en cualquier momento con /cancelar\n\n"
            "Primero, ¿cuál es tu nombre completo?"
        )
    else:
        await update.message.reply_text(
            f"{settings.EMOJI_PLAN} ¡Excelente! Vamos a crear tu plan nutricional personalizado.\n\n"
            "Necesitaré algunos datos sobre ti. Puedes cancelar en cualquier momento con /cancelar\n\n"
            "Primero, ¿cuál es tu nombre completo?"
        )
    
    # Initialize user data
    context.user_data['plan_data'] = {}
    
    return States.NAME


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate name."""
    name = update.message.text
    
    # Validate
    is_valid, error_msg = validators.validate_name(name)
    if not is_valid:
        await update.message.reply_text(
            f"{settings.EMOJI_ERROR} {error_msg}\n\n"
            "Por favor, ingresa tu nombre completo:"
        )
        return States.NAME
    
    # Store and continue
    context.user_data['plan_data']['name'] = validators.sanitize_input(name)
    
    await update.message.reply_text(
        f"Perfecto, {name}. Ahora dime, ¿cuántos años tienes?"
    )
    
    return States.AGE


async def receive_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate age."""
    age_text = update.message.text
    
    # Validate
    is_valid, error_msg = validators.validate_age(age_text)
    if not is_valid:
        await update.message.reply_text(
            f"{settings.EMOJI_ERROR} {error_msg}\n\n"
            "Por favor, ingresa tu edad en años:"
        )
        return States.AGE
    
    # Store and continue
    context.user_data['plan_data']['age'] = int(age_text.strip())
    
    # Send gender selection keyboard
    keyboard = keyboards.get_gender_keyboard()
    await update.message.reply_text(
        "¿Cuál es tu género?",
        reply_markup=keyboard
    )
    
    return States.GENDER


async def receive_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive gender selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract gender from callback data
    gender = query.data.split('_')[1]  # gender_M or gender_F
    context.user_data['plan_data']['gender'] = gender
    
    await query.edit_message_text(
        f"Entendido. Ahora necesito tu altura en centímetros (ej: 170):"
    )
    
    return States.HEIGHT


async def receive_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate height."""
    height_text = update.message.text
    
    # Validate
    is_valid, error_msg = validators.validate_height(height_text)
    if not is_valid:
        await update.message.reply_text(
            f"{settings.EMOJI_ERROR} {error_msg}\n\n"
            "Por favor, ingresa tu altura en centímetros:"
        )
        return States.HEIGHT
    
    # Store and continue
    height_text = height_text.replace(',', '.').strip()
    context.user_data['plan_data']['height'] = float(height_text)
    
    await update.message.reply_text(
        "¿Cuál es tu peso actual en kilogramos? (ej: 70 o 70.5)"
    )
    
    return States.WEIGHT


async def receive_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate weight."""
    weight_text = update.message.text
    
    # Validate
    is_valid, error_msg = validators.validate_weight(weight_text)
    if not is_valid:
        await update.message.reply_text(
            f"{settings.EMOJI_ERROR} {error_msg}\n\n"
            "Por favor, ingresa tu peso en kilogramos:"
        )
        return States.WEIGHT
    
    # Store and continue
    weight_text = weight_text.replace(',', '.').strip()
    context.user_data['plan_data']['weight'] = float(weight_text)
    
    # Send activity level keyboard
    keyboard = keyboards.get_activity_level_keyboard()
    await update.message.reply_text(
        "¿Cuál es tu nivel de actividad física?",
        reply_markup=keyboard
    )
    
    return States.ACTIVITY


async def receive_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive activity level selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract activity from callback data
    activity = query.data.split('_', 1)[1]  # activity_sedentario
    context.user_data['plan_data']['physical_activity'] = activity
    
    await query.edit_message_text(
        "¿Tienes alguna patología o condición médica que deba considerar?\n\n"
        "(Ej: diabetes, hipertensión, etc. Si no tienes ninguna, escribe 'no')"
    )
    
    return States.PATHOLOGIES


async def receive_pathologies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive pathologies information."""
    pathologies = update.message.text
    
    # Validate
    is_valid, error_msg = validators.validate_text_list(pathologies, "patologías")
    if not is_valid:
        await update.message.reply_text(
            f"{settings.EMOJI_ERROR} {error_msg}\n\n"
            "Por favor, describe tus patologías o escribe 'no':"
        )
        return States.PATHOLOGIES
    
    # Store and continue
    context.user_data['plan_data']['pathologies'] = validators.format_list_input(pathologies)
    
    await update.message.reply_text(
        "¿Tienes alguna alergia alimentaria?\n\n"
        "(Ej: gluten, lactosa, frutos secos. Si no tienes, escribe 'no')"
    )
    
    return States.ALLERGIES


async def receive_allergies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive allergies information."""
    allergies = update.message.text
    
    # Validate
    is_valid, error_msg = validators.validate_text_list(allergies, "alergias")
    if not is_valid:
        await update.message.reply_text(
            f"{settings.EMOJI_ERROR} {error_msg}\n\n"
            "Por favor, describe tus alergias o escribe 'no':"
        )
        return States.ALLERGIES
    
    # Store and continue
    context.user_data['plan_data']['allergies'] = validators.format_list_input(allergies)
    
    await update.message.reply_text(
        "¿Tienes alguna preferencia alimentaria?\n\n"
        "(Ej: vegetariano, vegano, sin cerdo. Si no tienes, escribe 'no')"
    )
    
    return States.PREFERENCES


async def receive_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive food preferences."""
    preferences = update.message.text
    
    # Validate
    is_valid, error_msg = validators.validate_text_list(preferences, "preferencias")
    if not is_valid:
        await update.message.reply_text(
            f"{settings.EMOJI_ERROR} {error_msg}\n\n"
            "Por favor, describe tus preferencias o escribe 'no':"
        )
        return States.PREFERENCES
    
    # Store and continue
    context.user_data['plan_data']['preferences'] = validators.format_list_input(preferences)
    
    await update.message.reply_text(
        "¿Hay algún alimento que no te guste o prefieras evitar?\n\n"
        "(Ej: brócoli, hígado, pescado. Si no hay ninguno, escribe 'no')"
    )
    
    return States.DISLIKES


async def receive_dislikes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive food dislikes."""
    dislikes = update.message.text
    
    # Validate
    is_valid, error_msg = validators.validate_text_list(dislikes, "alimentos")
    if not is_valid:
        await update.message.reply_text(
            f"{settings.EMOJI_ERROR} {error_msg}\n\n"
            "Por favor, describe qué no te gusta o escribe 'no':"
        )
        return States.DISLIKES
    
    # Store and continue
    context.user_data['plan_data']['dislikes'] = validators.format_list_input(dislikes)
    
    # Send meals per day keyboard
    keyboard = keyboards.get_meals_per_day_keyboard()
    await update.message.reply_text(
        "¿Cuántas comidas al día prefieres hacer?",
        reply_markup=keyboard
    )
    
    return States.MEALS_PER_DAY


async def receive_meals_per_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive meals per day selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract meals from callback data
    meals = int(query.data.split('_')[1])  # meals_4
    context.user_data['plan_data']['meals_per_day'] = meals
    
    # Send days keyboard
    keyboard = keyboards.get_days_keyboard()
    await query.edit_message_text(
        "¿Para cuántos días quieres el plan nutricional?",
        reply_markup=keyboard
    )
    
    return States.DAYS_REQUESTED


async def receive_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive days selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract days from callback data
    days = int(query.data.split('_')[1])  # days_7
    context.user_data['plan_data']['days_requested'] = days
    
    # Send economic level keyboard
    keyboard = keyboards.get_economic_level_keyboard()
    await query.edit_message_text(
        "¿Qué nivel económico prefieres para las recetas?",
        reply_markup=keyboard
    )
    
    return States.CONFIRM


async def receive_economic_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive economic level and show confirmation."""
    query = update.callback_query
    await query.answer()
    
    # Extract economic level
    economic_level = query.data.split('_')[1]  # economic_standard
    context.user_data['plan_data']['economic_level'] = economic_level
    
    # Show summary for confirmation
    summary = formatters.format_patient_summary(context.user_data['plan_data'])
    keyboard = keyboards.get_confirmation_keyboard(summary)
    
    await query.edit_message_text(
        summary,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    return States.CONFIRM


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle plan generation confirmation."""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'confirm_no':
        # Cancel
        await query.edit_message_text(
            f"{settings.EMOJI_INFO} Operación cancelada. Puedes comenzar de nuevo cuando quieras."
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # User confirmed, generate plan
    await query.edit_message_text(
        formatters.format_progress_message('generating_plan')
    )
    
    try:
        # Call API to generate plan
        plan_data = await api_client.generate_new_plan(context.user_data['plan_data'])
        
        # Format and send plan
        messages = formatters.format_meal_plan(plan_data)
        
        for message in messages:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                parse_mode='Markdown'
            )
            await asyncio.sleep(0.5)  # Small delay between messages
        
        # Send completion message with back to menu option
        keyboard = keyboards.get_back_to_menu_keyboard()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"{settings.EMOJI_SUCCESS} ¡Tu plan nutricional está listo!\n\n"
                 "Recuerda que este plan está diseñado específicamente para ti. "
                 "Si necesitas hacer algún cambio o tienes dudas, no dudes en consultarme.",
            reply_markup=keyboard
        )
        
    except APIError as e:
        logger.error(f"API error generating plan: {str(e)}")
        error_msg = formatters.format_error_message('generation_error', str(e))
        
        keyboard = keyboards.get_back_to_menu_keyboard()
        await query.edit_message_text(
            error_msg,
            reply_markup=keyboard
        )
    
    except Exception as e:
        logger.error(f"Unexpected error generating plan: {str(e)}")
        error_msg = formatters.format_error_message('unknown')
        
        keyboard = keyboards.get_back_to_menu_keyboard()
        await query.edit_message_text(
            error_msg,
            reply_markup=keyboard
        )
    
    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text(
        f"{settings.EMOJI_INFO} Operación cancelada. Puedes comenzar de nuevo cuando quieras con /start"
    )
    context.user_data.clear()
    return ConversationHandler.END


def get_new_plan_handler() -> ConversationHandler:
    """Get the conversation handler for new plan generation."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_new_plan, pattern='^new_plan$'),
            CommandHandler('nuevo_plan', start_new_plan)
        ],
        states={
            States.NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            States.AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_age)],
            States.GENDER: [CallbackQueryHandler(receive_gender, pattern='^gender_')],
            States.HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_height)],
            States.WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_weight)],
            States.ACTIVITY: [CallbackQueryHandler(receive_activity, pattern='^activity_')],
            States.PATHOLOGIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_pathologies)],
            States.ALLERGIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_allergies)],
            States.PREFERENCES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_preferences)],
            States.DISLIKES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_dislikes)],
            States.MEALS_PER_DAY: [CallbackQueryHandler(receive_meals_per_day, pattern='^meals_')],
            States.DAYS_REQUESTED: [CallbackQueryHandler(receive_days, pattern='^days_')],
            States.CONFIRM: [
                CallbackQueryHandler(receive_economic_level, pattern='^economic_'),
                CallbackQueryHandler(handle_confirmation, pattern='^confirm_')
            ],
        },
        fallbacks=[
            CommandHandler('cancelar', cancel),
            CommandHandler('cancel', cancel)
        ],
        conversation_timeout=settings.CONVERSATION_TIMEOUT
    )


# Import asyncio for sleep
import asyncio