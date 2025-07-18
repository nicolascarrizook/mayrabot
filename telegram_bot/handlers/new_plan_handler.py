"""
New Plan Generation Handler (Motor 1) - Tres Días y Carga Version
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
            "Método Tres Días y Carga | Dieta Inteligente® & Nutrición Evolutiva\n\n"
            "Necesitaré algunos datos sobre vos. Podés cancelar en cualquier momento con /cancelar\n\n"
            "Primero, ¿cuál es tu nombre completo?"
        )
    else:
        await update.message.reply_text(
            f"{settings.EMOJI_PLAN} ¡Excelente! Vamos a crear tu plan nutricional personalizado.\n\n"
            "Método Tres Días y Carga | Dieta Inteligente® & Nutrición Evolutiva\n\n"
            "Necesitaré algunos datos sobre vos. Podés cancelar en cualquier momento con /cancelar\n\n"
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
            "Por favor, ingresá tu nombre completo:"
        )
        return States.NAME
    
    # Store and continue
    context.user_data['plan_data']['name'] = validators.sanitize_input(name)
    
    await update.message.reply_text(
        f"Perfecto, {name}. Ahora decime, ¿cuántos años tenés?"
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
            "Por favor, ingresá tu edad en años:"
        )
        return States.AGE
    
    # Store and continue
    context.user_data['plan_data']['age'] = int(age_text.strip())
    
    # Send gender selection keyboard
    keyboard = keyboards.get_gender_keyboard()
    await update.message.reply_text(
        "¿Cuál es tu sexo?",
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
        f"Entendido. Ahora necesito tu estatura en centímetros (ej: 170):"
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
            "Por favor, ingresá tu estatura en centímetros:"
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
            "Por favor, ingresá tu peso en kilogramos:"
        )
        return States.WEIGHT
    
    # Store and continue
    weight_text = weight_text.replace(',', '.').strip()
    context.user_data['plan_data']['weight'] = float(weight_text)
    
    # Send objective keyboard
    keyboard = keyboards.get_objective_keyboard()
    await update.message.reply_text(
        "¿Cuál es tu objetivo?",
        reply_markup=keyboard
    )
    
    return States.OBJECTIVE


async def receive_objective(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive objective selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract objective from callback data
    objective = query.data.split('_', 1)[1]  # obj_mantenimiento
    context.user_data['plan_data']['objective'] = objective
    
    # Send activity type keyboard
    keyboard = keyboards.get_activity_type_keyboard()
    await query.edit_message_text(
        "¿Qué tipo de actividad física realizás?",
        reply_markup=keyboard
    )
    
    return States.ACTIVITY_TYPE


async def receive_activity_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive activity type selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract activity type from callback data
    activity_type = query.data.split('_', 1)[1]  # type_pesas
    context.user_data['plan_data']['activity_type'] = activity_type
    
    if activity_type == 'sedentario':
        # Skip frequency and duration for sedentary
        context.user_data['plan_data']['activity_frequency'] = 1
        context.user_data['plan_data']['activity_duration'] = 30
        
        await query.edit_message_text(
            "¿Estás tomando algún suplemento actualmente?\n\n"
            "(Ej: creatina, proteína, omega 3. Si no tomás ninguno, escribí 'no')"
        )
        
        return States.SUPPLEMENTATION
    else:
        # Send frequency keyboard
        keyboard = keyboards.get_activity_frequency_keyboard()
        await query.edit_message_text(
            "¿Cuántas veces por semana entrenás?",
            reply_markup=keyboard
        )
        
        return States.ACTIVITY_FREQUENCY


async def receive_activity_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive activity frequency selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract frequency from callback data
    frequency = int(query.data.split('_')[1])  # freq_4
    context.user_data['plan_data']['activity_frequency'] = frequency
    
    # Send duration keyboard
    keyboard = keyboards.get_activity_duration_keyboard()
    await query.edit_message_text(
        "¿Cuánto dura cada sesión de entrenamiento?",
        reply_markup=keyboard
    )
    
    return States.ACTIVITY_DURATION


async def receive_activity_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive activity duration selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract duration from callback data
    duration = int(query.data.split('_')[1])  # dur_60
    context.user_data['plan_data']['activity_duration'] = duration
    
    await query.edit_message_text(
        "¿Estás tomando algún suplemento actualmente?\n\n"
        "(Ej: creatina, proteína, omega 3. Si no tomás ninguno, escribí 'no')"
    )
    
    return States.SUPPLEMENTATION


async def receive_supplementation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive supplementation information."""
    supplements = update.message.text
    
    # Validate
    is_valid, error_msg = validators.validate_text_list(supplements, "suplementos")
    if not is_valid:
        await update.message.reply_text(
            f"{settings.EMOJI_ERROR} {error_msg}\n\n"
            "Por favor, describí tus suplementos o escribí 'no':"
        )
        return States.SUPPLEMENTATION
    
    # Store and continue
    context.user_data['plan_data']['supplementation'] = validators.format_list_input(supplements)
    
    await update.message.reply_text(
        "¿Tenés alguna patología o condición médica que deba considerar?\n\n"
        "(Ej: diabetes, hipertensión, resistencia a la insulina, hígado graso, colon irritable. Si no tenés ninguna, escribí 'no')"
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
            "Por favor, describí tus patologías o escribí 'no':"
        )
        return States.PATHOLOGIES
    
    # Store and continue
    context.user_data['plan_data']['pathologies'] = validators.format_list_input(pathologies)
    
    await update.message.reply_text(
        "¿Tomás alguna medicación?\n\n"
        "(Si no tomás ninguna, escribí 'no')"
    )
    
    return States.MEDICATIONS


async def receive_medications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive medications information."""
    medications = update.message.text
    
    # Validate
    is_valid, error_msg = validators.validate_text_list(medications, "medicaciones")
    if not is_valid:
        await update.message.reply_text(
            f"{settings.EMOJI_ERROR} {error_msg}\n\n"
            "Por favor, describí tus medicaciones o escribí 'no':"
        )
        return States.MEDICATIONS
    
    # Store and continue
    context.user_data['plan_data']['medications'] = validators.format_list_input(medications)
    
    await update.message.reply_text(
        "¿Tenés alguna alergia alimentaria?\n\n"
        "(Ej: gluten, lactosa, frutos secos. Si no tenés, escribí 'no')"
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
            "Por favor, describí tus alergias o escribí 'no':"
        )
        return States.ALLERGIES
    
    # Store and continue
    context.user_data['plan_data']['allergies'] = validators.format_list_input(allergies)
    
    await update.message.reply_text(
        "¿Qué alimentos te gustan o preferís incluir?\n\n"
        "(Ej: pollo, pescado, avena. Si no tenés preferencias, escribí 'no')"
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
            "Por favor, describí tus preferencias o escribí 'no':"
        )
        return States.PREFERENCES
    
    # Store and continue
    context.user_data['plan_data']['food_preferences'] = validators.format_list_input(preferences)
    
    await update.message.reply_text(
        "¿Hay algún alimento que NO consumís o preferís evitar?\n\n"
        "(Ej: brócoli, hígado, pescado. Si no hay ninguno, escribí 'no')"
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
            "Por favor, describí qué no te gusta o escribí 'no':"
        )
        return States.DISLIKES
    
    # Store and continue
    context.user_data['plan_data']['food_dislikes'] = validators.format_list_input(dislikes)
    
    await update.message.reply_text(
        "¿Cuáles son tus horarios habituales de comida y entrenamiento?\n\n"
        "(Ej: Desayuno 8am, entreno 18hs, ceno 21hs. Esto me ayuda a organizar mejor tu plan)"
    )
    
    return States.MEAL_SCHEDULE


async def receive_meal_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive meal schedule information."""
    schedule = update.message.text
    
    # Store schedule
    context.user_data['plan_data']['meal_schedule'] = schedule
    
    # Send meals per day keyboard
    keyboard = keyboards.get_meals_per_day_keyboard()
    await update.message.reply_text(
        "¿Cuántas comidas principales querés hacer al día?",
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
    
    # Send snacks keyboard
    keyboard = keyboards.get_snacks_keyboard()
    await query.edit_message_text(
        "¿Querés incluir colaciones?",
        reply_markup=keyboard
    )
    
    return States.INCLUDE_SNACKS


async def receive_snacks_preference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive snacks preference."""
    query = update.callback_query
    await query.answer()
    
    # Extract snack preference from callback data
    snack_data = query.data.split('_', 1)[1]  # snack_no, snack_saciedad, etc.
    
    if snack_data == 'no':
        context.user_data['plan_data']['include_snacks'] = False
        context.user_data['plan_data']['snack_type'] = None
    else:
        context.user_data['plan_data']['include_snacks'] = True
        context.user_data['plan_data']['snack_type'] = snack_data
    
    # Send economic level keyboard
    keyboard = keyboards.get_economic_level_keyboard()
    await query.edit_message_text(
        "¿Qué nivel económico preferís para las recetas?",
        reply_markup=keyboard
    )
    
    return States.ECONOMIC_LEVEL


async def receive_economic_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive economic level selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract economic level
    economic_level = query.data.split('_', 1)[1]  # economic_medio
    context.user_data['plan_data']['economic_level'] = economic_level
    
    # Send food weight type keyboard
    keyboard = keyboards.get_food_weight_type_keyboard()
    await query.edit_message_text(
        "¿Cómo preferís que se expresen los pesos de los alimentos?",
        reply_markup=keyboard
    )
    
    return States.FOOD_WEIGHT_TYPE


async def receive_food_weight_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive food weight type selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract weight type
    weight_type = query.data.split('_')[1]  # weight_crudo
    context.user_data['plan_data']['food_weight_type'] = weight_type
    
    await query.edit_message_text(
        "¿Alguna nota personal o información adicional que quieras agregar?\n\n"
        "(Si no tenés nada que agregar, escribí 'no')"
    )
    
    return States.PERSONAL_NOTES


async def receive_personal_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive personal notes."""
    notes = update.message.text
    
    # Store notes
    if notes.lower() != 'no':
        context.user_data['plan_data']['personal_notes'] = notes
    else:
        context.user_data['plan_data']['personal_notes'] = None
    
    # Always 3 days for Tres Días y Carga
    context.user_data['plan_data']['days_requested'] = 3
    
    # Show summary for confirmation
    summary = formatters.format_patient_summary(context.user_data['plan_data'])
    keyboard = keyboards.get_confirmation_keyboard(summary)
    
    await update.message.reply_text(
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
            f"{settings.EMOJI_INFO} Operación cancelada. Podés comenzar de nuevo cuando quieras."
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # User confirmed, generate plan
    await query.edit_message_text(
        formatters.format_progress_message('generating_plan')
    )
    
    try:
        # Convert gender back to API format
        if context.user_data['plan_data']['gender'] == 'M':
            context.user_data['plan_data']['gender'] = 'male'
        else:
            context.user_data['plan_data']['gender'] = 'female'
        
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
                 "Plan de 3 días iguales - Método Tres Días y Carga\n\n"
                 "Recordá que este plan está diseñado específicamente para vos. "
                 "Si necesitás hacer algún cambio o tenés dudas, no dudes en consultarme.",
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
        f"{settings.EMOJI_INFO} Operación cancelada. Podés comenzar de nuevo cuando quieras con /start"
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
            States.OBJECTIVE: [CallbackQueryHandler(receive_objective, pattern='^obj_')],
            States.ACTIVITY_TYPE: [CallbackQueryHandler(receive_activity_type, pattern='^type_')],
            States.ACTIVITY_FREQUENCY: [CallbackQueryHandler(receive_activity_frequency, pattern='^freq_')],
            States.ACTIVITY_DURATION: [CallbackQueryHandler(receive_activity_duration, pattern='^dur_')],
            States.SUPPLEMENTATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_supplementation)],
            States.PATHOLOGIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_pathologies)],
            States.MEDICATIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_medications)],
            States.ALLERGIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_allergies)],
            States.PREFERENCES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_preferences)],
            States.DISLIKES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_dislikes)],
            States.MEAL_SCHEDULE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_meal_schedule)],
            States.MEALS_PER_DAY: [CallbackQueryHandler(receive_meals_per_day, pattern='^meals_')],
            States.INCLUDE_SNACKS: [CallbackQueryHandler(receive_snacks_preference, pattern='^snack_')],
            States.ECONOMIC_LEVEL: [CallbackQueryHandler(receive_economic_level, pattern='^economic_')],
            States.FOOD_WEIGHT_TYPE: [CallbackQueryHandler(receive_food_weight_type, pattern='^weight_')],
            States.PERSONAL_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_personal_notes)],
            States.CONFIRM: [
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