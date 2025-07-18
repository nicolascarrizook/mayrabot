"""
Message formatters for Telegram Bot
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from telegram_bot.config import settings


def format_patient_summary(patient_data: Dict[str, Any]) -> str:
    """Format patient data summary for confirmation."""
    summary = f"""
{settings.EMOJI_INFO} **Resumen de Información del Paciente**

👤 **Nombre:** {patient_data['name']}
🎂 **Edad:** {patient_data['age']} años
⚧️ **Género:** {'Masculino' if patient_data['gender'] == 'M' else 'Femenino'}
📏 **Altura:** {patient_data['height']} cm
⚖️ **Peso:** {patient_data['weight']} kg
💪 **Actividad Física:** {patient_data['physical_activity'].replace('_', ' ').title()}

🏥 **Patologías:** {patient_data.get('pathologies', 'Ninguna')}
🚫 **Alergias:** {patient_data.get('allergies', 'Ninguna')}
👍 **Preferencias:** {patient_data.get('preferences', 'Ninguna')}
👎 **No le gusta:** {patient_data.get('dislikes', 'Ninguna')}

🍽️ **Comidas al día:** {patient_data['meals_per_day']}
📅 **Días solicitados:** {patient_data['days_requested']}

¿Es correcta esta información?
"""
    return summary


def format_meal_plan(plan_data: Dict[str, Any]) -> List[str]:
    """Format meal plan response into Telegram messages."""
    messages = []
    
    # Header message
    header = f"""
{settings.EMOJI_SUCCESS} **Plan Nutricional Generado**

📊 **Información General:**
- Paciente: {plan_data.get('patient_name', 'N/A')}
- Calorías diarias: {plan_data.get('total_calories', plan_data.get('daily_calories', 'N/A'))} kcal
- IMC: {plan_data.get('bmi', 'N/A')} ({plan_data.get('bmi_category', 'N/A')})
- Plan de {plan_data.get('total_days', 'N/A')} días
"""
    messages.append(header)
    
    # Note: The response doesn't include detailed meal plans in the summary
    # The PDF would contain the full details
    summary_message = f"""
📋 **Resumen del Plan:**
- Comidas por día: {plan_data['plan_summary']['meals_per_day']}
- Nivel económico: {plan_data['plan_summary']['economic_level']}
- Patologías consideradas: {', '.join(plan_data['plan_summary']['pathologies']) if plan_data['plan_summary']['pathologies'] else 'Ninguna'}
- Alergias consideradas: {', '.join(plan_data['plan_summary']['allergies']) if plan_data['plan_summary']['allergies'] else 'Ninguna'}

📄 Tu plan nutricional completo está siendo generado en formato PDF.
{plan_data.get('message', '')}
"""
    messages.append(summary_message)
    
    # Add recommendations if present
    if 'recommendations' in plan_data:
        rec_message = f"\n{settings.EMOJI_INFO} **Recomendaciones:**\n{plan_data['recommendations']}"
        messages.append(rec_message)
    
    return messages


def format_meal_alternatives(alternatives: List[Dict[str, Any]], meal_type: str) -> str:
    """Format meal alternatives for display."""
    meal_emoji = get_meal_emoji(meal_type)
    
    message = f"{meal_emoji} **Alternativas para {meal_type.title()}**\n\n"
    
    for i, alt in enumerate(alternatives[:5], 1):
        message += f"**{i}. {alt['name']}**\n"
        message += f"   🔥 {alt['calories']} kcal\n"
        
        if 'ingredients' in alt:
            ingredients_preview = ', '.join(alt['ingredients'][:3])
            if len(alt['ingredients']) > 3:
                ingredients_preview += '...'
            message += f"   🥗 {ingredients_preview}\n"
        
        message += "\n"
    
    return message


def format_recipe_detail(recipe: Dict[str, Any]) -> str:
    """Format detailed recipe information."""
    message = f"🍽️ **{recipe['name']}**\n\n"
    
    # Nutritional info
    message += "**Información Nutricional:**\n"
    message += f"• Calorías: {recipe.get('calories', 'N/A')} kcal\n"
    message += f"• Proteínas: {recipe.get('protein', 'N/A')}g\n"
    message += f"• Carbohidratos: {recipe.get('carbs', 'N/A')}g\n"
    message += f"• Grasas: {recipe.get('fats', 'N/A')}g\n\n"
    
    # Ingredients
    if 'ingredients' in recipe:
        message += "**Ingredientes:**\n"
        for ing in recipe['ingredients']:
            message += f"• {ing['name']}: {ing['quantity']}\n"
        message += "\n"
    
    # Preparation
    if 'preparation' in recipe:
        message += "**Preparación:**\n"
        message += recipe['preparation'] + "\n"
    
    return message


def format_error_message(error_type: str, details: Optional[str] = None) -> str:
    """Format error messages for users."""
    base_messages = {
        'api_error': f"{settings.EMOJI_ERROR} Error al conectar con el servidor. Por favor, intenta más tarde.",
        'generation_error': f"{settings.EMOJI_ERROR} Error al generar el plan. Por favor, intenta nuevamente.",
        'validation_error': f"{settings.EMOJI_ERROR} Los datos ingresados no son válidos.",
        'timeout': f"{settings.EMOJI_ERROR} La operación tardó demasiado. Por favor, intenta más tarde.",
        'unknown': f"{settings.EMOJI_ERROR} Ocurrió un error inesperado."
    }
    
    message = base_messages.get(error_type, base_messages['unknown'])
    
    if details:
        message += f"\n\nDetalles: {details}"
    
    return message


def format_progress_message(step: str) -> str:
    """Format progress messages during long operations."""
    messages = {
        'collecting_data': f"{settings.EMOJI_LOADING} Recopilando información...",
        'generating_plan': f"{settings.EMOJI_LOADING} Generando tu plan nutricional personalizado...",
        'searching_alternatives': f"{settings.EMOJI_LOADING} Buscando alternativas...",
        'processing': f"{settings.EMOJI_LOADING} Procesando...",
        'almost_done': f"{settings.EMOJI_LOADING} Casi listo..."
    }
    
    return messages.get(step, messages['processing'])


def get_meal_emoji(meal_type: str) -> str:
    """Get emoji for meal type."""
    meal_emojis = {
        'desayuno': settings.EMOJI_BREAKFAST,
        'media_mañana': settings.EMOJI_SNACK,
        'media_manana': settings.EMOJI_SNACK,
        'almuerzo': settings.EMOJI_LUNCH,
        'merienda': settings.EMOJI_SNACK,
        'cena': settings.EMOJI_DINNER,
        'colación': settings.EMOJI_SNACK,
        'colacion': settings.EMOJI_SNACK
    }
    
    return meal_emojis.get(meal_type.lower(), settings.EMOJI_FOOD)


def truncate_message(message: str, max_length: int = 4000) -> List[str]:
    """Split long messages for Telegram's limit."""
    if len(message) <= max_length:
        return [message]
    
    messages = []
    current_message = ""
    
    # Split by paragraphs
    paragraphs = message.split('\n\n')
    
    for paragraph in paragraphs:
        if len(current_message) + len(paragraph) + 2 > max_length:
            if current_message:
                messages.append(current_message.strip())
                current_message = paragraph
            else:
                # Single paragraph too long, split by lines
                lines = paragraph.split('\n')
                for line in lines:
                    if len(current_message) + len(line) + 1 > max_length:
                        messages.append(current_message.strip())
                        current_message = line
                    else:
                        current_message += '\n' + line if current_message else line
        else:
            current_message += '\n\n' + paragraph if current_message else paragraph
    
    if current_message:
        messages.append(current_message.strip())
    
    return messages


def escape_markdown(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    # List of characters to escape
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text