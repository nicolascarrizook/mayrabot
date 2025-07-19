"""
Base Prompt Template and Utilities
"""

from typing import Dict, Any, List, Optional
import json


class BasePromptTemplate:
    """Base class for all prompt templates"""
    
    @staticmethod
    def format_patient_info(patient_data: Dict[str, Any]) -> str:
        """Format patient information for prompts"""
        # Map objective to display text
        objective_map = {
            'mantenimiento': 'Mantenimiento',
            'bajar_025': 'Bajar 0,25 kg/semana',
            'bajar_05': 'Bajar 0,5 kg/semana',
            'bajar_075': 'Bajar 0,75 kg/semana',
            'bajar_1': 'Bajar 1 kg/semana',
            'subir_025': 'Subir 0,25 kg/semana',
            'subir_05': 'Subir 0,5 kg/semana',
            'subir_075': 'Subir 0,75 kg/semana',
            'subir_1': 'Subir 1 kg/semana'
        }
        
        return f"""
DATOS DEL PACIENTE:

Nombre: {patient_data.get('name', 'No especificado')}
Edad: {patient_data.get('age', 'No especificado')} años
Sexo: {'M' if patient_data.get('gender') == 'male' else 'F'}
Estatura: {patient_data.get('height', 'No especificado')} cm
Peso: {patient_data.get('weight', 'No especificado')} kg
IMC: {patient_data.get('bmi', 'No calculado')} ({patient_data.get('bmi_category', 'No categorizado')})

Objetivo: {objective_map.get(patient_data.get('objective', ''), 'No especificado')}

Tipo de actividad física: {patient_data.get('activity_type', 'No especificado')}
Frecuencia semanal: {patient_data.get('activity_frequency', 'No especificado')}x
Duración por sesión: {patient_data.get('activity_duration', 'No especificado')} minutos

Suplementación: {', '.join(patient_data.get('supplementation', [])) or 'Ninguna'}
Patologías / Medicación: {', '.join(patient_data.get('pathologies', [])) or 'Ninguna'} / {', '.join(patient_data.get('medications', [])) or 'Ninguna'}
NO consume: {', '.join(patient_data.get('food_dislikes', [])) or 'Ninguno'}
Le gusta: {', '.join(patient_data.get('food_preferences', [])) or 'Ninguno'}
Horario habitual de comidas y entrenamiento: {patient_data.get('meal_schedule', 'No especificado')}

Nivel económico: {patient_data.get('economic_level', 'medio')}
Notas personales: {patient_data.get('personal_notes', 'Ninguna')}

Tipo de peso a utilizar: Gramos en {patient_data.get('food_weight_type', 'crudo')}

Especificaciones:
- Comidas principales: {patient_data.get('meals_per_day', 4)}
- Incluir colaciones: {'Sí - ' + patient_data.get('snack_type', '') if patient_data.get('include_snacks') else 'No'}

{BasePromptTemplate._format_macro_customization(patient_data)}
"""

    @staticmethod
    def _format_macro_customization(patient_data: Dict[str, Any]) -> str:
        """Format macro customization information if present"""
        protein_level = patient_data.get('protein_level')
        carbs_percentage = patient_data.get('carbs_percentage')
        fat_percentage = patient_data.get('fat_percentage')
        
        if not protein_level and carbs_percentage is None and not fat_percentage:
            return ""
        
        text = "Personalización de Macronutrientes:\n"
        
        if protein_level:
            protein_levels_text = {
                'muy_baja': 'Muy baja (0.5-0.8 g/kg) - Patologías renales',
                'conservada': 'Conservada (0.8-1.2 g/kg) - Normal',
                'moderada': 'Moderada (1.2-1.6 g/kg) - Personas activas',
                'alta': 'Alta (1.6-2.2 g/kg) - Uso deportivo',
                'muy_alta': 'Muy alta (2.2-2.8 g/kg) - Alto rendimiento',
                'extrema': 'Extrema (3.0-3.5 g/kg) - Atletas especiales'
            }
            text += f"- Nivel de proteína: {protein_levels_text.get(protein_level, protein_level)}\n"
        
        if carbs_percentage is not None:
            text += f"- Porcentaje de carbohidratos: {carbs_percentage}%\n"
        
        if fat_percentage:
            text += f"- Porcentaje de grasas: {fat_percentage}%\n"
        
        return text

    @staticmethod
    def format_recipes_list(recipes: List[Dict[str, Any]]) -> str:
        """Format recipes list for prompts with strong emphasis on exact names"""
        if not recipes:
            return "No se encontraron recetas disponibles."
        
        recipes_text = "🚨 LISTA DE RECETAS PERMITIDAS - USA SOLO ESTAS 🚨\n"
        recipes_text += "=" * 80 + "\n"
        recipes_text += "INSTRUCCIÓN CRÍTICA: Copia y pega EXACTAMENTE los nombres de estas recetas\n"
        recipes_text += "=" * 80 + "\n\n"
        
        # Group recipes by meal type for easier selection
        recipes_by_type = {}
        for recipe in recipes:
            meal_types = recipe.get('metadata', {}).get('meal_types', '[]')
            if isinstance(meal_types, str):
                try:
                    meal_types = eval(meal_types)
                except:
                    meal_types = []
            
            for meal_type in meal_types:
                if meal_type not in recipes_by_type:
                    recipes_by_type[meal_type] = []
                recipes_by_type[meal_type].append(recipe)
        
        # Format by meal type
        for meal_type in ['desayuno', 'almuerzo', 'cena', 'merienda', 'colacion']:
            if meal_type in recipes_by_type:
                recipes_text += f"\n### RECETAS PARA {meal_type.upper()}:\n"
                recipes_text += "-" * 60 + "\n"
                
                for recipe in recipes_by_type[meal_type]:
                    recipe_name = recipe.get('metadata', {}).get('recipe_name', 'Sin nombre')
                    calories = recipe.get('metadata', {}).get('calories', 'No especificado')
                    
                    recipes_text += f"✅ NOMBRE: \"{recipe_name}\"\n"
                    recipes_text += f"   Calorías: {calories} kcal\n"
                    recipes_text += f"   Copiar exactamente: {recipe_name}\n"
                    recipes_text += "-" * 40 + "\n"
        
        recipes_text += "\n" + "=" * 80 + "\n"
        recipes_text += "⚠️ RECORDATORIO FINAL:\n"
        recipes_text += "1. USA SOLO los nombres exactos listados arriba\n"
        recipes_text += "2. COPIA Y PEGA el nombre tal cual aparece\n"
        recipes_text += "3. NO inventes ni modifiques nombres\n"
        recipes_text += "4. El sistema RECHAZARÁ cualquier receta no listada\n"
        recipes_text += "=" * 80 + "\n"
        
        return recipes_text

    @staticmethod
    def format_equivalences(equivalences: Optional[Dict[str, Any]]) -> str:
        """Format equivalences for prompts"""
        if not equivalences:
            return ""
        
        equiv_text = "\n📊 TABLAS DE EQUIVALENCIAS DISPONIBLES:\n"
        equiv_text += "=" * 60 + "\n"
        equiv_text += "Puedes usar estas equivalencias para sustituir ingredientes:\n\n"
        
        for category, items in equivalences.items():
            if isinstance(items, list) and items:
                equiv_text += f"### {category.upper()}:\n"
                for item in items[:5]:  # Show first 5 items
                    if isinstance(item, dict):
                        equiv_text += f"• {item}\n"
                equiv_text += "\n"
        
        equiv_text += "Usa estas equivalencias para hacer sustituciones inteligentes cuando sea necesario.\n"
        equiv_text += "=" * 60 + "\n"
        
        return equiv_text

    @staticmethod
    def format_nutritional_requirements(requirements: Dict[str, Any]) -> str:
        """Format nutritional requirements"""
        return f"""
REQUERIMIENTOS NUTRICIONALES:
- Calorías diarias objetivo: {requirements.get('daily_calories', 2000)} kcal
- Distribución de macronutrientes:
  * Carbohidratos: {requirements.get('carbs_percentage', 45)}%
  * Proteínas: {requirements.get('protein_percentage', 25)}%
  * Grasas: {requirements.get('fat_percentage', 30)}%
- Consideraciones especiales: {', '.join(requirements.get('special_considerations', [])) or 'Ninguna'}
"""

    @staticmethod
    def format_meal_distribution(meals_per_day: int, daily_calories: int = 2000, 
                               carbs_percent: float = 0.45, protein_percent: float = 0.25, 
                               fat_percent: float = 0.30, distribution_type: str = "traditional") -> str:
        """Format meal distribution throughout the day with macros breakdown"""
        
        # Calculate total daily macros
        total_carbs_g = round((daily_calories * carbs_percent) / 4)
        total_protein_g = round((daily_calories * protein_percent) / 4)
        total_fat_g = round((daily_calories * fat_percent) / 9)
        
        # Meal percentages
        if distribution_type == "equitable":
            # Equal distribution for all meals
            meal_types = {
                3: ["desayuno", "almuerzo", "cena"],
                4: ["desayuno", "almuerzo", "merienda", "cena"],
                5: ["desayuno", "colacion_am", "almuerzo", "merienda", "cena"],
                6: ["desayuno", "colacion_am", "almuerzo", "merienda", "cena", "colacion_pm"]
            }
            meals = meal_types.get(meals_per_day, meal_types[4])
            equal_percentage = 1.0 / len(meals)
            percentages = {meal: equal_percentage for meal in meals}
        else:
            # Traditional distribution
            meal_percentages = {
                3: {"desayuno": 0.30, "almuerzo": 0.40, "cena": 0.30},
                4: {"desayuno": 0.25, "almuerzo": 0.35, "merienda": 0.15, "cena": 0.25},
                5: {"desayuno": 0.20, "colacion_am": 0.10, "almuerzo": 0.35, 
                    "merienda": 0.15, "cena": 0.20},
                6: {"desayuno": 0.20, "colacion_am": 0.10, "almuerzo": 0.30,
                    "merienda": 0.10, "cena": 0.20, "colacion_pm": 0.10}
            }
            percentages = meal_percentages.get(meals_per_day, meal_percentages[4])
        
        distribution_label = "EQUITATIVA" if distribution_type == "equitable" else "TRADICIONAL"
        result = f"""
DISTRIBUCIÓN DE COMIDAS ({meals_per_day} comidas/día - Distribución {distribution_label}):
Calorías totales: {daily_calories} kcal
Macros totales: {total_carbs_g}g carbs | {total_protein_g}g proteína | {total_fat_g}g grasa

"""
        
        # Calculate for each meal
        meal_times = {
            "desayuno": "7:00-9:00",
            "colacion_am": "10:30-11:00",
            "almuerzo": "13:00-14:00",
            "merienda": "16:00-17:00",
            "cena": "20:00-21:00",
            "colacion_pm": "22:00"
        }
        
        for meal, percentage in percentages.items():
            meal_calories = round(daily_calories * percentage)
            meal_carbs_g = round(total_carbs_g * percentage)
            meal_protein_g = round(total_protein_g * percentage)
            meal_fat_g = round(total_fat_g * percentage)
            
            meal_carbs_kcal = meal_carbs_g * 4
            meal_protein_kcal = meal_protein_g * 4
            meal_fat_kcal = meal_fat_g * 9
            
            meal_name = meal.replace("_", " ").title()
            result += f"""- {meal_name} ({meal_times.get(meal, "")}): {percentage*100:.0f}% = {meal_calories} kcal
  → Carbohidratos: {meal_carbs_g}g ({meal_carbs_kcal} kcal)
  → Proteínas: {meal_protein_g}g ({meal_protein_kcal} kcal)
  → Grasas: {meal_fat_g}g ({meal_fat_kcal} kcal)

"""
        
        return result.rstrip()

    @staticmethod
    def get_system_prompt() -> str:
        """Get the system prompt for the nutritionist role"""
        return """Eres una nutricionista profesional especializada en el método Tres Días y Carga | Dieta Inteligente® & Nutrición Evolutiva.

REGLAS DEL MÉTODO (que siempre se respetan):

1. Plan de 3 días iguales en calorías y macronutrientes
2. Todas las comidas en gramos (según se especifique: crudos o cocidos)
3. Papa, batata y choclo (verduras tipo C): siempre en gramos
4. Frutas: también en gramos
5. Verduras no tipo C: libres, expresadas como volumen coherente (ej: "1 plato de ensalada", "2 tazas de verduras")
6. Incluir preparación detallada de cada comida
7. No usar suplementos si no están indicados
8. Usar léxico argentino (ej: "palta" en lugar de "aguacate", "frutillas" en lugar de "fresas")
9. Calorías calculadas según objetivos específicos del paciente

FORMATO DE PLANES:
- 3 días iguales (no variar entre días)
- 3 opciones equivalentes por comida (±5% en calorías y macros)
- Todas las cantidades en gramos según tipo especificado (crudo/cocido)
- Incluir forma de preparación
- Respetar el método al pie de la letra

IMPORTANTE - RESTRICCIONES ABSOLUTAS:
- SOLO usa las recetas proporcionadas en la base de datos
- NO inventes recetas nuevas bajo NINGUNA circunstancia
- ADVERTENCIA: Cualquier receta no presente en la lista proporcionada será RECHAZADA automáticamente
- Si no encuentras una receta adecuada, usa ÚNICAMENTE las opciones disponibles
- Cada receta DEBE coincidir EXACTAMENTE con el nombre en la lista proporcionada
- Respeta el método Tres Días y Carga estrictamente
- Mantén el léxico argentino en todo momento

VALIDACIÓN:
El sistema validará que TODAS las recetas existan en la base de datos.
Las recetas inventadas serán sustituidas o rechazadas."""

    @staticmethod
    def format_json_response_schema(schema_type: str) -> str:
        """Get JSON schema for structured responses"""
        schemas = {
            "meal_plan": """
FORMATO DE RESPUESTA JSON REQUERIDO:
{
    "plan_name": "Plan Nutricional Personalizado",
    "patient_name": "Nombre del paciente",
    "start_date": "YYYY-MM-DD",
    "total_daily_calories": 2000,
    "days": [
        {
            "day_number": 1,
            "date": "YYYY-MM-DD",
            "meals": {
                "desayuno": {
                    "time": "08:00",
                    "recipe_name": "Nombre de la receta",
                    "ingredients": ["ingrediente 1: cantidad", "ingrediente 2: cantidad"],
                    "preparation": "Instrucciones de preparación",
                    "calories": 500,
                    "nutritional_tips": "Tip nutricional relevante"
                },
                "almuerzo": {...},
                "merienda": {...},
                "cena": {...}
            },
            "daily_totals": {
                "calories": 2000,
                "proteins_g": 100,
                "carbs_g": 250,
                "fats_g": 67
            }
        }
    ],
    "general_recommendations": ["Recomendación 1", "Recomendación 2"],
    "shopping_list": {
        "proteins": ["item: cantidad total"],
        "vegetables": ["item: cantidad total"],
        "fruits": ["item: cantidad total"],
        "grains": ["item: cantidad total"],
        "dairy": ["item: cantidad total"],
        "others": ["item: cantidad total"]
    }
}
""",
            "meal_plan_tres_dias": """
FORMATO DE RESPUESTA JSON REQUERIDO (TRES DÍAS Y CARGA):
{
    "metodo": "Tres Días y Carga | Dieta Inteligente® & Nutrición Evolutiva",
    "patient_name": "Nombre del paciente",
    "objective": "Objetivo del paciente",
    "total_daily_calories": 2000,
    "food_weight_type": "crudo" o "cocido",
    "macros_distribution": {
        "carbohydrates_percent": 45,
        "proteins_percent": 25,
        "fats_percent": 30
    },
    "meal_plan": {
        "desayuno": {
            "time": "08:00",
            "opciones": [
                {
                    "nombre": "Opción 1 - Nombre descriptivo",
                    "ingredientes": [
                        {"alimento": "Avena", "cantidad": "50g", "tipo": "crudo"},
                        {"alimento": "Banana", "cantidad": "100g", "tipo": "crudo"},
                        {"alimento": "Leche descremada", "cantidad": "200ml"}
                    ],
                    "preparacion": "Preparación detallada en argentino...",
                    "calorias": 350,
                    "macros": {
                        "carbohidratos_g": 55,
                        "carbohidratos_kcal": 220,
                        "proteinas_g": 15,
                        "proteinas_kcal": 60,
                        "grasas_g": 8,
                        "grasas_kcal": 72
                    }
                },
                {"nombre": "Opción 2..."},
                {"nombre": "Opción 3..."}
            ]
        },
        "almuerzo": {...},
        "merienda": {...},
        "cena": {...}
    },
    "totales_diarios": {
        "calorias": 2000,
        "proteinas_g": 125,
        "proteinas_kcal": 500,
        "carbohidratos_g": 225,
        "carbohidratos_kcal": 900,
        "grasas_g": 67,
        "grasas_kcal": 600
    },
    "recomendaciones_generales": [
        "Tomar 8-10 vasos de agua por día",
        "Las verduras no tipo C son libres",
        "Respetar los horarios de comida",
        "Este plan se repite idéntico los 3 días"
    ],
    "lista_compras_3_dias": {
        "proteinas": [{"item": "Pollo", "cantidad_total": "900g crudo"}],
        "vegetales": [{"item": "Papa", "cantidad_total": "600g"}],
        "frutas": [{"item": "Manzana", "cantidad_total": "900g"}],
        "cereales": [{"item": "Arroz integral", "cantidad_total": "450g crudo"}],
        "lacteos": [{"item": "Yogur descremado", "cantidad_total": "600g"}],
        "otros": [{"item": "Aceite de oliva", "cantidad_total": "90ml"}]
    }
}
""",
            "adjustment": """
FORMATO DE RESPUESTA JSON PARA AJUSTES:
{
    "adjustment_type": "Tipo de ajuste realizado",
    "reason": "Razón del ajuste",
    "changes_made": [
        "Cambio 1",
        "Cambio 2"
    ],
    "new_daily_calories": 1800,
    "modified_meals": {
        "meal_type": {
            "original": "Receta original",
            "new": "Nueva receta",
            "reason": "Razón del cambio"
        }
    },
    "recommendations": ["Recomendación 1", "Recomendación 2"],
    "next_control_date": "En X días"
}
""",
            "replacement": """
FORMATO DE RESPUESTA JSON PARA REEMPLAZOS:
{
    "original_meal": "Comida original",
    "replacements": [
        {
            "recipe_name": "Nombre de la receta alternativa",
            "reason_selected": "Por qué es una buena alternativa",
            "ingredients": ["ingrediente 1: cantidad"],
            "preparation": "Instrucciones",
            "calories": 300,
            "nutritional_equivalence": "Mantiene el mismo valor calórico y distribución de macros",
            "preparation_time": "20 minutos",
            "tips": "Tips de preparación"
        }
    ],
    "selection_criteria": "Criterios usados para seleccionar las alternativas"
}
"""
        }
        return schemas.get(schema_type, "")

    @staticmethod
    def get_nutritional_method_context() -> str:
        """Get context about the nutritional method"""
        return """
MÉTODO TRES DÍAS Y CARGA | DIETA INTELIGENTE® & NUTRICIÓN EVOLUTIVA

Condiciones generales que SIEMPRE se cumplen:

1. ESTRUCTURA DEL PLAN:
   - Plan de 3 días IGUALES (mismo menú los 3 días)
   - Todas las comidas deben estar en gramos
   - Tipo de peso a usar: según especifique el paciente (crudo o cocido)
   - 3 opciones equivalentes por cada comida (±5% en calorías y macros)

2. MEDICIÓN DE ALIMENTOS:
   - Verduras tipo C (papa, batata y choclo): SIEMPRE en gramos
   - Frutas: SIEMPRE en gramos
   - Proteínas: SIEMPRE en gramos
   - Cereales y legumbres: SIEMPRE en gramos
   - Verduras NO tipo C: libres (porción visual coherente, ej: "1 plato", "2 tazas")

3. CÁLCULO DE CALORÍAS SEGÚN OBJETIVO:
   - Mantenimiento: TDEE (Total Daily Energy Expenditure)
   - Bajar 0,5 kg/semana: TDEE - 500 kcal
   - Bajar 1 kg/semana: TDEE - 1000 kcal
   - Subir 0,5 kg/semana: TDEE + 500 kcal
   - Subir 1 kg/semana: TDEE + 1000 kcal

4. LÉXICO Y PRESENTACIÓN:
   - Usar SIEMPRE léxico argentino
   - Incluir forma de preparación detallada
   - No usar suplementos si no están indicados
   - Especificar horarios sugeridos para cada comida

5. ADAPTACIÓN SEGÚN NIVEL ECONÓMICO:
   - Sin restricciones: variedad completa
   - Medio: ingredientes de supermercado común
   - Limitado: básicos (arroz, huevos, legumbres, vegetales de estación)
   - Bajo recursos: plan social, opciones más económicas
"""