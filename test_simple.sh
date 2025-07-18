#!/bin/bash
# Prueba simple de la API

echo "🔍 Test 1: Health Check"
curl -s "http://localhost:8000/health" | python3 -m json.tool

echo -e "\n🔍 Test 2: Motor 1 - Generación de Plan"
curl -s -X POST "http://localhost:8000/api/v1/motor1/generate-plan" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "age": 30,
    "gender": "male",
    "height": 175,
    "weight": 75,
    "activity_level": "moderate",
    "economic_level": "standard",
    "pathologies": [],
    "allergies": [],
    "food_preferences": [],
    "food_dislikes": [],
    "meals_per_day": 4,
    "days_requested": 7
  }'

echo -e "\n🔍 Test 3: Motor 3 - Buscar Recetas de Desayuno"
# Primero veamos qué recetas de desayuno tenemos
curl -s -X POST "http://localhost:8000/api/v1/motor3/find-alternatives" \
  -H "Content-Type: application/json" \
  -d '{
    "meal_type": "desayuno",
    "category": "desayuno_dulce",
    "avoid_ingredients": [],
    "economic_level": "standard"
  }' | python3 -m json.tool