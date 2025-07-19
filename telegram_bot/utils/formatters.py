"""
Message formatters for Telegram Bot
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from telegram_bot.config import settings

logger = logging.getLogger(__name__)


def format_patient_summary(patient_data: Dict[str, Any]) -> str:
    """Format patient data summary for confirmation."""
    # Map objectives
    objective_map = {
        'mantenimiento': 'Mantenimiento',
        'bajar_05': 'Bajar 0,5 kg/semana',
        'bajar_1': 'Bajar 1 kg/semana',
        'subir_05': 'Subir 0,5 kg/semana',
        'subir_1': 'Subir 1 kg/semana'
    }
    
    # Format activity info
    activity_info = patient_data.get('activity_type', '').replace('_', ' ').title()
    if patient_data.get('activity_frequency', 0) > 0:
        activity_info += f" - {patient_data['activity_frequency']}x por semana, {patient_data['activity_duration']} min"
    
    # Format snacks info
    snacks_info = "No"
    if patient_data.get('include_snacks'):
        snack_types = {
            'saciedad': 'Por saciedad',
            'pre': 'Pre-entreno',
            'post': 'Post-entreno'
        }
        snacks_info = snack_types.get(patient_data.get('snack_type', ''), 'Sí')
    
    # Format lists
    def format_list(items):
        if isinstance(items, list):
            return ', '.join(items) if items else 'Ninguna'
        return items if items and items != 'no' else 'Ninguna'
    
    summary = f"""
{settings.EMOJI_INFO} **Resumen - Método Tres Días y Carga**

👤 **Nombre:** {patient_data['name']}
🎂 **Edad:** {patient_data['age']} años
⚧️ **Sexo:** {'Masculino' if patient_data['gender'] == 'M' else 'Femenino'}
📏 **Estatura:** {patient_data['height']} cm
⚖️ **Peso:** {patient_data['weight']} kg

🎯 **Objetivo:** {objective_map.get(patient_data.get('objective', ''), 'No especificado')}
🏋️ **Actividad:** {activity_info}
💊 **Suplementos:** {format_list(patient_data.get('supplementation', []))}

🏥 **Patologías:** {format_list(patient_data.get('pathologies', []))}
💊 **Medicaciones:** {format_list(patient_data.get('medications', []))}
🚫 **Alergias:** {format_list(patient_data.get('allergies', []))}
👍 **Le gusta:** {format_list(patient_data.get('food_preferences', patient_data.get('preferences', [])))}
👎 **NO consume:** {format_list(patient_data.get('food_dislikes', patient_data.get('dislikes', [])))}

🕒 **Horarios:** {patient_data.get('meal_schedule', 'No especificado')}
🍽️ **Comidas principales:** {patient_data['meals_per_day']}
🍎 **Colaciones:** {snacks_info}
💰 **Nivel económico:** {patient_data.get('economic_level', 'medio').replace('_', ' ').title()}
🍳 **Pesos en:** {patient_data.get('food_weight_type', 'crudo').title()}
📄 **Notas:** {patient_data.get('personal_notes', 'Ninguna')}

📅 **Plan:** 3 días iguales (Tres Días y Carga)

¿Es correcta esta información?
"""
    return summary


def format_meal_plan(plan_data: Dict[str, Any]) -> List[str]:
    """Format meal plan response into Telegram messages."""
    messages = []
    
    # Escape dynamic values for MarkdownV2
    patient_name = escape_markdown(str(plan_data.get('patient_name', 'N/A')))
    total_calories = escape_markdown(str(plan_data.get('total_calories', plan_data.get('daily_calories', 'N/A'))))
    bmi = escape_markdown(str(plan_data.get('bmi', 'N/A')))
    bmi_category = escape_markdown(str(plan_data.get('bmi_category', 'N/A')))
    total_days = escape_markdown(str(plan_data.get('total_days', 'N/A')))
    
    # Header message
    header = f"""
{settings.EMOJI_SUCCESS} *Plan Nutricional Generado*

📊 *Información General:*
\\- Paciente: {patient_name}
\\- Calorías diarias: {total_calories} kcal
\\- IMC: {bmi} \\({bmi_category}\\)
\\- Plan de {total_days} días \\(Método Tres Días y Carga\\)
"""
    messages.append(header)
    
    # Check if meal data is included
    if 'meals' in plan_data and plan_data['meals']:
        meals_message = "\n🍽️ *Tu Plan de Comidas \(se repite los 3 días\):*\n"
        
        # Log for debugging
        logger.info(f"Meals data received: {list(plan_data['meals'].keys())}")
        
        # Define meal order
        meal_order = ['desayuno', 'colacion_am', 'almuerzo', 'merienda', 'cena', 'colacion_pm']
        meal_names = {
            'desayuno': 'Desayuno',
            'colacion_am': 'Colación AM',
            'almuerzo': 'Almuerzo',
            'merienda': 'Merienda',
            'cena': 'Cena',
            'colacion_pm': 'Colación PM'
        }
        
        for meal_type in meal_order:
            if meal_type in plan_data['meals']:
                meal = plan_data['meals'][meal_type]
                meal_emoji = get_meal_emoji(meal_type)
                
                meal_name = escape_markdown(meal_names.get(meal_type, meal_type.title()))
                meals_message += f"\n{meal_emoji} *{meal_name}*\n"
                
                if meal.get('name'):
                    recipe_name = escape_markdown(str(meal['name']))
                    meals_message += f"📝 {recipe_name}\n"
                
                if meal.get('ingredients'):
                    meals_message += "🥗 *Ingredientes:*\n"
                    for ingredient in meal['ingredients']:
                        if isinstance(ingredient, dict):
                            ing_name = escape_markdown(str(ingredient.get('alimento', ingredient.get('name', ''))))
                            ing_quantity = escape_markdown(str(ingredient.get('cantidad', ingredient.get('quantity', ''))))
                            meals_message += f"  • {ing_name} \- {ing_quantity}\n"
                        else:
                            ing_text = escape_markdown(str(ingredient))
                            meals_message += f"  • {ing_text}\n"
                
                if meal.get('preparation'):
                    prep_text = str(meal['preparation'])
                    # Truncate if too long
                    if len(prep_text) > 200:
                        prep_text = prep_text[:197] + "..."
                    prep_text = escape_markdown(prep_text)
                    meals_message += f"👨‍🍳 *Preparación:* {prep_text}\n"
                
                if meal.get('calories'):
                    calories = escape_markdown(str(meal['calories']))
                    meals_message += f"🔥 *Calorías:* {calories} kcal\n"
                
                if meal.get('macros'):
                    macros = meal['macros']
                    carb = escape_markdown(str(macros.get('carbohydrates', 0)))
                    prot = escape_markdown(str(macros.get('proteins', 0)))
                    fats = escape_markdown(str(macros.get('fats', 0)))
                    meals_message += f"📊 *Macros:* Carb: {carb}g \| Prot: {prot}g \| Grasas: {fats}g\n"
        
        messages.append(meals_message)
    else:
        # No meal data received
        logger.warning("No meal data received in plan_data")
        meals_per_day = escape_markdown(str(plan_data.get('plan_summary', {}).get('meals_per_day', 4)))
        total_cal = escape_markdown(str(plan_data.get('total_calories', plan_data.get('daily_calories', 'N/A'))))
        
        no_meals_message = f"""
🍽️ *Tu Plan de Comidas:*

{settings.EMOJI_INFO} El detalle completo de las comidas está siendo procesado y estará disponible en el PDF\.

Por ahora, tu plan incluye:
\- {meals_per_day} comidas principales al día
\- Total de calorías diarias: {total_cal} kcal

El PDF contendrá:
✅ Todas las recetas detalladas
✅ Ingredientes con cantidades exactas
✅ Instrucciones de preparación
✅ Información nutricional completa
✅ 3 opciones equivalentes por comida
"""
        messages.append(no_meals_message)
    
    # Summary message
    meals_per_day_sum = escape_markdown(str(plan_data['plan_summary']['meals_per_day']))
    economic_level = escape_markdown(str(plan_data['plan_summary']['economic_level']))
    pathologies = escape_markdown(', '.join(plan_data['plan_summary']['pathologies']) if plan_data['plan_summary']['pathologies'] else 'Ninguna')
    allergies = escape_markdown(', '.join(plan_data['plan_summary']['allergies']) if plan_data['plan_summary']['allergies'] else 'Ninguna')
    extra_message = escape_markdown(str(plan_data.get('message', '')))
    
    summary_message = f"""
📋 *Resumen del Plan:*
\- Comidas por día: {meals_per_day_sum}
\- Nivel económico: {economic_level}
\- Patologías consideradas: {pathologies}
\- Alergias consideradas: {allergies}

📄 Tu plan nutricional completo con todas las opciones está siendo generado en formato PDF\.
{extra_message}
"""
    messages.append(summary_message)
    
    # Add recommendations if present
    if 'recommendations' in plan_data:
        recommendations = escape_markdown(str(plan_data['recommendations']))
        rec_message = f"\n{settings.EMOJI_INFO} *Recomendaciones:*\n{recommendations}"
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