"""
Motor 1: New Patient Plan Generation Prompt Template
"""

from typing import Dict, Any, List
from prompts.base_prompt import BasePromptTemplate


class Motor1PromptTemplate(BasePromptTemplate):
    """Prompt template for generating new nutrition plans"""
    
    @classmethod
    def generate_plan_prompt(
        cls,
        patient_data: Dict[str, Any],
        available_recipes: List[Dict[str, Any]],
        nutritional_requirements: Dict[str, Any]
    ) -> str:
        """
        Generate the complete prompt for creating a new nutrition plan
        
        Args:
            patient_data: Patient information
            available_recipes: Recipes retrieved from ChromaDB
            nutritional_requirements: Calculated nutritional needs
            
        Returns:
            Complete prompt for GPT-4
        """
        
        prompt = f"""
{cls.get_nutritional_method_context()}

TAREA: Genera un plan nutricional completo y personalizado para el siguiente paciente.

{cls.format_patient_info(patient_data)}

{cls.format_nutritional_requirements(nutritional_requirements)}

{cls.format_meal_distribution(
    patient_data.get('meals_per_day', 4),
    nutritional_requirements.get('daily_calories', 2000),
    nutritional_requirements.get('carbs_percentage', 45) / 100,
    nutritional_requirements.get('protein_percentage', 25) / 100,
    nutritional_requirements.get('fat_percentage', 30) / 100,
    patient_data.get('distribution_type', 'traditional')
)}

{cls.format_recipes_list(available_recipes)}

INSTRUCCIONES ESPECÍFICAS:

1. SELECCIÓN DE RECETAS - CRÍTICO:
   ⚠️ ADVERTENCIA: SOLO puedes usar las recetas EXACTAS de la lista proporcionada
   - Usa ÚNICAMENTE las recetas proporcionadas en la lista - NO INVENTES NUEVAS
   - Los nombres de las recetas deben coincidir EXACTAMENTE con los de la lista
   - Si necesitas una receta y no está en la lista, elige la más similar disponible
   - Varía las recetas durante los {patient_data.get('days_requested', 7)} días
   - No repitas la misma receta más de 2 veces por semana
   - Considera el nivel económico "{patient_data.get('economic_level', 'standard')}"
   - NUNCA crees recetas que no estén en la lista proporcionada

2. BALANCE NUTRICIONAL:
   - Asegura que cada día cumpla con las calorías objetivo (±5%)
   - Mantén la distribución de macronutrientes especificada EXACTAMENTE
   - IMPORTANTE: Cada comida debe respetar la distribución de macros indicada arriba
   - CRÍTICO: Respeta el tipo de distribución seleccionado:
     * DISTRIBUCIÓN EQUITATIVA: Todas las comidas tienen EXACTAMENTE las mismas calorías y macros
     * DISTRIBUCIÓN TRADICIONAL: Sigue los porcentajes variables indicados
   - Para cada comida, calcula los gramos de cada macro según su porcentaje calórico
   - Si el paciente tiene nivel de proteína personalizado, respétalo estrictamente
   - Incluye todos los grupos de alimentos diariamente
   - Verifica que los macros sumen 100% y respeten las especificaciones
   - Los porcentajes de macros son del total calórico diario
   - Cada comida debe incluir gramos específicos de proteína, carbohidratos y grasas

3. CONSIDERACIONES MÉDICAS:
{cls._format_medical_considerations(patient_data)}

4. PREFERENCIAS Y RESTRICCIONES:
{cls._format_preferences_restrictions(patient_data)}

5. PREPARACIÓN Y PRESENTACIÓN:
   - Proporciona instrucciones claras de preparación
   - Especifica cantidades exactas en gramos o unidades
   - Incluye tips nutricionales relevantes para cada comida
   - Sugiere horarios apropiados para cada comida
   - Para cada comida, incluye SIEMPRE:
     * Gramos de carbohidratos y sus kcal (1g = 4 kcal)
     * Gramos de proteínas y sus kcal (1g = 4 kcal)
     * Gramos de grasas y sus kcal (1g = 9 kcal)

6. LISTA DE COMPRAS:
   - Genera una lista de compras consolidada para toda la semana
   - Agrupa por categorías (proteínas, vegetales, frutas, etc.)
   - Especifica cantidades totales necesarias

{cls.format_json_response_schema('meal_plan_tres_dias')}

RECUERDA:
- Sé específico con las cantidades y preparaciones
- Ofrece variedad manteniendo el equilibrio nutricional
- Adapta las recomendaciones al estilo de vida del paciente
- Incluye consejos prácticos para mejorar la adherencia al plan

Genera el plan nutricional completo en formato JSON.
"""
        
        return prompt
    
    @staticmethod
    def _format_medical_considerations(patient_data: Dict[str, Any]) -> str:
        """Format medical considerations based on pathologies"""
        pathologies = patient_data.get('pathologies', [])
        
        if not pathologies:
            return "   - No hay patologías reportadas. Enfócate en un plan equilibrado y preventivo."
        
        considerations = []
        
        # Map pathologies to specific dietary considerations
        pathology_guidelines = {
            "diabetes": [
                "Controla el índice glucémico de las comidas",
                "Distribuye los carbohidratos uniformemente durante el día",
                "Evita azúcares simples y prefiere carbohidratos complejos",
                "Incluye fibra en cada comida"
            ],
            "hipertension": [
                "Limita el sodio a menos de 2000mg/día",
                "Aumenta el consumo de potasio (frutas y vegetales)",
                "Evita alimentos procesados y embutidos",
                "Prefiere preparaciones al vapor o asadas"
            ],
            "colesterol": [
                "Limita las grasas saturadas",
                "Aumenta el consumo de omega-3",
                "Incluye fibra soluble (avena, legumbres)",
                "Evita frituras y grasas trans"
            ],
            "sobrepeso": [
                "Crea un déficit calórico moderado (500 kcal/día)",
                "Aumenta la proporción de proteínas para mayor saciedad",
                "Incluye volumen con vegetales bajos en calorías",
                "Distribuye las comidas para evitar largos períodos de ayuno"
            ],
            "obesidad": [
                "Crea un déficit calórico de 500-750 kcal/día",
                "Prioriza proteínas magras y vegetales",
                "Limita carbohidratos simples",
                "Enfócate en la reeducación alimentaria"
            ]
        }
        
        for pathology in pathologies:
            pathology_lower = pathology.lower()
            for condition, guidelines in pathology_guidelines.items():
                if condition in pathology_lower:
                    considerations.extend(guidelines)
        
        if considerations:
            return "   - " + "\n   - ".join(set(considerations))  # Remove duplicates
        else:
            return f"   - Considera las siguientes patologías: {', '.join(pathologies)}"
    
    @staticmethod
    def _format_preferences_restrictions(patient_data: Dict[str, Any]) -> str:
        """Format food preferences and restrictions"""
        allergies = patient_data.get('allergies', [])
        preferences = patient_data.get('food_preferences', [])
        dislikes = patient_data.get('food_dislikes', [])
        
        text = ""
        
        if allergies:
            text += f"   - ALERGIAS (EVITAR COMPLETAMENTE): {', '.join(allergies)}\n"
        
        if dislikes:
            text += f"   - No le gustan (evitar si es posible): {', '.join(dislikes)}\n"
        
        if preferences:
            text += f"   - Preferencias (incluir cuando sea posible): {', '.join(preferences)}\n"
        
        if not (allergies or preferences or dislikes):
            text = "   - No hay restricciones alimentarias específicas\n"
        
        return text.rstrip()
    
    @classmethod
    def generate_recipe_search_queries(cls, patient_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Generate search queries for finding appropriate recipes
        
        Returns:
            Dictionary with meal types and their search queries
        """
        queries = {
            "desayuno": [],
            "almuerzo": [],
            "cena": [],
            "merienda": [],
            "colacion": []
        }
        
        # Base queries by meal type
        base_queries = {
            "desayuno": ["desayuno saludable", "desayuno proteico", "desayuno fibra"],
            "almuerzo": ["almuerzo balanceado", "almuerzo proteína vegetales", "plato principal"],
            "cena": ["cena ligera", "cena digestiva", "cena proteína"],
            "merienda": ["merienda saludable", "snack nutritivo", "colación tarde"],
            "colacion": ["colación", "snack bajo calorías", "entre comidas"]
        }
        
        # Add pathology-specific queries
        pathologies = patient_data.get('pathologies', [])
        for pathology in pathologies:
            pathology_lower = pathology.lower()
            if "diabetes" in pathology_lower:
                for meal_type in queries:
                    queries[meal_type].append("bajo índice glucémico")
            if "hipertension" in pathology_lower:
                for meal_type in queries:
                    queries[meal_type].append("bajo sodio")
            if "colesterol" in pathology_lower:
                for meal_type in queries:
                    queries[meal_type].append("bajo grasa saturada")
        
        # Add preference-based queries
        preferences = patient_data.get('food_preferences', [])
        for preference in preferences:
            if "vegetariano" in preference.lower():
                for meal_type in queries:
                    queries[meal_type].append("vegetariano")
        
        # Combine with base queries
        for meal_type, base in base_queries.items():
            queries[meal_type] = base + queries[meal_type]
        
        return queries
    
    @classmethod
    def generate_validation_prompt(cls, generated_plan: Dict[str, Any], patient_data: Dict[str, Any]) -> str:
        """Generate a prompt to validate the generated plan"""
        return f"""
Valida el siguiente plan nutricional generado:

PLAN GENERADO:
{generated_plan}

CRITERIOS DE VALIDACIÓN:
1. ¿Cumple con las calorías diarias objetivo (±5%)?
2. ¿Respeta la distribución de macronutrientes?
3. ¿Evita todos los alimentos con alergias reportadas?
4. ¿Incluye variedad en las recetas?
5. ¿Es apropiado para las patologías del paciente?
6. ¿Las cantidades son realistas y precisas?
7. ¿Las instrucciones de preparación son claras?

Si encuentras algún problema, indica qué debe corregirse.
"""