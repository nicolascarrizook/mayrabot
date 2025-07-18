"""
Help Handler
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.config import settings
from telegram_bot.utils import keyboards

logger = logging.getLogger(__name__)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message when /help command is issued."""
    help_text = f"""
{settings.EMOJI_INFO} **Ayuda - Bot Nutricional**

**Comandos disponibles:**
• `/start` - Iniciar el bot y ver el menú principal
• `/nuevo_plan` - Crear un nuevo plan nutricional
• `/reemplazar` - Buscar alternativas para una comida
• `/ayuda` o `/help` - Mostrar esta ayuda
• `/cancelar` - Cancelar la operación actual

**¿Cómo funciona?**

{settings.EMOJI_PLAN} **Nuevo Plan Nutricional**
Te haré algunas preguntas sobre tu información personal, condiciones de salud y preferencias. Con estos datos, generaré un plan nutricional personalizado adaptado a tus necesidades.

{settings.EMOJI_FOOD} **Reemplazar Comida**
Si necesitas cambiar alguna comida de tu plan, puedo sugerirte alternativas equivalentes que mantengan el balance nutricional.

**Consejos:**
• Responde con la mayor precisión posible
• Si tienes condiciones médicas, asegúrate de mencionarlas
• Puedes cancelar en cualquier momento con `/cancelar`

**Importante:**
Este bot es una herramienta de apoyo. Para condiciones médicas específicas, siempre consulta con un profesional de la salud.

¿Necesitas algo más?
"""
    
    keyboard = keyboards.get_back_to_menu_keyboard()
    
    # Handle both command and callback query
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send information about the bot."""
    about_text = f"""
{settings.EMOJI_INFO} **Acerca del Bot Nutricional**

Este bot ha sido diseñado para ayudarte a mantener una alimentación saludable y equilibrada mediante planes nutricionales personalizados.

**Características:**
• Planes adaptados a tus necesidades específicas
• Consideración de patologías y alergias
• Alternativas para cada comida
• Recetas detalladas con valores nutricionales

**Metodología:**
Utilizamos inteligencia artificial avanzada combinada con una base de datos de recetas cuidadosamente seleccionadas por profesionales de la nutrición.

**Privacidad:**
No almacenamos tu información personal. Cada plan se genera de forma única y segura.

Versión: 1.0.0
"""
    
    keyboard = keyboards.get_back_to_menu_keyboard()
    
    await update.message.reply_text(
        about_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )