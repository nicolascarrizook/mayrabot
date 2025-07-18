"""Test that enum values match between bot and API"""

# Bot sends these values
bot_activity_types = ["sedentario", "caminatas", "pesas", "funcional", "crossfit", "calistenia", "powerlifting", "running", "ciclismo", "futbol", "otro"]
bot_objectives = ["mantenimiento", "bajar_05", "bajar_1", "subir_05", "subir_1"]
bot_economic_levels = ["sin_restricciones", "medio", "limitado", "bajo_recursos"]
bot_weight_types = ["crudo", "cocido"]

# API expects these values (from models/patient.py)
from api.models.patient import ActivityType, Objective, EconomicLevel, FoodWeightType

print("Checking ActivityType values:")
for bot_val in bot_activity_types:
    try:
        ActivityType(bot_val)
        print(f"✓ {bot_val}")
    except ValueError:
        print(f"✗ {bot_val} - NOT VALID")

print("\nChecking Objective values:")
for bot_val in bot_objectives:
    try:
        Objective(bot_val)
        print(f"✓ {bot_val}")
    except ValueError:
        print(f"✗ {bot_val} - NOT VALID")

print("\nChecking EconomicLevel values:")
for bot_val in bot_economic_levels:
    try:
        EconomicLevel(bot_val)
        print(f"✓ {bot_val}")
    except ValueError:
        print(f"✗ {bot_val} - NOT VALID")

print("\nChecking FoodWeightType values:")
for bot_val in bot_weight_types:
    try:
        FoodWeightType(bot_val)
        print(f"✓ {bot_val}")
    except ValueError:
        print(f"✗ {bot_val} - NOT VALID")