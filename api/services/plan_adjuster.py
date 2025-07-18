"""
Plan Adjuster Service - Adjusts existing nutrition plans
"""

import logging
from typing import Dict, Any, List
from dataclasses import dataclass

from api.models.patient import ControlData
from api.services.chromadb_service import ChromaDBService
from api.services.openai_service import OpenAIService
from api.services.plan_generator import NutritionPlan
from prompts.motor2_prompt import Motor2PromptTemplate

logger = logging.getLogger(__name__)


class PlanAdjusterService:
    """Service for adjusting existing nutrition plans"""
    
    def __init__(self, chromadb_service: ChromaDBService):
        self.chromadb = chromadb_service
        self.openai = OpenAIService()
    
    async def adjust_plan(
        self,
        control_data: ControlData,
        progress_analysis: Dict[str, Any]
    ) -> NutritionPlan:
        """
        Adjust an existing nutrition plan based on progress
        
        Args:
            control_data: Control consultation data
            progress_analysis: Analysis of patient progress
            
        Returns:
            Adjusted nutrition plan
        """
        logger.info(f"Adjusting plan for {control_data.patient_data.name}")
        
        # Determine necessary adjustments
        adjustments = self._determine_adjustments(control_data, progress_analysis)
        
        # Search for alternative recipes if needed
        alternative_recipes = []
        if progress_analysis.get('issues_reported') or progress_analysis.get('changes_requested'):
            # Search for alternatives based on issues
            search_query = self._build_adjustment_search_query(control_data, progress_analysis)
            alternative_recipes = self.chromadb.search_recipes(
                query=search_query,
                n_results=20
            )
        
        # Generate prompt for adjustment
        prompt = Motor2PromptTemplate.generate_adjustment_prompt(
            control_data=control_data.__dict__,
            progress_analysis=progress_analysis,
            current_plan={},  # Would be the actual current plan in production
            available_recipes=alternative_recipes
        )
        
        # Get adjusted plan from OpenAI
        adjusted_plan_json = await self.openai.adjust_meal_plan(prompt)
        
        # For now, return a placeholder plan
        from datetime import date, timedelta
        
        adjusted_plan = NutritionPlan(
            patient_name=control_data.patient_data.name,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=control_data.patient_data.days_requested),
            days=[],
            total_daily_calories=self._calculate_adjusted_calories(control_data, progress_analysis),
            adjustments_summary=adjustments
        )
        
        return adjusted_plan
    
    def _determine_adjustments(self, control_data: ControlData, progress_analysis: Dict[str, Any]) -> List[str]:
        """Determine necessary plan adjustments"""
        adjustments = []
        
        # Calorie adjustments
        if progress_analysis["progress_status"] == "rapid_loss":
            adjustments.append("Increased daily calories by 200-300 kcal")
        elif progress_analysis["progress_status"] == "slow_loss":
            adjustments.append("Reduced daily calories by 100-200 kcal")
        elif progress_analysis["progress_status"] == "rapid_gain":
            adjustments.append("Reduced daily calories by 200-300 kcal")
        
        # Address reported issues
        if "hunger" in str(control_data.reported_issues).lower():
            adjustments.append("Added more high-fiber foods for satiety")
            adjustments.append("Increased protein portions")
        
        if "fatigue" in str(control_data.reported_issues).lower():
            adjustments.append("Added iron-rich foods")
            adjustments.append("Improved meal timing for energy")
        
        # Handle new medical conditions
        if control_data.new_pathologies:
            adjustments.append(f"Adapted for new conditions: {', '.join(control_data.new_pathologies)}")
        
        # Address specific requests
        for request in control_data.requested_changes:
            adjustments.append(f"Accommodated request: {request}")
        
        return adjustments
    
    def _calculate_adjusted_calories(self, control_data: ControlData, progress_analysis: Dict[str, Any]) -> float:
        """Calculate adjusted daily calories based on progress"""
        # Start with original calculation
        from api.services.plan_generator import PlanGeneratorService
        generator = PlanGeneratorService(self.chromadb)
        base_calories = generator._calculate_daily_calories(control_data.patient_data)
        
        # Adjust based on progress
        if progress_analysis["progress_status"] == "rapid_loss":
            return base_calories + 250
        elif progress_analysis["progress_status"] == "slow_loss":
            return base_calories - 150
        elif progress_analysis["progress_status"] == "rapid_gain":
            return base_calories - 250
        else:
            return base_calories
    
    def _build_adjustment_search_query(self, control_data: ControlData, progress_analysis: Dict[str, Any]) -> str:
        """Build search query for finding alternative recipes"""
        query_parts = []
        
        # Base on reported issues
        issues_text = ' '.join(control_data.reported_issues).lower()
        if 'hambre' in issues_text:
            query_parts.append("alto contenido proteico saciante")
        if 'monoton' in issues_text:
            query_parts.append("variedad nuevas opciones")
        if 'difícil' in issues_text:
            query_parts.append("fácil preparación simple")
        
        # Base on progress
        if progress_analysis.get('progress_status') == 'slow_loss':
            query_parts.append("bajo calorías volumen")
        
        # Base on preferences
        if control_data.requested_changes:
            query_parts.extend(control_data.requested_changes)
        
        return ' '.join(query_parts) if query_parts else "recetas saludables variadas"