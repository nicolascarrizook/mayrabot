#!/usr/bin/env python3
"""
Debug script to test API call with new patient data format
"""

import asyncio
import aiohttp
import json

async def test_api_call():
    """Test the API with the new data format"""
    
    # Sample data matching what the bot sends
    test_data = {
        "name": "Test User",
        "age": 30,
        "gender": "male",
        "height": 170,
        "weight": 70,
        "objective": "mantenimiento",
        "activity_type": "pesas",
        "activity_frequency": 3,
        "activity_duration": 60,
        "supplementation": ["creatina"],
        "pathologies": [],
        "medications": [],
        "allergies": [],
        "food_preferences": ["pollo", "pescado"],
        "food_dislikes": ["hígado"],
        "meal_schedule": "Desayuno 8am, almuerzo 13hs, cena 20hs",
        "meals_per_day": 4,
        "include_snacks": True,
        "snack_type": "post",
        "days_requested": 3,
        "economic_level": "medio",
        "food_weight_type": "crudo",
        "personal_notes": "Test note"
    }
    
    print("Sending data:")
    print(json.dumps(test_data, indent=2))
    
    url = "http://localhost:8000/api/v1/motor1/generate-plan"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=test_data) as response:
                response_text = await response.text()
                print(f"\nStatus: {response.status}")
                print(f"Response: {response_text}")
                
                if response.status == 422:
                    # Parse validation error
                    error_data = json.loads(response_text)
                    print("\nValidation errors:")
                    for error in error_data.get('detail', []):
                        print(f"- Field: {error.get('loc', [])[-1]}")
                        print(f"  Error: {error.get('msg')}")
                        print(f"  Type: {error.get('type')}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_call())