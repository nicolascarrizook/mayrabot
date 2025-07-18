"""
Keyboard utilities for Telegram Bot
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Tuple

from telegram_bot.config import settings


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Get the main menu keyboard."""
    keyboard = [
        [InlineKeyboardButton(f"{settings.EMOJI_PLAN} Nuevo Plan Nutricional", callback_data='new_plan')],
        [InlineKeyboardButton(f"{settings.EMOJI_FOOD} Reemplazar Comida", callback_data='replace_meal')],
        [InlineKeyboardButton(f"{settings.EMOJI_INFO} Ayuda", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_gender_keyboard() -> InlineKeyboardMarkup:
    """Get gender selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("👨 Masculino", callback_data='gender_M'),
            InlineKeyboardButton("👩 Femenino", callback_data='gender_F')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_activity_level_keyboard() -> InlineKeyboardMarkup:
    """Get physical activity level keyboard."""
    keyboard = [
        [InlineKeyboardButton("💤 Sedentario", callback_data='activity_sedentario')],
        [InlineKeyboardButton("🚶 Ligera", callback_data='activity_ligera')],
        [InlineKeyboardButton("🏃 Moderada", callback_data='activity_moderada')],
        [InlineKeyboardButton("🏋️ Intensa", callback_data='activity_intensa')],
        [InlineKeyboardButton("🏅 Muy Intensa", callback_data='activity_muy_intensa')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    """Get yes/no keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Sí", callback_data='yes'),
            InlineKeyboardButton("❌ No", callback_data='no')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_meals_per_day_keyboard() -> InlineKeyboardMarkup:
    """Get meals per day selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("3 comidas", callback_data='meals_3'),
            InlineKeyboardButton("4 comidas", callback_data='meals_4')
        ],
        [
            InlineKeyboardButton("5 comidas", callback_data='meals_5'),
            InlineKeyboardButton("6 comidas", callback_data='meals_6')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_days_keyboard() -> InlineKeyboardMarkup:
    """Get days selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("1 día", callback_data='days_1'),
            InlineKeyboardButton("3 días", callback_data='days_3')
        ],
        [
            InlineKeyboardButton("7 días", callback_data='days_7'),
            InlineKeyboardButton("14 días", callback_data='days_14')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_meal_type_keyboard() -> InlineKeyboardMarkup:
    """Get meal type selection keyboard for replacement."""
    keyboard = [
        [InlineKeyboardButton(f"{settings.EMOJI_BREAKFAST} Desayuno", callback_data='meal_desayuno')],
        [InlineKeyboardButton(f"{settings.EMOJI_SNACK} Media Mañana", callback_data='meal_media_manana')],
        [InlineKeyboardButton(f"{settings.EMOJI_LUNCH} Almuerzo", callback_data='meal_almuerzo')],
        [InlineKeyboardButton(f"{settings.EMOJI_SNACK} Merienda", callback_data='meal_merienda')],
        [InlineKeyboardButton(f"{settings.EMOJI_DINNER} Cena", callback_data='meal_cena')],
        [InlineKeyboardButton(f"{settings.EMOJI_SNACK} Colación", callback_data='meal_colacion')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Get cancel keyboard."""
    keyboard = [
        [InlineKeyboardButton("❌ Cancelar", callback_data='cancel')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Get back to main menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("🏠 Volver al Menú Principal", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard(data_summary: str) -> InlineKeyboardMarkup:
    """Get confirmation keyboard with data summary."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmar", callback_data='confirm_yes'),
            InlineKeyboardButton("❌ Cancelar", callback_data='confirm_no')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_economic_level_keyboard() -> InlineKeyboardMarkup:
    """Get economic level selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("💰 Económico", callback_data='economic_economico'),
            InlineKeyboardButton("💵 Estándar", callback_data='economic_standard')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_alternative_selection_keyboard(alternatives: List[dict]) -> InlineKeyboardMarkup:
    """Create keyboard for selecting meal alternatives."""
    keyboard = []
    for i, alt in enumerate(alternatives[:5]):  # Show max 5 alternatives
        button_text = f"{i+1}. {alt['name']} ({alt['calories']} kcal)"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'select_alt_{i}')])
    
    keyboard.append([InlineKeyboardButton("🔍 Buscar otra vez", callback_data='search_again')])
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data='cancel')])
    
    return InlineKeyboardMarkup(keyboard)