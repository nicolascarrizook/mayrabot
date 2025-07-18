"""
Motor 2: Control/Follow-up Adjustments Prompt Template
"""

from typing import Dict, Any, List
from prompts.base_prompt import BasePromptTemplate


class Motor2PromptTemplate(BasePromptTemplate):
    """Prompt template for adjusting existing nutrition plans"""
    
    @classmethod
    def generate_adjustment_prompt(
        cls,
        control_data: Dict[str, Any],
        progress_analysis: Dict[str, Any],
        current_plan: Dict[str, Any],
        available_recipes: List[Dict[str, Any]]
    ) -> str:
        """
        Generate prompt for plan adjustments based on progress
        
        Args:
            control_data: Control consultation data
            progress_analysis: Analysis of patient progress
            current_plan: Current nutrition plan
            available_recipes: Alternative recipes from ChromaDB
            
        Returns:
            Complete prompt for GPT-4
        """
        
        prompt = f"""
{cls.get_nutritional_method_context()}

TAREA: Ajusta el plan nutricional existente basándote en el progreso y necesidades del paciente.

INFORMACIÓN DEL PACIENTE ORIGINAL:
{cls.format_patient_info(control_data['patient_data'])}

DATOS DE CONTROL Y SEGUIMIENTO:
{cls._format_control_data(control_data)}

ANÁLISIS DE PROGRESO:
{cls._format_progress_analysis(progress_analysis)}

PLAN ACTUAL (RESUMEN):
{cls._format_current_plan_summary(current_plan)}

PROBLEMAS REPORTADOS:
{cls._format_reported_issues(control_data)}

CAMBIOS SOLICITADOS:
{cls._format_requested_changes(control_data)}

{cls.format_recipes_list(available_recipes)}

INSTRUCCIONES PARA EL AJUSTE:

1. ANÁLISIS DE LA SITUACIÓN:
   - Evalúa el progreso del paciente
   - Identifica las áreas que requieren modificación
   - Considera la adherencia y satisfacción del paciente

2. AJUSTES CALÓRICOS:
{cls._generate_caloric_adjustment_guidelines(progress_analysis)}

3. MODIFICACIONES ESPECÍFICAS:
{cls._generate_specific_modifications(control_data, progress_analysis)}

4. REEMPLAZOS DE COMIDAS:
   - Reemplaza las comidas problemáticas con alternativas de la lista
   - Mantén el balance nutricional general
   - Considera las nuevas preferencias o restricciones

5. RECOMENDACIONES ADICIONALES:
   - Proporciona estrategias para mejorar la adherencia
   - Sugiere modificaciones en los horarios si es necesario
   - Incluye tips para superar los obstáculos reportados

6. SEGUIMIENTO:
   - Indica cuándo debe ser el próximo control
   - Especifica qué aspectos monitorear especialmente
   - Sugiere ajustes preventivos si es necesario

{cls.format_json_response_schema('adjustment')}

CONSIDERACIONES IMPORTANTES:
- Mantén los cambios moderados y progresivos
- No hagas modificaciones drásticas a menos que sea médicamente necesario
- Refuerza los aspectos positivos del progreso
- Sé empático con las dificultades reportadas
- Ofrece soluciones prácticas y realistas

Genera los ajustes del plan en formato JSON.
"""
        
        return prompt
    
    @staticmethod
    def _format_control_data(control_data: Dict[str, Any]) -> str:
        """Format control consultation data"""
        return f"""
- Peso actual: {control_data.get('current_weight', 'No especificado')} kg
- Peso inicial: {control_data['patient_data'].get('weight', 'No especificado')} kg
- Cambio de peso: {control_data.get('weight_change', 0)} kg ({control_data.get('weight_change_percentage', 0)}%)
- Días en el plan: {control_data.get('days_on_plan', 'No especificado')}
- Adherencia reportada: {control_data.get('adherence_percentage', 'No especificado')}%
- Nuevas patologías: {', '.join(control_data.get('new_pathologies', [])) or 'Ninguna'}
- Nuevos medicamentos: {', '.join(control_data.get('new_medications', [])) or 'Ninguno'}
"""
    
    @staticmethod
    def _format_progress_analysis(progress_analysis: Dict[str, Any]) -> str:
        """Format progress analysis results"""
        return f"""
- Estado del progreso: {progress_analysis.get('progress_status', 'No determinado')}
- Mensaje de estado: {progress_analysis.get('status_message', 'Sin mensaje')}
- Cambio de peso semanal: {progress_analysis.get('weight_change_per_week', 0)} kg/semana
- Estado de adherencia: {progress_analysis.get('adherence_status', 'No determinado')}
- IMC actual: {progress_analysis.get('current_bmi', 'No calculado')}
- Problemas reportados: {'Sí' if progress_analysis.get('issues_reported') else 'No'}
- Cambios solicitados: {'Sí' if progress_analysis.get('changes_requested') else 'No'}
"""
    
    @staticmethod
    def _format_current_plan_summary(current_plan: Dict[str, Any]) -> str:
        """Format summary of current plan"""
        if not current_plan:
            return "- No se proporcionó el plan actual"
        
        return f"""
- Calorías diarias actuales: {current_plan.get('daily_calories', 'No especificado')} kcal
- Comidas por día: {current_plan.get('meals_per_day', 'No especificado')}
- Distribución de macros: Carbs {current_plan.get('carbs_percentage', 'N/A')}%, 
  Proteínas {current_plan.get('protein_percentage', 'N/A')}%, 
  Grasas {current_plan.get('fat_percentage', 'N/A')}%
"""
    
    @staticmethod
    def _format_reported_issues(control_data: Dict[str, Any]) -> str:
        """Format reported issues"""
        issues = control_data.get('reported_issues', [])
        if not issues:
            return "- No se reportaron problemas específicos"
        
        formatted_issues = "\n".join([f"- {issue}" for issue in issues])
        return formatted_issues
    
    @staticmethod
    def _format_requested_changes(control_data: Dict[str, Any]) -> str:
        """Format requested changes"""
        changes = control_data.get('requested_changes', [])
        if not changes:
            return "- No se solicitaron cambios específicos"
        
        formatted_changes = "\n".join([f"- {change}" for change in changes])
        return formatted_changes
    
    @staticmethod
    def _generate_caloric_adjustment_guidelines(progress_analysis: Dict[str, Any]) -> str:
        """Generate guidelines for caloric adjustments based on progress"""
        progress_status = progress_analysis.get('progress_status', '')
        
        guidelines = {
            'rapid_loss': """
   - AUMENTA las calorías diarias en 200-300 kcal
   - Distribuye el aumento principalmente en proteínas y grasas saludables
   - Añade colaciones nutritivas entre comidas
   - Evita que la pérdida sea mayor a 0.5-1 kg por semana
""",
            'good_loss': """
   - MANTÉN las calorías actuales, el progreso es adecuado
   - Puedes hacer ajustes menores según preferencias
   - Continúa con el mismo enfoque nutricional
   - Refuerza los hábitos positivos establecidos
""",
            'slow_loss': """
   - REDUCE las calorías diarias en 100-200 kcal
   - Revisa las porciones y métodos de preparación
   - Aumenta la proporción de vegetales sin almidón
   - Verifica la precisión en el seguimiento del plan
""",
            'stable': """
   - EVALÚA el objetivo: ¿mantenimiento o pérdida?
   - Si busca pérdida: reduce 200-300 kcal
   - Si busca mantenimiento: plan actual es apropiado
   - Considera aumentar la actividad física
""",
            'moderate_gain': """
   - REDUCE las calorías diarias en 200-250 kcal
   - Revisa posibles excesos o desviaciones del plan
   - Enfócate en alimentos de mayor volumen y menor densidad calórica
   - Evalúa factores externos (estrés, sueño, hidratación)
""",
            'rapid_gain': """
   - REDUCE las calorías diarias en 300-400 kcal
   - Realiza una revisión completa del plan
   - Elimina temporalmente alimentos de alta densidad calórica
   - Considera factores médicos o medicamentos
"""
        }
        
        return guidelines.get(progress_status, """
   - Realiza ajustes moderados según el análisis
   - Prioriza la adherencia y sostenibilidad
   - Consulta con el equipo médico si es necesario
""")
    
    @staticmethod
    def _generate_specific_modifications(control_data: Dict[str, Any], progress_analysis: Dict[str, Any]) -> str:
        """Generate specific modifications based on reported issues"""
        modifications = []
        
        issues_text = ' '.join(control_data.get('reported_issues', [])).lower()
        
        if 'hambre' in issues_text or 'hunger' in issues_text:
            modifications.append("- Aumenta el contenido de fibra y proteína en las comidas")
            modifications.append("- Añade vegetales de libre consumo para mayor volumen")
            modifications.append("- Distribuye las calorías en más comidas durante el día")
        
        if 'cansancio' in issues_text or 'fatiga' in issues_text:
            modifications.append("- Asegura adecuado aporte de hierro y vitaminas B")
            modifications.append("- Revisa la distribución de carbohidratos durante el día")
            modifications.append("- Incluye snacks energéticos pre/post actividad")
        
        if 'ansiedad' in issues_text:
            modifications.append("- Incluye alimentos ricos en triptófano y magnesio")
            modifications.append("- Establece horarios regulares de comida")
            modifications.append("- Añade técnicas de mindful eating")
        
        if 'digestivo' in issues_text or 'estomago' in issues_text:
            modifications.append("- Reduce el tamaño de las porciones principales")
            modifications.append("- Aumenta la frecuencia de comidas pequeñas")
            modifications.append("- Evita alimentos que generen gases o irritación")
        
        if not modifications:
            modifications.append("- Ajusta según las necesidades específicas reportadas")
            modifications.append("- Mantén flexibilidad para mejorar adherencia")
        
        return '\n'.join(modifications)
    
    @classmethod
    def generate_encouragement_message(cls, progress_analysis: Dict[str, Any]) -> str:
        """Generate an encouraging message based on progress"""
        adherence_status = progress_analysis.get('adherence_status', 'unknown')
        progress_status = progress_analysis.get('progress_status', 'unknown')
        
        messages = {
            'excellent': "¡Excelente trabajo! Tu dedicación está dando resultados. Continúa así.",
            'good': "Vas muy bien. Tu esfuerzo se nota en los resultados.",
            'moderate': "Estás avanzando. Algunos ajustes te ayudarán a mejorar aún más.",
            'poor': "Entiendo que puede ser desafiante. Estos ajustes harán el plan más llevadero."
        }
        
        base_message = messages.get(adherence_status, "Sigamos trabajando juntos en tu salud.")
        
        if progress_status == 'good_loss':
            base_message += " La pérdida de peso es saludable y sostenible."
        elif progress_status == 'stable':
            base_message += " La estabilidad puede ser positiva, evaluemos tus objetivos."
        
        return base_message