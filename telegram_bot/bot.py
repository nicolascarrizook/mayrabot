#!/usr/bin/env python3
"""
Nutrition Bot - Telegram Bot Main Application
"""

import logging
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
)
from dotenv import load_dotenv

from telegram_bot.config import settings
from telegram_bot.handlers import (
    start_handler,
    new_plan_handler,
    meal_replacement_handler,
    help_handler,
    error_handler,
    secretary_mode
)
from telegram_bot.middleware.error_middleware import error_callback

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    # Start command
    application.add_handler(CommandHandler("start", start_handler.start))
    
    # Help command
    application.add_handler(CommandHandler("ayuda", help_handler.help_command))
    application.add_handler(CommandHandler("help", help_handler.help_command))
    
    # New plan conversation
    application.add_handler(new_plan_handler.get_new_plan_handler())
    
    # Meal replacement conversation
    application.add_handler(meal_replacement_handler.get_meal_replacement_handler())
    
    # Secretary mode conversation
    application.add_handler(secretary_mode.get_secretary_handler())
    
    # Cancel command (works globally)
    application.add_handler(CommandHandler("cancelar", start_handler.cancel))
    application.add_handler(CommandHandler("cancel", start_handler.cancel))
    
    # Callback query handler for inline keyboards
    application.add_handler(CallbackQueryHandler(start_handler.button_callback))
    
    # Error handler
    application.add_error_handler(error_callback)
    
    # Log startup
    logger.info("Bot started successfully!")
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()