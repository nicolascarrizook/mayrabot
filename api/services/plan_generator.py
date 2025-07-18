"""
Plan Generator Service - Generates nutrition plans using AI
"""

from typing import Dict, Any, List
import logging
from dataclasses import dataclass
from datetime import date, timedelta

from api.models.patient import PatientData
from api.services.chromadb_service import ChromaDBService
from api.services.openai_service import OpenAIService
from prompts.motor1_prompt import Motor1PromptTemplate

logger = logging.getLogger(__name__)


@dataclass
class DayPlan:
    """Represents a single day's meal plan"""
    date: date
    meals: Dict[str, Dict[str, Any]]
    total_calories: float
    macros: Dict[str, float]


@dataclass
class NutritionPlan:
    """Complete nutrition plan"""
    patient_name: str
    start_date: date
    end_date: date
    days: List[DayPlan]
    total_daily_calories: float
    adjustments_summary: List[str] = None


class PlanGeneratorService:
    """Service for generating nutrition plans"""
    
    def __init__(self, chromadb_service: ChromaDBService):
        self.chromadb = chromadb_service
        self.openai = OpenAIService()
    
    async def generate_plan(self, patient_data: PatientData) -> NutritionPlan:
        """
        Generate a complete nutrition plan for a patient
        
        Args:
            patient_data: Patient information and preferences
            
        Returns:
            Complete nutrition plan
        """
        logger.info(f"Generating plan for {patient_data.name}")
        
        # Calculate nutritional requirements
        daily_calories = self._calculate_daily_calories(patient_data)
        macro_distribution = self._calculate_macro_distribution(patient_data)
        
        # Generate meal plans for each day
        days = []
        start_date = date.today()
        
        for day_num in range(patient_data.days_requested):
            current_date = start_date + timedelta(days=day_num)
            
            # Generate meals for the day
            day_meals = await self._generate_day_meals(
                patient_data,
                daily_calories,
                macro_distribution,
                day_num
            )
            
            # Calculate day totals
            day_calories = sum(meal['calories'] for meal in day_meals.values())
            day_macros = self._calculate_day_macros(day_meals)
            
            days.append(DayPlan(
                date=current_date,
                meals=day_meals,
                total_calories=day_calories,
                macros=day_macros
            ))
        
        return NutritionPlan(
            patient_name=patient_data.name,
            start_date=start_date,
            end_date=start_date + timedelta(days=patient_data.days_requested - 1),
            days=days,
            total_daily_calories=daily_calories
        )
    
    def _calculate_daily_calories(self, patient_data: PatientData) -> float:
        """Calculate daily caloric needs"""
        # Mifflin-St Jeor equation for BMR
        if patient_data.gender == "male":
            bmr = 10 * patient_data.weight + 6.25 * patient_data.height - 5 * patient_data.age + 5
        else:
            bmr = 10 * patient_data.weight + 6.25 * patient_data.height - 5 * patient_data.age - 161
        
        # Activity factor
        activity_factors = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9
        }
        
        tdee = bmr * activity_factors.get(patient_data.activity_level, 1.2)
        
        # Adjust for weight goals based on BMI
        if patient_data.bmi > 25:  # Overweight
            tdee *= 0.85  # 15% deficit
        elif patient_data.bmi < 18.5:  # Underweight
            tdee *= 1.15  # 15% surplus
        
        return round(tdee)
    
    def _calculate_macro_distribution(self, patient_data: PatientData) -> Dict[str, float]:
        """Calculate macronutrient distribution"""
        # Default balanced distribution
        distribution = {
            "carbohydrates": 0.45,
            "proteins": 0.25,
            "fats": 0.30
        }
        
        # Adjust for specific conditions
        if "diabetes" in [p.lower() for p in patient_data.pathologies]:
            distribution["carbohydrates"] = 0.40
            distribution["proteins"] = 0.30
            distribution["fats"] = 0.30
        
        return distribution
    
    async def _generate_day_meals(
        self,
        patient_data: PatientData,
        daily_calories: float,
        macro_distribution: Dict[str, float],
        day_num: int
    ) -> Dict[str, Dict[str, Any]]:
        """Generate meals for a single day"""
        
        # Get search queries for each meal type
        search_queries = Motor1PromptTemplate.generate_recipe_search_queries(
            patient_data.__dict__
        )
        
        # Distribute calories across meals
        meal_distribution = self._get_meal_distribution(patient_data.meals_per_day)
        
        meals = {}
        meal_types = self._get_meal_types(patient_data.meals_per_day)
        
        # Collect all recipes for the day
        all_day_recipes = []
        
        for meal_type in meal_types:
            meal_calories = daily_calories * meal_distribution[meal_type]
            
            # Search for recipes using appropriate queries
            queries = search_queries.get(meal_type, [meal_type])
            for query in queries[:3]:  # Use top 3 queries
                recipes = self.chromadb.search_recipes(
                    query=query,
                    n_results=5,
                    filters={
                        "meal_types": meal_type,
                        "economic_level": patient_data.economic_level.value if hasattr(patient_data.economic_level, 'value') else patient_data.economic_level
                    }
                )
                if recipes:
                    all_day_recipes.extend(recipes)
                    break
        
        # Generate the complete day plan using GPT-4
        if all_day_recipes:
            # Prepare the prompt
            prompt = Motor1PromptTemplate.generate_plan_prompt(
                patient_data=patient_data.__dict__,
                available_recipes=all_day_recipes,
                nutritional_requirements={
                    "daily_calories": daily_calories,
                    "carbs_percentage": macro_distribution["carbohydrates"] * 100,
                    "protein_percentage": macro_distribution["proteins"] * 100,
                    "fat_percentage": macro_distribution["fats"] * 100,
                    "special_considerations": self._get_special_considerations(patient_data)
                }
            )
            
            # Get plan from OpenAI
            logger.info(f"Calling OpenAI with prompt length: {len(prompt)} chars")
            plan_json = await self.openai.generate_meal_plan(
                patient_info=patient_data.__dict__,
                recipes=all_day_recipes,
                requirements={"prompt": prompt}
            )
            
            logger.info(f"Received OpenAI response length: {len(plan_json)} chars")
            logger.debug(f"OpenAI response preview: {plan_json[:500]}...")
            
            # Parse and return the day's meals
            import json
            try:
                plan_data = json.loads(plan_json)
                logger.info(f"Successfully parsed JSON with keys: {list(plan_data.keys())}")
                parsed_meals = self._parse_generated_meals(plan_data, meal_types)
                logger.info(f"Parsed {len(parsed_meals)} meals")
                return parsed_meals
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.error(f"Failed to parse OpenAI response: {plan_json[:200]}...")
                return self._generate_placeholder_meals(meal_types, meal_distribution, daily_calories)
        
        # If no recipes found, return placeholder
        return self._generate_placeholder_meals(meal_types, meal_distribution, daily_calories)
    
    def _get_meal_distribution(self, meals_per_day: int) -> Dict[str, float]:
        """Get calorie distribution across meals"""
        distributions = {
            3: {"desayuno": 0.30, "almuerzo": 0.40, "cena": 0.30},
            4: {"desayuno": 0.25, "almuerzo": 0.35, "merienda": 0.15, "cena": 0.25},
            5: {"desayuno": 0.20, "colacion_am": 0.10, "almuerzo": 0.35, 
                "merienda": 0.15, "cena": 0.20},
            6: {"desayuno": 0.20, "colacion_am": 0.10, "almuerzo": 0.30,
                "merienda": 0.10, "cena": 0.20, "colacion_pm": 0.10}
        }
        return distributions.get(meals_per_day, distributions[4])
    
    def _get_meal_types(self, meals_per_day: int) -> List[str]:
        """Get meal types based on meals per day"""
        meal_plans = {
            3: ["desayuno", "almuerzo", "cena"],
            4: ["desayuno", "almuerzo", "merienda", "cena"],
            5: ["desayuno", "colacion_am", "almuerzo", "merienda", "cena"],
            6: ["desayuno", "colacion_am", "almuerzo", "merienda", "cena", "colacion_pm"]
        }
        return meal_plans.get(meals_per_day, meal_plans[4])
    
    async def _select_recipe_for_meal(
        self,
        patient_data: PatientData,
        meal_type: str,
        target_calories: float,
        day_num: int
    ) -> Dict[str, Any]:
        """Select appropriate recipe for a meal"""
        
        # Placeholder implementation
        # In production, this would use ChromaDB search and OpenAI
        return {
            "name": f"Sample {meal_type} - Day {day_num + 1}",
            "description": "Placeholder meal description",
            "ingredients": ["ingredient1", "ingredient2"],
            "preparation": "Preparation instructions",
            "calories": target_calories,
            "macros": {
                "carbohydrates": target_calories * 0.45 / 4,
                "proteins": target_calories * 0.25 / 4,
                "fats": target_calories * 0.30 / 9
            }
        }
    
    def _calculate_day_macros(self, meals: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Calculate total macros for a day"""
        totals = {"carbohydrates": 0, "proteins": 0, "fats": 0}
        
        for meal in meals.values():
            if "macros" in meal:
                for macro, value in meal["macros"].items():
                    totals[macro] += value
        
        return totals
    
    def _parse_generated_meals(self, plan_data: Dict[str, Any], meal_types: List[str]) -> Dict[str, Dict[str, Any]]:
        """Parse meals from OpenAI response"""
        meals = {}
        
        # Handle different possible response formats
        if "meals" in plan_data:
            meal_list = plan_data["meals"]
        elif "day_meals" in plan_data:
            meal_list = plan_data["day_meals"]
        else:
            # Try to find meals in the response
            for key in plan_data:
                if isinstance(plan_data[key], list) and len(plan_data[key]) > 0:
                    meal_list = plan_data[key]
                    break
            else:
                logger.error("No meals found in OpenAI response")
                return {}
        
        # Parse each meal
        for meal_data in meal_list:
            meal_type = meal_data.get("meal_type", "").lower()
            
            # Map meal types if needed
            if meal_type in ["breakfast", "desayuno"]:
                meal_type = "desayuno"
            elif meal_type in ["lunch", "almuerzo"]:
                meal_type = "almuerzo"
            elif meal_type in ["dinner", "cena"]:
                meal_type = "cena"
            elif meal_type in ["snack", "merienda"]:
                meal_type = "merienda"
            elif "colacion" in meal_type or "snack" in meal_type:
                if "am" in meal_type or "morning" in meal_type:
                    meal_type = "colacion_am"
                else:
                    meal_type = "colacion_pm"
            
            if meal_type in meal_types:
                meals[meal_type] = {
                    "name": meal_data.get("recipe_name", meal_data.get("name", "Sin nombre")),
                    "description": meal_data.get("description", ""),
                    "ingredients": meal_data.get("ingredients", []),
                    "preparation": meal_data.get("preparation", meal_data.get("instructions", "")),
                    "calories": float(meal_data.get("calories", 0)),
                    "portion": meal_data.get("portion", ""),
                    "macros": {
                        "carbohydrates": float(meal_data.get("carbs", meal_data.get("carbohydrates", 0))),
                        "proteins": float(meal_data.get("protein", meal_data.get("proteins", 0))),
                        "fats": float(meal_data.get("fat", meal_data.get("fats", 0)))
                    }
                }
        
        # Fill any missing meals with defaults
        for meal_type in meal_types:
            if meal_type not in meals:
                logger.warning(f"Missing meal type {meal_type} in generated plan")
        
        return meals
    
    def _get_special_considerations(self, patient_data: PatientData) -> List[str]:
        """Get special considerations based on patient data"""
        considerations = []
        
        if patient_data.pathologies:
            considerations.append(f"Patologías: {', '.join(patient_data.pathologies)}")
        
        if patient_data.allergies:
            considerations.append(f"Alergias: {', '.join(patient_data.allergies)}")
        
        if patient_data.bmi > 30:
            considerations.append("Enfoque en pérdida de peso saludable")
        elif patient_data.bmi < 18.5:
            considerations.append("Enfoque en ganancia de peso saludable")
        
        return considerations
    
    def _generate_placeholder_meals(
        self,
        meal_types: List[str],
        meal_distribution: Dict[str, float],
        daily_calories: float
    ) -> Dict[str, Dict[str, Any]]:
        """Generate placeholder meals for testing"""
        meals = {}
        
        for meal_type in meal_types:
            meal_calories = daily_calories * meal_distribution.get(meal_type, 0.25)
            meals[meal_type] = {
                "name": f"Placeholder {meal_type}",
                "description": f"Comida de prueba para {meal_type}",
                "ingredients": ["Ingrediente 1", "Ingrediente 2"],
                "preparation": "Preparación de prueba",
                "calories": meal_calories,
                "macros": {
                    "carbohydrates": meal_calories * 0.45 / 4,
                    "proteins": meal_calories * 0.25 / 4,
                    "fats": meal_calories * 0.30 / 9
                }
            }
        
        return meals