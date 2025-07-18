#!/bin/bash
# Prueba de búsqueda de recetas

echo "🔍 Test: Buscar recetas en ChromaDB"

# Buscar recetas de desayuno dulce
echo -e "\n📍 Buscando recetas de desayuno dulce:"
curl -s -X POST "http://localhost:8000/api/v1/motor3/find-alternatives" \
  -H "Content-Type: application/json" \
  -d '{
    "meal_type": "desayuno",
    "category": "desayuno_dulce",
    "avoid_ingredients": [],
    "economic_level": "standard"
  }' | python3 -m json.tool | head -50

# Buscar recetas de almuerzo con pollo
echo -e "\n📍 Buscando recetas de almuerzo con pollo:"
curl -s -X POST "http://localhost:8000/api/v1/motor3/find-alternatives" \
  -H "Content-Type: application/json" \
  -d '{
    "meal_type": "almuerzo",
    "category": "pollo",
    "avoid_ingredients": [],
    "economic_level": "standard"
  }' | python3 -m json.tool | head -50