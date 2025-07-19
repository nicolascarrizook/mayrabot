#!/usr/bin/env python3
"""
Test script to verify equitable distribution implementation
"""

import sys
sys.path.append('.')

from prompts.base_prompt import BasePromptTemplate

def test_distributions():
    """Test both traditional and equitable distributions"""
    
    # Test parameters
    meals_per_day = 4
    daily_calories = 2000
    carbs_percent = 0.45
    protein_percent = 0.25
    fat_percent = 0.30
    
    print("=" * 80)
    print("TESTING MEAL DISTRIBUTIONS")
    print("=" * 80)
    print(f"\nTotal daily calories: {daily_calories} kcal")
    print(f"Macros: {carbs_percent*100}% carbs, {protein_percent*100}% protein, {fat_percent*100}% fat")
    print(f"Number of meals: {meals_per_day}")
    
    # Test traditional distribution
    print("\n" + "=" * 80)
    print("TRADITIONAL DISTRIBUTION:")
    print("=" * 80)
    traditional = BasePromptTemplate.format_meal_distribution(
        meals_per_day=meals_per_day,
        daily_calories=daily_calories,
        carbs_percent=carbs_percent,
        protein_percent=protein_percent,
        fat_percent=fat_percent,
        distribution_type="traditional"
    )
    print(traditional)
    
    # Test equitable distribution
    print("\n" + "=" * 80)
    print("EQUITABLE DISTRIBUTION:")
    print("=" * 80)
    equitable = BasePromptTemplate.format_meal_distribution(
        meals_per_day=meals_per_day,
        daily_calories=daily_calories,
        carbs_percent=carbs_percent,
        protein_percent=protein_percent,
        fat_percent=fat_percent,
        distribution_type="equitable"
    )
    print(equitable)
    
    # Verify equitable distribution calculations
    print("\n" + "=" * 80)
    print("VERIFICATION:")
    print("=" * 80)
    
    calories_per_meal = daily_calories / meals_per_day
    carbs_per_meal = (daily_calories * carbs_percent) / 4 / meals_per_day
    protein_per_meal = (daily_calories * protein_percent) / 4 / meals_per_day
    fat_per_meal = (daily_calories * fat_percent) / 9 / meals_per_day
    
    print(f"Expected values per meal (equitable):")
    print(f"  - Calories: {calories_per_meal:.0f} kcal")
    print(f"  - Carbs: {carbs_per_meal:.0f}g ({carbs_per_meal * 4:.0f} kcal)")
    print(f"  - Protein: {protein_per_meal:.0f}g ({protein_per_meal * 4:.0f} kcal)")
    print(f"  - Fat: {fat_per_meal:.0f}g ({fat_per_meal * 9:.0f} kcal)")
    
    # Test with 3 meals
    print("\n" + "=" * 80)
    print("EQUITABLE DISTRIBUTION WITH 3 MEALS:")
    print("=" * 80)
    equitable_3 = BasePromptTemplate.format_meal_distribution(
        meals_per_day=3,
        daily_calories=1500,
        carbs_percent=0.40,
        protein_percent=0.30,
        fat_percent=0.30,
        distribution_type="equitable"
    )
    print(equitable_3)

if __name__ == "__main__":
    test_distributions()