#!/usr/bin/env python3
"""
Script para probar la API de Nutrition Bot
"""

import requests
import json
from datetime import datetime

# Base URL de la API
BASE_URL = "http://localhost:8002"

def test_health():
    """Probar endpoint de salud"""
    print("\n🔍 Probando endpoint de salud...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_motor1_validation():
    """Probar validación de datos del paciente"""
    print("\n🔍 Probando validación de paciente (Motor 1)...")
    
    patient_data = {
        "name": "María García",
        "age": 35,
        "gender": "female",
        "height": 165,
        "weight": 70,
        "activity_level": "moderate",
        "economic_level": "standard",
        "pathologies": ["diabetes tipo 2"],
        "allergies": ["frutos secos"],
        "food_preferences": ["pollo", "vegetales"],
        "food_dislikes": ["pescado"],
        "meals_per_day": 4,
        "days_requested": 7,
        "observations": "Prefiere comidas simples de preparar"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/motor1/validate-patient",
        json=patient_data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_motor1_generate_plan():
    """Probar generación de plan nutricional"""
    print("\n🔍 Probando generación de plan (Motor 1)...")
    
    patient_data = {
        "name": "Juan Pérez",
        "age": 45,
        "gender": "male",
        "height": 175,
        "weight": 85,
        "activity_level": "light",
        "economic_level": "standard",
        "pathologies": ["hipertension"],
        "allergies": [],
        "food_preferences": ["carne", "ensaladas"],
        "food_dislikes": ["cerdo"],
        "meals_per_day": 4,
        "days_requested": 7,
        "observations": "Necesita opciones bajas en sodio"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/motor1/generate-plan",
        json=patient_data
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Plan ID: {result.get('plan_id')}")
        print(f"Calorías diarias: {result.get('total_calories')}")
        print(f"IMC: {result.get('bmi')} ({result.get('bmi_category')})")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200

def test_motor2_analyze_progress():
    """Probar análisis de progreso"""
    print("\n🔍 Probando análisis de progreso (Motor 2)...")
    
    control_data = {
        "patient_data": {
            "name": "Ana López",
            "age": 30,
            "gender": "female",
            "height": 160,
            "weight": 65,
            "activity_level": "moderate",
            "economic_level": "standard",
            "pathologies": [],
            "allergies": [],
            "food_preferences": [],
            "food_dislikes": [],
            "meals_per_day": 4,
            "days_requested": 7
        },
        "current_weight": 63,
        "days_on_plan": 14,
        "adherence_percentage": 85,
        "reported_issues": ["Siento hambre entre comidas"],
        "requested_changes": ["Más opciones de snacks"],
        "new_pathologies": [],
        "new_medications": []
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/motor2/analyze-progress",
        json=control_data
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        progress = result.get('progress_analysis', {})
        print(f"Cambio de peso: {progress.get('weight_change')} kg")
        print(f"Estado: {progress.get('progress_status')}")
        print(f"Adherencia: {progress.get('adherence_status')}")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200

def test_motor3_meal_categories():
    """Probar obtención de categorías de comidas"""
    print("\n🔍 Probando categorías de comidas (Motor 3)...")
    
    response = requests.get(f"{BASE_URL}/api/v1/motor3/meal-categories")
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("Tipos de comida disponibles:")
        for meal_type, categories in result.get('meal_types', {}).items():
            print(f"  {meal_type}: {', '.join(categories)}")
    return response.status_code == 200

def test_motor3_find_alternatives():
    """Probar búsqueda de alternativas"""
    print("\n🔍 Probando búsqueda de alternativas (Motor 3)...")
    
    params = {
        "meal_type": "desayuno",
        "category": "desayuno_dulce",
        "avoid_ingredients": ["leche", "huevo"],
        "economic_level": "standard"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/motor3/find-alternatives",
        json=params
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Alternativas encontradas: {result.get('alternatives_found')}")
        alternatives = result.get('alternatives', [])
        for i, alt in enumerate(alternatives[:3], 1):
            print(f"\n{i}. {alt.get('recipe_name')}")
            print(f"   Categoría: {alt.get('category')}")
            print(f"   Match score: {alt.get('match_score')}")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 Iniciando pruebas de la API de Nutrition Bot")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Motor 1 - Validación", test_motor1_validation),
        ("Motor 1 - Generación de Plan", test_motor1_generate_plan),
        ("Motor 2 - Análisis de Progreso", test_motor2_analyze_progress),
        ("Motor 3 - Categorías", test_motor3_meal_categories),
        ("Motor 3 - Buscar Alternativas", test_motor3_find_alternatives)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, "✅" if success else "❌"))
        except Exception as e:
            print(f"Error en {test_name}: {e}")
            results.append((test_name, "❌"))
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS:")
    print("=" * 50)
    for test_name, status in results:
        print(f"{status} {test_name}")
    
    success_count = sum(1 for _, status in results if status == "✅")
    print(f"\nTotal: {success_count}/{len(results)} pruebas exitosas")

if __name__ == "__main__":
    main()