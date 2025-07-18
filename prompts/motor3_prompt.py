"""
Motor 3: Meal Replacement Prompt Template
"""

from typing import Dict, Any, List
from prompts.base_prompt import BasePromptTemplate


class Motor3PromptTemplate(BasePromptTemplate):
    """Prompt template for meal replacements"""
    
    @classmethod
    def generate_replacement_prompt(
        cls,
        replacement_request: Dict[str, Any],
        candidate_recipes: List[Dict[str, Any]],
        original_meal_nutrition: Dict[str, Any] = None
    ) -> str:
        """
        Generate prompt for finding meal replacements
        
        Args:
            replacement_request: Meal replacement request data
            candidate_recipes: Potential replacement recipes from ChromaDB
            original_meal_nutrition: Nutritional info of original meal if available
            
        Returns:
            Complete prompt for GPT-4
        """
        
        patient_data = replacement_request.get('patient_data', {})
        
        prompt = f"""
{cls.get_nutritional_method_context()}

TAREA: Encuentra reemplazos adecuados para la siguiente comida.

INFORMACIÓN DEL PACIENTE:
{cls.format_patient_info(patient_data)}

SOLICITUD DE REEMPLAZO:
- Comida a reemplazar: {replacement_request.get('meal_to_replace', 'No especificada')}
- Tipo de comida: {replacement_request.get('meal_type', 'No especificado')}
- Razón del reemplazo: {replacement_request.get('reason', 'No especificada')}
- Mantener calorías: {'Sí' if replacement_request.get('maintain_calories', True) else 'No'}

RESTRICCIONES Y PREFERENCIAS:
{cls._format_replacement_constraints(replacement_request)}

{cls._format_original_meal_info(original_meal_nutrition)}

RECETAS CANDIDATAS DISPONIBLES:
{cls.format_recipes_list(candidate_recipes)}

INSTRUCCIONES PARA SELECCIÓN:

1. CRITERIOS DE SELECCIÓN:
   - PRIORIDAD 1: Seguridad (evitar alergias y contraindicaciones)
   - PRIORIDAD 2: Equivalencia nutricional (si se requiere mantener calorías)
   - PRIORIDAD 3: Satisfacción del motivo de reemplazo
   - PRIORIDAD 4: Preferencias y gustos del paciente
   - PRIORIDAD 5: Facilidad de preparación

2. ANÁLISIS NUTRICIONAL:
{cls._generate_nutritional_matching_criteria(replacement_request, original_meal_nutrition)}

3. CONSIDERACIONES ESPECÍFICAS:
{cls._generate_specific_considerations(replacement_request)}

4. EVALUACIÓN DE OPCIONES:
   - Analiza cada receta candidata según los criterios
   - Calcula la equivalencia nutricional
   - Considera el contexto del día completo
   - Verifica disponibilidad según nivel económico

5. PRESENTACIÓN DE ALTERNATIVAS:
   - Ofrece 3-5 opciones ordenadas por idoneidad
   - Explica por qué cada opción es apropiada
   - Incluye modificaciones sugeridas si es necesario
   - Proporciona tips de preparación específicos

{cls.format_json_response_schema('replacement')}

NOTAS IMPORTANTES:
- Si ninguna receta cumple los criterios mínimos, indícalo claramente
- Puedes sugerir modificaciones menores a las recetas para mejor ajuste
- Considera el horario y contexto de la comida
- Mantén un tono empático y comprensivo con las necesidades del paciente

Genera las opciones de reemplazo en formato JSON.
"""
        
        return prompt
    
    @staticmethod
    def _format_replacement_constraints(replacement_request: Dict[str, Any]) -> str:
        """Format constraints for replacement"""
        constraints = []
        
        # Add allergies as absolute constraints
        patient_data = replacement_request.get('patient_data', {})
        allergies = patient_data.get('allergies', [])
        if allergies:
            constraints.append(f"- EVITAR ABSOLUTAMENTE: {', '.join(allergies)} (alergias)")
        
        # Add ingredients to avoid
        avoid = replacement_request.get('avoid_ingredients', [])
        if avoid:
            constraints.append(f"- Evitar ingredientes: {', '.join(avoid)}")
        
        # Add alternative ingredients preference
        alternatives = replacement_request.get('alternative_ingredients', [])
        if alternatives:
            constraints.append(f"- Preferir ingredientes: {', '.join(alternatives)}")
        
        # Add medical conditions constraints
        pathologies = patient_data.get('pathologies', [])
        if pathologies:
            constraints.append(f"- Considerar patologías: {', '.join(pathologies)}")
        
        # Add preparation constraints based on reason
        reason = replacement_request.get('reason', '').lower()
        if 'tiempo' in reason or 'rápido' in reason:
            constraints.append("- Preferir opciones de preparación rápida (< 20 minutos)")
        if 'difícil' in reason or 'complicado' in reason:
            constraints.append("- Preferir opciones de preparación simple")
        
        if not constraints:
            constraints.append("- No hay restricciones específicas adicionales")
        
        return '\n'.join(constraints)
    
    @staticmethod
    def _format_original_meal_info(original_meal_nutrition: Dict[str, Any]) -> str:
        """Format original meal nutritional information"""
        if not original_meal_nutrition:
            return """
INFORMACIÓN NUTRICIONAL ORIGINAL:
- No se proporcionó información específica de la comida original
- Usar criterios generales según el tipo de comida
"""
        
        return f"""
INFORMACIÓN NUTRICIONAL ORIGINAL:
- Calorías: {original_meal_nutrition.get('calories', 'No especificado')} kcal
- Proteínas: {original_meal_nutrition.get('proteins', 'No especificado')} g
- Carbohidratos: {original_meal_nutrition.get('carbs', 'No especificado')} g
- Grasas: {original_meal_nutrition.get('fats', 'No especificado')} g
- Fibra: {original_meal_nutrition.get('fiber', 'No especificado')} g
"""
    
    @staticmethod
    def _generate_nutritional_matching_criteria(
        replacement_request: Dict[str, Any],
        original_meal_nutrition: Dict[str, Any]
    ) -> str:
        """Generate criteria for nutritional matching"""
        
        if replacement_request.get('maintain_calories', True) and original_meal_nutrition:
            original_cal = original_meal_nutrition.get('calories', 0)
            return f"""
   - Busca opciones con calorías similares (±10%): {original_cal * 0.9:.0f}-{original_cal * 1.1:.0f} kcal
   - Mantén proporción similar de macronutrientes
   - Prioriza opciones con valor nutricional equivalente o superior
   - Considera la densidad de nutrientes, no solo calorías
"""
        
        meal_type = replacement_request.get('meal_type', '').lower()
        meal_type_criteria = {
            'desayuno': """
   - Rango calórico típico: 300-500 kcal
   - Incluir proteínas para saciedad matutina
   - Preferir carbohidratos complejos
   - Incluir una porción de lácteos si es posible
""",
            'almuerzo': """
   - Rango calórico típico: 500-700 kcal
   - Balance entre proteínas, carbohidratos y vegetales
   - Incluir al menos 2 grupos de alimentos
   - Asegurar saciedad para la tarde
""",
            'cena': """
   - Rango calórico típico: 400-600 kcal
   - Preferir proteínas magras y vegetales
   - Limitar carbohidratos pesados
   - Opciones de fácil digestión
""",
            'merienda': """
   - Rango calórico típico: 150-300 kcal
   - Combinar proteínas y carbohidratos
   - Porciones moderadas
   - Fácil de preparar y transportar
""",
            'colacion': """
   - Rango calórico típico: 100-200 kcal
   - Opciones prácticas y portables
   - Preferir opciones saciantes
   - Evitar azúcares simples
"""
        }
        
        return meal_type_criteria.get(meal_type, """
   - Usar criterios generales de balance nutricional
   - Considerar el contexto del plan diario
   - Mantener coherencia con objetivos del paciente
""")
    
    @staticmethod
    def _generate_specific_considerations(replacement_request: Dict[str, Any]) -> str:
        """Generate specific considerations based on replacement reason"""
        reason = replacement_request.get('reason', '').lower()
        patient_data = replacement_request.get('patient_data', {})
        
        considerations = []
        
        # Reason-based considerations
        if 'monotonía' in reason or 'aburrido' in reason or 'variedad' in reason:
            considerations.append("- Prioriza opciones con sabores y texturas diferentes")
            considerations.append("- Busca recetas de categorías distintas a las habituales")
            considerations.append("- Sugiere preparaciones novedosas pero accesibles")
        
        if 'no gusta' in reason or 'disgusto' in reason:
            considerations.append("- Evita ingredientes similares a la comida rechazada")
            considerations.append("- Ofrece alternativas con perfiles de sabor diferentes")
            considerations.append("- Considera texturas y presentaciones alternativas")
        
        if 'tiempo' in reason or 'rápido' in reason:
            considerations.append("- Prioriza recetas de 15-20 minutos máximo")
            considerations.append("- Sugiere opciones que se pueden preparar con anticipación")
            considerations.append("- Incluye tips para agilizar la preparación")
        
        if 'ingrediente' in reason or 'alergia' in reason:
            considerations.append("- Verifica cuidadosamente todos los ingredientes")
            considerations.append("- Considera contaminación cruzada si es relevante")
            considerations.append("- Ofrece alternativas seguras y confiables")
        
        # Medical considerations
        pathologies = patient_data.get('pathologies', [])
        for pathology in pathologies:
            if 'diabetes' in pathology.lower():
                considerations.append("- Prioriza opciones de bajo índice glucémico")
            if 'hipertension' in pathology.lower():
                considerations.append("- Selecciona opciones bajas en sodio")
            if 'celiac' in pathology.lower() or 'celiaco' in pathology.lower():
                considerations.append("- Asegura opciones 100% libres de gluten")
        
        if not considerations:
            considerations.append("- Aplica criterios generales de nutrición saludable")
            considerations.append("- Mantén el balance del plan general")
        
        return '\n'.join(considerations)
    
    @classmethod
    def generate_quick_swap_prompt(
        cls,
        food_category: str,
        dietary_restrictions: List[str],
        calorie_range: tuple
    ) -> str:
        """Generate a quick prompt for simple food swaps"""
        
        return f"""
Proporciona 5 alternativas rápidas para la categoría: {food_category}

Restricciones: {', '.join(dietary_restrictions) if dietary_restrictions else 'Ninguna'}
Rango calórico: {calorie_range[0]}-{calorie_range[1]} kcal

Lista las opciones con:
- Nombre del alimento/preparación
- Calorías
- Porción
- Preparación básica si aplica
"""
    
    @classmethod
    def generate_emergency_replacement_prompt(cls, meal_type: str, available_ingredients: List[str]) -> str:
        """Generate prompt for emergency replacements with limited ingredients"""
        
        return f"""
Crea una opción de {meal_type} de emergencia con estos ingredientes disponibles:
{', '.join(available_ingredients)}

Proporciona:
1. Receta rápida (< 15 minutos)
2. Instrucciones paso a paso
3. Información nutricional aproximada
4. Tips para mejorar el sabor/presentación
"""