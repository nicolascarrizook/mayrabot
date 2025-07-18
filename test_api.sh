#!/bin/bash
# Script para probar la API de Nutrition Bot

BASE_URL="http://localhost:8002"

echo "🚀 Iniciando pruebas de la API de Nutrition Bot"
echo "=================================================="

# Test 1: Health Check
echo -e "\n🔍 Test 1: Health Check"
curl -s "$BASE_URL/health" | python3 -m json.tool

# Test 2: Detailed Health Check
echo -e "\n🔍 Test 2: Detailed Health Check"
curl -s "$BASE_URL/health/detailed" | python3 -m json.tool

# Test 3: Motor 1 - Validación de paciente
echo -e "\n🔍 Test 3: Motor 1 - Validación de paciente"
curl -s -X POST "$BASE_URL/api/v1/motor1/validate-patient" \
  -H "Content-Type: application/json" \
  -d '{
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
  }' | python3 -m json.tool

# Test 4: Motor 2 - Análisis de progreso
echo -e "\n🔍 Test 4: Motor 2 - Análisis de progreso"
curl -s -X POST "$BASE_URL/api/v1/motor2/analyze-progress" \
  -H "Content-Type: application/json" \
  -d '{
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
  }' | python3 -m json.tool

# Test 5: Motor 3 - Categorías de comidas
echo -e "\n🔍 Test 5: Motor 3 - Categorías de comidas"
curl -s "$BASE_URL/api/v1/motor3/meal-categories" | python3 -m json.tool

# Test 6: Motor 3 - Buscar alternativas
echo -e "\n🔍 Test 6: Motor 3 - Buscar alternativas de desayuno"
curl -s -X POST "$BASE_URL/api/v1/motor3/find-alternatives" \
  -H "Content-Type: application/json" \
  -d '{
    "meal_type": "desayuno",
    "category": "desayuno_dulce",
    "avoid_ingredients": ["leche", "huevo"],
    "economic_level": "standard"
  }' | python3 -m json.tool

echo -e "\n✅ Pruebas completadas"