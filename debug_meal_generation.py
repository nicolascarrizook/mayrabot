#!/usr/bin/env python3
"""
Debug script to test meal generation locally
"""

import asyncio
import logging
from datetime import date, timedelta
from api.models.patient import PatientData, Gender, ActivityLevel, Objective, ActivityType
from api.services.chromadb_service import ChromaDBService
from api.services.plan_generator import PlanGeneratorService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_meal_generation():
    """Test the meal generation process"""
    
    # Create test patient data
    patient_data = PatientData(
        name="Test Patient",
        age=30,
        gender=Gender.MALE,
        height=175,
        weight=75,
        objective=Objective.MANTENIMIENTO,
        activity_type=ActivityType.PESAS,
        activity_frequency=3,
        activity_duration=60,
        meals_per_day=4,
        include_snacks=False
    )
    
    # Initialize services
    chromadb = ChromaDBService()
    plan_generator = PlanGeneratorService(chromadb)
    
    print(f"Generating plan for: {patient_data.name}")
    print(f"Objective: {patient_data.objective}")
    print(f"Activity: {patient_data.activity_type} - {patient_data.activity_frequency}x/week")
    
    # Generate plan
    try:
        nutrition_plan = await plan_generator.generate_plan(patient_data)
        
        print(f"\n=== NUTRITION PLAN STRUCTURE ===")
        print(f"Type: {type(nutrition_plan)}")
        print(f"Has days: {hasattr(nutrition_plan, 'days')}")
        
        if hasattr(nutrition_plan, 'days') and nutrition_plan.days:
            print(f"Number of days: {len(nutrition_plan.days)}")
            
            first_day = nutrition_plan.days[0]
            print(f"\nFirst day type: {type(first_day)}")
            print(f"First day has meals: {hasattr(first_day, 'meals')}")
            
            if hasattr(first_day, 'meals'):
                print(f"Meals type: {type(first_day.meals)}")
                
                if isinstance(first_day.meals, dict):
                    print(f"Meal types: {list(first_day.meals.keys())}")
                    
                    # Print first meal details
                    for meal_type, meal_data in first_day.meals.items():
                        print(f"\n=== {meal_type.upper()} ===")
                        print(f"Type: {type(meal_data)}")
                        
                        if isinstance(meal_data, dict):
                            for key, value in meal_data.items():
                                if key == 'ingredients' and isinstance(value, list) and len(value) > 3:
                                    print(f"{key}: {value[:3]}... (total: {len(value)} items)")
                                elif key == 'preparation' and isinstance(value, str) and len(value) > 100:
                                    print(f"{key}: {value[:100]}...")
                                else:
                                    print(f"{key}: {value}")
                        else:
                            print(f"Meal data is not a dict: {meal_data}")
                        
                        break  # Just show first meal
    
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_meal_generation())