"""
Base Prompt Template and Utilities
"""

from typing import Dict, Any, List
import json


class BasePromptTemplate:
    """Base class for all prompt templates"""
    
    @staticmethod
    def format_patient_info(patient_data: Dict[str, Any]) -> str:
        """Format patient information for prompts"""
        return f"""
INFORMACIÓN DEL PACIENTE:
- Nombre: {patient_data.get('name', 'No especificado')}
- Edad: {patient_data.get('age', 'No especificado')} años
- Género: {patient_data.get('gender', 'No especificado')}
- Altura: {patient_data.get('height', 'No especificado')} cm
- Peso: {patient_data.get('weight', 'No especificado')} kg
- IMC: {patient_data.get('bmi', 'No calculado')} ({patient_data.get('bmi_category', 'No categorizado')})
- Nivel de actividad: {patient_data.get('activity_level', 'No especificado')}
- Nivel económico: {patient_data.get('economic_level', 'standard')}

CONDICIONES MÉDICAS:
- Patologías: {', '.join(patient_data.get('pathologies', [])) or 'Ninguna'}
- Alergias: {', '.join(patient_data.get('allergies', [])) or 'Ninguna'}
- Preferencias alimentarias: {', '.join(patient_data.get('food_preferences', [])) or 'Ninguna'}
- Alimentos que no le gustan: {', '.join(patient_data.get('food_dislikes', [])) or 'Ninguno'}

PLAN SOLICITADO:
- Comidas por día: {patient_data.get('meals_per_day', 4)}
- Días solicitados: {patient_data.get('days_requested', 7)}
- Observaciones: {patient_data.get('observations', 'Ninguna')}
"""

    @staticmethod
    def format_recipes_list(recipes: List[Dict[str, Any]]) -> str:
        """Format recipes list for prompts"""
        if not recipes:
            return "No se encontraron recetas disponibles."
        
        recipes_text = "RECETAS DISPONIBLES:\n\n"
        for i, recipe in enumerate(recipes, 1):
            recipes_text += f"{i}. {recipe.get('metadata', {}).get('recipe_name', 'Sin nombre')}\n"
            recipes_text += f"   Categoría: {recipe.get('metadata', {}).get('category', 'Sin categoría')}\n"
            recipes_text += f"   Contenido: {recipe.get('content', '')[:200]}...\n\n"
        
        return recipes_text

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
    def format_meal_distribution(meals_per_day: int) -> str:
        """Format meal distribution throughout the day"""
        distributions = {
            3: """
DISTRIBUCIÓN DE COMIDAS (3 comidas/día):
- Desayuno: 30% de las calorías diarias (7:00-9:00)
- Almuerzo: 40% de las calorías diarias (13:00-14:00)
- Cena: 30% de las calorías diarias (20:00-21:00)
""",
            4: """
DISTRIBUCIÓN DE COMIDAS (4 comidas/día):
- Desayuno: 25% de las calorías diarias (7:00-9:00)
- Almuerzo: 35% de las calorías diarias (13:00-14:00)
- Merienda: 15% de las calorías diarias (17:00-18:00)
- Cena: 25% de las calorías diarias (20:00-21:00)
""",
            5: """
DISTRIBUCIÓN DE COMIDAS (5 comidas/día):
- Desayuno: 20% de las calorías diarias (7:00-9:00)
- Colación AM: 10% de las calorías diarias (10:30-11:00)
- Almuerzo: 35% de las calorías diarias (13:00-14:00)
- Merienda: 15% de las calorías diarias (17:00-18:00)
- Cena: 20% de las calorías diarias (20:00-21:00)
""",
            6: """
DISTRIBUCIÓN DE COMIDAS (6 comidas/día):
- Desayuno: 20% de las calorías diarias (7:00-9:00)
- Colación AM: 10% de las calorías diarias (10:30-11:00)
- Almuerzo: 30% de las calorías diarias (13:00-14:00)
- Merienda: 10% de las calorías diarias (16:00-17:00)
- Cena: 20% de las calorías diarias (20:00-21:00)
- Colación PM: 10% de las calorías diarias (22:00)
"""
        }
        return distributions.get(meals_per_day, distributions[4])

    @staticmethod
    def get_system_prompt() -> str:
        """Get the system prompt for the nutritionist role"""
        return """Eres una nutricionista profesional especializada en crear planes de alimentación personalizados. Tu enfoque se basa en:

1. MÉTODO NUTRICIONAL: Utilizas un sistema de intercambios y equivalencias calóricas para garantizar flexibilidad y adherencia al plan.

2. PRINCIPIOS FUNDAMENTALES:
   - Equilibrio nutricional basado en las necesidades individuales
   - Variedad en las opciones de alimentos
   - Respeto por las preferencias y restricciones del paciente
   - Adaptación al nivel económico
   - Educación nutricional implícita en cada recomendación

3. FORMATO DE RESPUESTA:
   - Utiliza un lenguaje claro y profesional pero cercano
   - Proporciona instrucciones precisas de preparación
   - Incluye tips nutricionales relevantes
   - Especifica cantidades exactas en gramos o unidades
   - Ofrece alternativas cuando sea apropiado

4. CONSIDERACIONES MÉDICAS:
   - Siempre ten en cuenta las patologías reportadas
   - Adapta las recomendaciones según las condiciones de salud
   - Prioriza la seguridad alimentaria

5. IMPORTANTE:
   - SOLO usa las recetas proporcionadas en la base de datos
   - NO inventes recetas nuevas
   - Respeta las cantidades y preparaciones indicadas
   - Mantén la coherencia con el método nutricional establecido"""

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
CONTEXTO DEL MÉTODO NUTRICIONAL:

Este método se basa en el sistema de intercambios y equivalencias, donde:

1. GRUPOS DE ALIMENTOS Y SUS EQUIVALENCIAS CALÓRICAS:
   - Lácteos: 80 kcal por porción
   - Frutas: 60 kcal por porción
   - Cereales: 80 kcal por porción
   - Proteínas: 75 kcal por porción
   - Grasas: 45 kcal por porción
   - Vegetales: 25 kcal por porción

2. FLEXIBILIDAD:
   - Los alimentos dentro de cada grupo son intercambiables
   - Se respetan las porciones equivalentes
   - Se permite adaptación según disponibilidad y preferencias

3. PRINCIPIOS DE COMBINACIÓN:
   - Cada comida debe incluir al menos 3 grupos de alimentos
   - El desayuno y merienda deben incluir lácteos
   - Almuerzo y cena deben incluir proteínas y vegetales
   - Los cereales se distribuyen a lo largo del día

4. HIDRATACIÓN:
   - Recomendar 8-10 vasos de agua al día
   - Evitar bebidas azucaradas
   - Infusiones permitidas sin azúcar

5. CONDIMENTOS Y PREPARACIÓN:
   - Preferir métodos de cocción saludables (vapor, horno, plancha)
   - Usar condimentos naturales y hierbas
   - Limitar el uso de sal
   - Aceite con moderación según el plan
"""