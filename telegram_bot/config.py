"""
Telegram Bot Configuration
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Bot configuration settings"""
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str
    
    # API Configuration
    API_BASE_URL: str = "http://api:8000"  # Using Docker service name
    API_TIMEOUT: int = 300  # 5 minutes for GPT-4 generation
    
    # Bot Configuration
    MAX_MESSAGE_LENGTH: int = 4096  # Telegram limit
    TYPING_DELAY: float = 0.5  # Delay between typing indicators
    
    # Conversation timeouts
    CONVERSATION_TIMEOUT: int = 600  # 10 minutes
    
    # Message intervals for long operations
    PROGRESS_MESSAGE_INTERVAL: int = 30  # seconds
    
    # Emojis for better UX
    EMOJI_WELCOME: str = "👋"
    EMOJI_FOOD: str = "🍽️"
    EMOJI_PLAN: str = "📋"
    EMOJI_LOADING: str = "⏳"
    EMOJI_SUCCESS: str = "✅"
    EMOJI_ERROR: str = "❌"
    EMOJI_INFO: str = "ℹ️"
    EMOJI_QUESTION: str = "❓"
    EMOJI_BREAKFAST: str = "🌅"
    EMOJI_LUNCH: str = "🍲"
    EMOJI_DINNER: str = "🌙"
    EMOJI_SNACK: str = "🥤"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Conversation states
class States:
    """Conversation states for handlers"""
    # New plan states
    NAME = 1
    AGE = 2
    GENDER = 3
    HEIGHT = 4
    WEIGHT = 5
    OBJECTIVE = 6
    ACTIVITY_TYPE = 7
    ACTIVITY_FREQUENCY = 8
    ACTIVITY_DURATION = 9
    SUPPLEMENTATION = 10
    PATHOLOGIES = 11
    MEDICATIONS = 12
    ALLERGIES = 13
    PREFERENCES = 14
    DISLIKES = 15
    MEAL_SCHEDULE = 16
    MEALS_PER_DAY = 17
    INCLUDE_SNACKS = 18
    ECONOMIC_LEVEL = 19
    FOOD_WEIGHT_TYPE = 20
    PERSONAL_NOTES = 21
    DAYS_REQUESTED = 22
    CONFIRM = 23
    GENERATING = 24
    
    # Meal replacement states
    MEAL_TO_REPLACE = 20
    MEAL_TYPE = 21
    REASON = 22
    AVOID_INGREDIENTS = 23
    SEARCHING = 24
    
    # Common states
    SELECTING_ACTION = 30