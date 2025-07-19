"""
Input validators for Telegram Bot
"""

import re
from typing import Optional, Tuple


def validate_name(name: str) -> Tuple[bool, Optional[str]]:
    """Validate patient name."""
    name = name.strip()
    
    if len(name) < 2:
        return False, "El nombre debe tener al menos 2 caracteres."
    
    if len(name) > 100:
        return False, "El nombre es demasiado largo (máximo 100 caracteres)."
    
    if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s'-]+$", name):
        return False, "El nombre solo puede contener letras, espacios y guiones."
    
    return True, None


def validate_age(age_str: str) -> Tuple[bool, Optional[str]]:
    """Validate age input."""
    try:
        age = int(age_str.strip())
        if age < 1:
            return False, "La edad debe ser mayor a 0."
        if age > 120:
            return False, "Por favor, ingresa una edad válida."
        return True, None
    except ValueError:
        return False, "Por favor, ingresa un número válido para la edad."


def validate_height(height_str: str) -> Tuple[bool, Optional[str]]:
    """Validate height in cm."""
    try:
        # Accept both comma and dot as decimal separator
        height_str = height_str.replace(',', '.').strip()
        height = float(height_str)
        
        if height < 50:
            return False, "La altura debe ser mayor a 50 cm."
        if height > 250:
            return False, "Por favor, ingresa una altura válida en centímetros."
        
        return True, None
    except ValueError:
        return False, "Por favor, ingresa un número válido para la altura (ej: 170 o 170.5)."


def validate_weight(weight_str: str) -> Tuple[bool, Optional[str]]:
    """Validate weight in kg."""
    try:
        # Accept both comma and dot as decimal separator
        weight_str = weight_str.replace(',', '.').strip()
        weight = float(weight_str)
        
        if weight < 20:
            return False, "El peso debe ser mayor a 20 kg."
        if weight > 300:
            return False, "Por favor, ingresa un peso válido en kilogramos."
        
        return True, None
    except ValueError:
        return False, "Por favor, ingresa un número válido para el peso (ej: 70 o 70.5)."


def validate_text_list(text: str, field_name: str, max_length: int = 500) -> Tuple[bool, Optional[str]]:
    """Validate text input for lists (pathologies, allergies, etc)."""
    text = text.strip()
    
    if len(text) > max_length:
        return False, f"El texto es demasiado largo (máximo {max_length} caracteres)."
    
    # Check for suspicious patterns
    if re.search(r'<[^>]+>', text):
        return False, "El texto contiene caracteres no permitidos."
    
    return True, None


def validate_meal_count(meal_str: str) -> Tuple[bool, Optional[str]]:
    """Validate meal count input."""
    try:
        meals = int(meal_str.strip())
        if meals < 3 or meals > 6:
            return False, "El número de comidas debe estar entre 3 y 6."
        return True, None
    except ValueError:
        return False, "Por favor, ingresa un número válido (3-6)."


def validate_days(days_str: str) -> Tuple[bool, Optional[str]]:
    """Validate days requested."""
    try:
        days = int(days_str.strip())
        if days not in [1, 3, 7, 14]:
            return False, "Por favor selecciona 1, 3, 7 o 14 días."
        return True, None
    except ValueError:
        return False, "Por favor, ingresa un número válido."


def sanitize_input(text: str) -> str:
    """Sanitize user input for safety."""
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>{}\\]', '', text)
    
    return text


def format_list_input(text: str) -> str:
    """Format list input (pathologies, allergies, etc) for consistency."""
    if not text or text.lower() in ['no', 'ninguno', 'ninguna', 'n/a', '-']:
        return "Ninguno"
    
    # Capitalize first letter of each item
    items = [item.strip().capitalize() for item in text.split(',')]
    return ', '.join(items)


def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """Validate phone number for secretary use."""
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    if not phone:
        return False, "Por favor, ingresá un número de teléfono."
    
    # Accept various formats
    if re.match(r'^\+?549?\d{10,}$', phone):
        return True, None
    
    return False, "Por favor, ingresá un número de teléfono válido (ej: +5491112345678)."


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Validate email address."""
    email = email.strip().lower()
    
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return False, "Por favor, ingresá un email válido."
    
    return True, None


def validate_activity_level(activity_type: str, frequency: int, duration: int) -> str:
    """Calculate activity level based on type, frequency and duration."""
    if activity_type == 'sedentario':
        return 'sedentary'
    
    total_minutes = frequency * duration
    
    if total_minutes < 150:
        return 'light'
    elif total_minutes < 300:
        return 'moderate'
    elif total_minutes < 450:
        return 'active'
    else:
        return 'very_active'