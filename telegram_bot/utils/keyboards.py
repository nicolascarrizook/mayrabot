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


def get_objective_keyboard() -> InlineKeyboardMarkup:
    """Get weight objective keyboard."""
    keyboard = [
        [InlineKeyboardButton("⚖️ Mantenimiento", callback_data='obj_mantenimiento')],
        [InlineKeyboardButton("📉 Bajar 0,5 kg/semana", callback_data='obj_bajar_05')],
        [InlineKeyboardButton("📉 Bajar 1 kg/semana", callback_data='obj_bajar_1')],
        [InlineKeyboardButton("📈 Subir 0,5 kg/semana", callback_data='obj_subir_05')],
        [InlineKeyboardButton("📈 Subir 1 kg/semana", callback_data='obj_subir_1')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_activity_type_keyboard() -> InlineKeyboardMarkup:
    """Get activity type keyboard."""
    keyboard = [
        [InlineKeyboardButton("💤 Sedentario", callback_data='type_sedentario')],
        [InlineKeyboardButton("🚶 Caminatas", callback_data='type_caminatas')],
        [InlineKeyboardButton("🏋️ Pesas", callback_data='type_pesas')],
        [InlineKeyboardButton("🤸 Funcional", callback_data='type_funcional')],
        [InlineKeyboardButton("💪 Crossfit", callback_data='type_crossfit')],
        [InlineKeyboardButton("🤾 Calistenia", callback_data='type_calistenia')],
        [InlineKeyboardButton("🏋️ Powerlifting", callback_data='type_powerlifting')],
        [InlineKeyboardButton("🏃 Running", callback_data='type_running')],
        [InlineKeyboardButton("🚴 Ciclismo", callback_data='type_ciclismo')],
        [InlineKeyboardButton("⚽ Fútbol", callback_data='type_futbol')],
        [InlineKeyboardButton("🎯 Otro", callback_data='type_otro')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_activity_frequency_keyboard() -> InlineKeyboardMarkup:
    """Get activity frequency keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("1x", callback_data='freq_1'),
            InlineKeyboardButton("2x", callback_data='freq_2'),
            InlineKeyboardButton("3x", callback_data='freq_3')
        ],
        [
            InlineKeyboardButton("4x", callback_data='freq_4'),
            InlineKeyboardButton("5x", callback_data='freq_5'),
            InlineKeyboardButton("6x", callback_data='freq_6')
        ],
        [
            InlineKeyboardButton("7x (todos los días)", callback_data='freq_7')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_activity_duration_keyboard() -> InlineKeyboardMarkup:
    """Get activity duration keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("30 min", callback_data='dur_30'),
            InlineKeyboardButton("45 min", callback_data='dur_45')
        ],
        [
            InlineKeyboardButton("60 min", callback_data='dur_60'),
            InlineKeyboardButton("75 min", callback_data='dur_75')
        ],
        [
            InlineKeyboardButton("90 min", callback_data='dur_90'),
            InlineKeyboardButton("120 min", callback_data='dur_120')
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
            InlineKeyboardButton("3 comidas principales", callback_data='meals_3'),
            InlineKeyboardButton("4 comidas principales", callback_data='meals_4')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_snacks_keyboard() -> InlineKeyboardMarkup:
    """Get snacks/colaciones keyboard."""
    keyboard = [
        [InlineKeyboardButton("❌ No incluir colaciones", callback_data='snack_no')],
        [InlineKeyboardButton("🍎 Por saciedad", callback_data='snack_saciedad')],
        [InlineKeyboardButton("🏋️ Pre-entreno", callback_data='snack_pre')],
        [InlineKeyboardButton("💪 Post-entreno", callback_data='snack_post')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_food_weight_type_keyboard() -> InlineKeyboardMarkup:
    """Get food weight type keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🥩 Gramos en crudo", callback_data='weight_crudo'),
            InlineKeyboardButton("🍳 Gramos en cocido", callback_data='weight_cocido')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_days_keyboard() -> InlineKeyboardMarkup:
    """Get days selection keyboard - Always 3 days for Tres Días y Carga."""
    keyboard = [
        [
            InlineKeyboardButton("📅 3 días (Método Tres Días y Carga)", callback_data='days_3')
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
        [InlineKeyboardButton("💸 Sin restricciones", callback_data='economic_sin_restricciones')],
        [InlineKeyboardButton("💵 Medio", callback_data='economic_medio')],
        [InlineKeyboardButton("💰 Limitado", callback_data='economic_limitado')],
        [InlineKeyboardButton("🏠 Bajo recursos", callback_data='economic_bajo_recursos')]
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