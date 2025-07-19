"""
Secretary Mode Handler - Professional features for nutrition secretaries
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
from telegram_bot.utils.api_client import api_client
from telegram_bot.utils.progress import ProgressTracker

logger = logging.getLogger(__name__)

# Secretary states
class SecretaryStates:
    MENU = 100
    PATIENT_NAME = 101
    PATIENT_PHONE = 102
    PATIENT_EMAIL = 103
    DELIVERY_METHOD = 104
    NOTES = 105
    CONFIRM_PATIENT = 106
    TEMPLATE_SELECT = 107
    QUICK_PARAMS = 108


async def start_secretary_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start secretary mode with professional menu."""
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message
    
    # Check if user is authorized secretary
    user_id = update.effective_user.id
    if not await is_authorized_secretary(user_id):
        await message.reply_text(
            f"{settings.EMOJI_ERROR} Acceso denegado. Solo personal autorizado puede usar el modo secretaria.\n\n"
            "Si sos secretaria, contactá al administrador para obtener acceso."
        )
        return ConversationHandler.END
    
    # Show secretary menu
    keyboard = [
        [
            InlineKeyboardButton("📝 Nuevo Plan Completo", callback_data="sec_new_full"),
            InlineKeyboardButton("⚡ Plan Rápido", callback_data="sec_quick")
        ],
        [
            InlineKeyboardButton("📋 Plantillas Guardadas", callback_data="sec_templates"),
            InlineKeyboardButton("👥 Pacientes Recientes", callback_data="sec_recent")
        ],
        [
            InlineKeyboardButton("📊 Estadísticas del Día", callback_data="sec_stats"),
            InlineKeyboardButton("⚙️ Configuración", callback_data="sec_config")
        ],
        [
            InlineKeyboardButton("◀️ Volver al Menú Principal", callback_data="back_to_menu")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_text(
        f"👩‍💼 **Modo Secretaria Profesional**\n\n"
        f"Bienvenida, {update.effective_user.first_name}!\n\n"
        "Seleccioná una opción:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SecretaryStates.MENU


async def is_authorized_secretary(user_id: int) -> bool:
    """Check if user is authorized secretary."""
    # In production, this would check against a database
    # For now, check environment variable
    authorized_ids = settings.secretary_ids_list
    return str(user_id) in authorized_ids


async def handle_secretary_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle secretary menu selections."""
    query = update.callback_query
    await query.answer()
    
    action = query.data.split('_')[1]
    
    if action == 'new':
        # Start full plan creation with patient info
        await query.edit_message_text(
            "📝 **Nuevo Plan Completo**\n\n"
            "Primero necesito los datos del paciente.\n\n"
            "¿Nombre completo del paciente?"
        )
        context.user_data['secretary_mode'] = True
        context.user_data['patient_info'] = {}
        return SecretaryStates.PATIENT_NAME
        
    elif action == 'quick':
        # Quick plan with templates
        keyboard = [
            [InlineKeyboardButton("🏃‍♀️ Deportista Mujer", callback_data="template_sport_f")],
            [InlineKeyboardButton("🏃‍♂️ Deportista Hombre", callback_data="template_sport_m")],
            [InlineKeyboardButton("📉 Descenso Moderado", callback_data="template_loss")],
            [InlineKeyboardButton("🍎 Diabético/a", callback_data="template_diabetic")],
            [InlineKeyboardButton("👶 Adolescente", callback_data="template_teen")],
            [InlineKeyboardButton("◀️ Volver", callback_data="sec_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚡ **Plan Rápido con Plantillas**\n\n"
            "Seleccioná el perfil que más se ajuste:",
            reply_markup=reply_markup
        )
        return SecretaryStates.TEMPLATE_SELECT
        
    elif action == 'templates':
        # Show saved templates
        await show_saved_templates(query, context)
        return SecretaryStates.MENU
        
    elif action == 'recent':
        # Show recent patients
        await show_recent_patients(query, context)
        return SecretaryStates.MENU
        
    elif action == 'stats':
        # Show daily statistics
        await show_daily_stats(query, context)
        return SecretaryStates.MENU
        
    elif action == 'config':
        # Secretary configuration
        await show_secretary_config(query, context)
        return SecretaryStates.MENU


async def receive_patient_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive patient name for secretary mode."""
    name = update.message.text
    
    # Validate
    is_valid, error_msg = validators.validate_name(name)
    if not is_valid:
        await update.message.reply_text(
            f"{settings.EMOJI_ERROR} {error_msg}\n\n"
            "Por favor, ingresá el nombre completo del paciente:"
        )
        return SecretaryStates.PATIENT_NAME
    
    context.user_data['patient_info']['name'] = name
    
    await update.message.reply_text(
        f"✅ Paciente: {name}\n\n"
        "¿Número de teléfono del paciente? (para envío por WhatsApp)"
    )
    
    return SecretaryStates.PATIENT_PHONE


async def receive_patient_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive patient phone number."""
    phone = update.message.text
    
    # Validate
    is_valid, error_msg = validators.validate_phone(phone)
    if not is_valid:
        await update.message.reply_text(
            f"{settings.EMOJI_ERROR} {error_msg}\n\n"
            "Formato esperado: +5491112345678"
        )
        return SecretaryStates.PATIENT_PHONE
    
    context.user_data['patient_info']['phone'] = phone
    
    await update.message.reply_text(
        "¿Email del paciente? (opcional, escribí 'no' si no tenés)"
    )
    
    return SecretaryStates.PATIENT_EMAIL


async def receive_patient_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive patient email."""
    email = update.message.text
    
    if email.lower() != 'no':
        # Validate email
        is_valid, error_msg = validators.validate_email(email)
        if not is_valid:
            await update.message.reply_text(
                f"{settings.EMOJI_ERROR} {error_msg}"
            )
            return SecretaryStates.PATIENT_EMAIL
        context.user_data['patient_info']['email'] = email
    else:
        context.user_data['patient_info']['email'] = None
    
    # Show delivery options
    keyboard = [
        [
            InlineKeyboardButton("📱 WhatsApp", callback_data="delivery_whatsapp"),
            InlineKeyboardButton("📧 Email", callback_data="delivery_email")
        ],
        [
            InlineKeyboardButton("💬 Telegram", callback_data="delivery_telegram"),
            InlineKeyboardButton("🖨️ Imprimir", callback_data="delivery_print")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "¿Cómo querés entregar el plan al paciente?",
        reply_markup=reply_markup
    )
    
    return SecretaryStates.DELIVERY_METHOD


async def handle_delivery_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle delivery method selection."""
    query = update.callback_query
    await query.answer()
    
    method = query.data.split('_')[1]
    context.user_data['patient_info']['delivery_method'] = method
    
    # Check if method is available
    if method == 'email' and not context.user_data['patient_info'].get('email'):
        await query.edit_message_text(
            f"{settings.EMOJI_ERROR} No se ingresó email del paciente.\n\n"
            "Por favor, seleccioná otro método de entrega."
        )
        return SecretaryStates.DELIVERY_METHOD
    
    # Show patient summary
    patient_info = context.user_data['patient_info']
    summary = f"""
📋 **Resumen del Paciente**

👤 **Nombre:** {patient_info['name']}
📱 **Teléfono:** {patient_info['phone']}
📧 **Email:** {patient_info.get('email', 'No especificado')}
📤 **Entrega:** {method.capitalize()}

¿Alguna nota adicional sobre el paciente? (alergias conocidas, preferencias, etc.)
Si no hay notas, escribí 'no'.
"""
    
    await query.edit_message_text(summary, parse_mode='Markdown')
    
    return SecretaryStates.NOTES


async def receive_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive additional notes about patient."""
    notes = update.message.text
    
    if notes.lower() != 'no':
        context.user_data['patient_info']['notes'] = notes
    
    # Start plan creation
    # Merge patient info with plan data
    context.user_data['plan_data'] = context.user_data.get('plan_data', {})
    context.user_data['plan_data']['secretary_patient'] = context.user_data['patient_info']
    
    # Continue to regular plan flow
    await update.message.reply_text(
        f"✅ Información del paciente guardada.\n\n"
        f"Ahora vamos a crear el plan nutricional.\n\n"
        f"Primero, ¿cuántos años tiene {context.user_data['patient_info']['name']}?"
    )
    
    # Continue with regular plan flow
    from telegram_bot.handlers.new_plan_handler import receive_age
    return States.AGE


async def show_saved_templates(query: Any, context: ContextTypes.DEFAULT_TYPE):
    """Show saved plan templates."""
    # In production, load from database
    templates = [
        {"name": "Deportista Standard", "id": "sport_std", "uses": 45},
        {"name": "Descenso 0.5kg/sem", "id": "loss_05", "uses": 32},
        {"name": "Diabético Tipo 2", "id": "diab_t2", "uses": 28},
        {"name": "Vegetariano Completo", "id": "veg_full", "uses": 15},
    ]
    
    keyboard = []
    for template in templates:
        keyboard.append([
            InlineKeyboardButton(
                f"{template['name']} ({template['uses']} usos)",
                callback_data=f"use_template_{template['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Volver", callback_data="secretary_menu")])
    
    await query.edit_message_text(
        "📋 **Plantillas Guardadas**\n\n"
        "Seleccioná una plantilla para usar:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_recent_patients(query: Any, context: ContextTypes.DEFAULT_TYPE):
    """Show recent patients."""
    # In production, load from database
    recent = [
        "María García - Plan generado hace 2 horas",
        "Juan Pérez - Plan generado ayer",
        "Ana López - Plan generado hace 3 días",
        "Carlos Rodríguez - Plan generado hace 5 días"
    ]
    
    text = "👥 **Pacientes Recientes**\n\n"
    for patient in recent:
        text += f"• {patient}\n"
    
    text += "\n_Los planes anteriores pueden duplicarse y modificarse._"
    
    keyboard = [[InlineKeyboardButton("◀️ Volver", callback_data="secretary_menu")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def show_daily_stats(query: Any, context: ContextTypes.DEFAULT_TYPE):
    """Show daily statistics."""
    # In production, calculate from database
    stats = {
        "plans_today": 8,
        "plans_week": 42,
        "avg_time": "12 minutos",
        "most_used_template": "Deportista Standard"
    }
    
    text = f"""
📊 **Estadísticas del Día**

📅 **Hoy:** {stats['plans_today']} planes generados
📆 **Esta semana:** {stats['plans_week']} planes
⏱️ **Tiempo promedio:** {stats['avg_time']}
🏆 **Plantilla más usada:** {stats['most_used_template']}

💡 _Tip: Usando plantillas podés reducir el tiempo a 5 minutos_
"""
    
    keyboard = [[InlineKeyboardButton("◀️ Volver", callback_data="secretary_menu")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def show_secretary_config(query: Any, context: ContextTypes.DEFAULT_TYPE):
    """Show secretary configuration options."""
    keyboard = [
        [InlineKeyboardButton("🏥 Datos del Consultorio", callback_data="config_clinic")],
        [InlineKeyboardButton("📝 Crear Nueva Plantilla", callback_data="config_template")],
        [InlineKeyboardButton("🔔 Notificaciones", callback_data="config_notif")],
        [InlineKeyboardButton("◀️ Volver", callback_data="secretary_menu")]
    ]
    
    await query.edit_message_text(
        "⚙️ **Configuración de Secretaria**\n\n"
        "Seleccioná qué querés configurar:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_template_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle template selection for quick plan."""
    query = update.callback_query
    await query.answer()
    
    template_id = query.data.split('_', 1)[1]
    
    # Load template data (in production from DB)
    templates = {
        "sport_f": {
            "name": "Deportista Mujer",
            "age": 28,
            "gender": "female",
            "objective": "mantenimiento",
            "activity_type": "gimnasio",
            "activity_frequency": 5,
            "meals_per_day": 5
        },
        "sport_m": {
            "name": "Deportista Hombre", 
            "age": 30,
            "gender": "male",
            "objective": "subir_05",
            "activity_type": "gimnasio",
            "activity_frequency": 5,
            "meals_per_day": 6
        },
        "loss": {
            "name": "Descenso Moderado",
            "age": 35,
            "gender": "female",
            "objective": "bajar_05",
            "activity_type": "caminata",
            "activity_frequency": 3,
            "meals_per_day": 4
        },
        "diabetic": {
            "name": "Plan Diabético",
            "age": 50,
            "gender": "male",
            "objective": "mantenimiento",
            "pathologies": ["Diabetes tipo 2"],
            "meals_per_day": 6
        }
    }
    
    if template_id in templates:
        template = templates[template_id]
        await query.edit_message_text(
            f"📋 Plantilla seleccionada: **{template['name']}**\n\n"
            "Necesito algunos datos específicos del paciente:\n\n"
            "¿Peso actual? (en kg)"
        )
        
        # Store template data
        context.user_data['template_data'] = template
        context.user_data['quick_params'] = {}
        
        return SecretaryStates.QUICK_PARAMS
    
    return SecretaryStates.MENU


async def handle_quick_params(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quick parameter collection."""
    params = context.user_data.get('quick_params', {})
    
    if 'weight' not in params:
        # Validate weight
        weight_text = update.message.text
        is_valid, error_msg = validators.validate_weight(weight_text)
        if not is_valid:
            await update.message.reply_text(f"{settings.EMOJI_ERROR} {error_msg}")
            return SecretaryStates.QUICK_PARAMS
        
        params['weight'] = float(weight_text.replace(',', '.'))
        context.user_data['quick_params'] = params
        
        await update.message.reply_text("¿Altura? (en cm)")
        return SecretaryStates.QUICK_PARAMS
        
    elif 'height' not in params:
        # Validate height
        height_text = update.message.text
        is_valid, error_msg = validators.validate_height(height_text)
        if not is_valid:
            await update.message.reply_text(f"{settings.EMOJI_ERROR} {error_msg}")
            return SecretaryStates.QUICK_PARAMS
        
        params['height'] = float(height_text.replace(',', '.'))
        context.user_data['quick_params'] = params
        
        # Now generate plan with template + params
        await generate_quick_plan(update, context)
        return ConversationHandler.END


async def generate_quick_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate plan using template and quick params."""
    template = context.user_data['template_data']
    params = context.user_data['quick_params']
    patient_info = context.user_data.get('patient_info', {})
    
    # Merge all data
    plan_data = {
        **template,
        **params,
        'name': patient_info.get('name', template['name']),
        'days_requested': 3,
        'economic_level': 'medio',
        'food_weight_type': 'crudo',
        'include_snacks': True,
        'snack_type': 'saciedad'
    }
    
    # Add defaults for missing fields
    defaults = {
        'activity_duration': 60,
        'supplementation': [],
        'pathologies': [],
        'medications': [],
        'allergies': [],
        'food_preferences': [],
        'food_dislikes': [],
        'meal_schedule': 'Desayuno 8am, Almuerzo 13pm, Cena 20pm'
    }
    
    for key, value in defaults.items():
        if key not in plan_data:
            plan_data[key] = value
    
    # Show progress
    progress = ProgressTracker(update, context)
    await progress.start("Generando Plan Rápido con Plantilla")
    
    try:
        # Generate plan
        await progress.update_progress(2, "Aplicando plantilla seleccionada...")
        result = await api_client.generate_new_plan(plan_data)
        
        await progress.update_progress(5, "Preparando documento...")
        await progress.complete(success=True)
        
        # Send result
        await update.effective_message.reply_text(
            f"✅ **Plan Rápido Generado!**\n\n"
            f"Paciente: {plan_data['name']}\n"
            f"Plantilla: {template['name']}\n"
            f"Calorías diarias: {result.get('daily_calories', 'N/A')} kcal\n\n"
            f"El PDF se está preparando para {patient_info.get('delivery_method', 'descarga')}..."
        )
        
        # Handle delivery based on method
        if patient_info.get('delivery_method') == 'whatsapp':
            await update.effective_message.reply_text(
                f"📱 Para enviar por WhatsApp:\n"
                f"1. Descargá el PDF\n"
                f"2. Envialo a: {patient_info['phone']}\n"
                f"3. Mensaje sugerido: 'Hola {patient_info['name']}! Te envío tu plan nutricional personalizado 🍎'"
            )
        
    except Exception as e:
        await progress.complete(success=False)
        logger.error(f"Error generating quick plan: {e}")
        await update.effective_message.reply_text(
            f"{settings.EMOJI_ERROR} Error al generar el plan. Por favor, intentá nuevamente."
        )


def get_secretary_handler() -> ConversationHandler:
    """Get the conversation handler for secretary mode."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_secretary_mode, pattern='^secretary_mode$'),
            CommandHandler('secretaria', start_secretary_mode)
        ],
        states={
            SecretaryStates.MENU: [
                CallbackQueryHandler(handle_secretary_menu, pattern='^sec_'),
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern='^back_to_menu$')
            ],
            SecretaryStates.PATIENT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_patient_name)
            ],
            SecretaryStates.PATIENT_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_patient_phone)
            ],
            SecretaryStates.PATIENT_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_patient_email)
            ],
            SecretaryStates.DELIVERY_METHOD: [
                CallbackQueryHandler(handle_delivery_method, pattern='^delivery_')
            ],
            SecretaryStates.NOTES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_notes)
            ],
            SecretaryStates.TEMPLATE_SELECT: [
                CallbackQueryHandler(handle_template_selection, pattern='^template_'),
                CallbackQueryHandler(
                    lambda u, c: SecretaryStates.MENU, 
                    pattern='^sec_menu$'
                )
            ],
            SecretaryStates.QUICK_PARAMS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quick_params)
            ],
            # Inherit states from new plan handler for full flow
            States.AGE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, 
                    lambda u, c: __import__('telegram_bot.handlers.new_plan_handler', 
                                          fromlist=['receive_age']).receive_age(u, c)
                )
            ],
        },
        fallbacks=[
            CommandHandler('cancelar', lambda u, c: ConversationHandler.END),
            CommandHandler('cancel', lambda u, c: ConversationHandler.END)
        ],
        conversation_timeout=settings.CONVERSATION_TIMEOUT
    )