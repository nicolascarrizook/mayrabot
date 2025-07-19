"""
Plan Generator Service - Generates nutrition plans using AI
"""

from typing import Dict, Any, List, Optional
import json
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
        
        # Load validation settings
        from api.config import settings
        self.strict_validation = settings.strict_recipe_validation
        self.reject_invalid = settings.reject_invalid_recipes
        self.log_validation = settings.log_recipe_validation
    
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
        
        # Generate meal plan for ONE day (Tres Días y Carga - same menu for 3 days)
        # Only generate day 0 since all days are identical
        day_meals = await self._generate_day_meals(
            patient_data,
            daily_calories,
            macro_distribution,
            0  # Always day 0 for Tres Días y Carga
        )
        
        # Calculate day totals
        day_calories = sum(meal['calories'] for meal in day_meals.values())
        day_macros = self._calculate_day_macros(day_meals)
        
        # Create 3 identical days
        days = []
        start_date = date.today()
        
        for day_num in range(3):  # Always 3 days for Tres Días y Carga
            current_date = start_date + timedelta(days=day_num)
            days.append(DayPlan(
                date=current_date,
                meals=day_meals,  # Same meals for all 3 days
                total_calories=day_calories,
                macros=day_macros
            ))
        
        return NutritionPlan(
            patient_name=patient_data.name,
            start_date=start_date,
            end_date=start_date + timedelta(days=2),  # Always 3 days
            days=days,
            total_daily_calories=daily_calories
        )
    
    def _calculate_daily_calories(self, patient_data: PatientData) -> float:
        """Calculate daily caloric needs based on objective"""
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
        
        tdee = bmr * activity_factors.get(patient_data.activity_level.value if hasattr(patient_data.activity_level, 'value') else patient_data.activity_level, 1.2)
        
        # Adjust based on objective (Tres Días y Carga method)
        objective = patient_data.objective.value if hasattr(patient_data.objective, 'value') else patient_data.objective
        if objective == "mantenimiento":
            return round(tdee)
        elif objective == "bajar_025":
            return round(tdee - 250)  # Bajar 0.25 kg/semana
        elif objective == "bajar_05":
            return round(tdee - 500)  # Bajar 0.5 kg/semana
        elif objective == "bajar_075":
            return round(tdee - 750)  # Bajar 0.75 kg/semana
        elif objective == "bajar_1":
            return round(tdee - 1000)  # Bajar 1 kg/semana
        elif objective == "subir_025":
            return round(tdee + 250)  # Subir 0.25 kg/semana
        elif objective == "subir_05":
            return round(tdee + 500)  # Subir 0.5 kg/semana
        elif objective == "subir_075":
            return round(tdee + 750)  # Subir 0.75 kg/semana
        elif objective == "subir_1":
            return round(tdee + 1000)  # Subir 1 kg/semana
        else:
            return round(tdee)
    
    def _calculate_macro_distribution(self, patient_data: PatientData) -> Dict[str, float]:
        """Calculate macronutrient distribution"""
        # Check if custom macros are provided
        if patient_data.protein_level or patient_data.carbs_percentage is not None or patient_data.fat_percentage:
            return self._calculate_custom_macro_distribution(patient_data)
        
        # Default distribution for Tres Días y Carga
        distribution = {
            "carbohydrates": 0.45,
            "proteins": 0.25,
            "fats": 0.30
        }
        
        # Adjust for specific conditions
        pathologies_lower = [p.lower() for p in patient_data.pathologies]
        
        if "diabetes" in pathologies_lower or "resistencia a la insulina" in pathologies_lower:
            distribution["carbohydrates"] = 0.40
            distribution["proteins"] = 0.30
            distribution["fats"] = 0.30
        elif "hígado graso" in pathologies_lower:
            distribution["carbohydrates"] = 0.40
            distribution["proteins"] = 0.30
            distribution["fats"] = 0.30
        
        # Adjust for objectives
        objective = patient_data.objective.value if hasattr(patient_data.objective, 'value') else patient_data.objective
        if "bajar" in objective:
            # Increase protein for weight loss
            distribution["proteins"] = 0.30
            distribution["carbohydrates"] = 0.40
        elif "subir" in objective:
            # Increase carbs for weight gain
            distribution["carbohydrates"] = 0.50
            distribution["proteins"] = 0.20
        
        return distribution
    
    def _calculate_custom_macro_distribution(self, patient_data: PatientData) -> Dict[str, float]:
        """Calculate custom macronutrient distribution based on user preferences"""
        # Get daily calories for calculations
        daily_calories = self._calculate_daily_calories(patient_data)
        
        # Step 1: Calculate protein percentage based on level and body weight
        protein_percentage = 0.25  # Default if not specified
        
        if patient_data.protein_level:
            protein_g_per_kg = self._get_protein_grams_per_kg(patient_data.protein_level)
            total_protein_g = patient_data.weight * protein_g_per_kg
            protein_calories = total_protein_g * 4  # 4 kcal per gram of protein
            protein_percentage = protein_calories / daily_calories
            
            # Cap protein percentage at reasonable levels
            protein_percentage = min(protein_percentage, 0.40)  # Max 40% protein
        
        # Step 2: Use direct carbs percentage if provided
        if patient_data.carbs_percentage is not None:
            carbs_percentage = patient_data.carbs_percentage / 100  # Convert to decimal
        else:
            # Default carbs if not specified
            carbs_percentage = 0.45
        
        # Step 3: Calculate or use specified fat percentage
        if patient_data.fat_percentage:
            fat_percentage = patient_data.fat_percentage / 100
        else:
            # Calculate remaining percentage for fats to complete 100%
            fat_percentage = 1.0 - protein_percentage - carbs_percentage
        
        # Validate that macros sum to 100%
        total = protein_percentage + carbs_percentage + fat_percentage
        if abs(total - 1.0) > 0.02:  # Allow 2% tolerance
            # Adjust fats to make it sum to 100%
            fat_percentage = 1.0 - protein_percentage - carbs_percentage
        
        # Ensure all macros are within healthy ranges
        distribution = {
            "proteins": round(protein_percentage, 2),
            "carbohydrates": round(carbs_percentage, 2),
            "fats": round(max(0.15, min(0.45, fat_percentage)), 2)  # Keep fats between 15-45%
        }
        
        # Final adjustment to ensure exactly 100%
        total = sum(distribution.values())
        if total != 1.0:
            distribution["fats"] = round(1.0 - distribution["proteins"] - distribution["carbohydrates"], 2)
        
        logger.info(f"Custom macro distribution: Protein={distribution['proteins']*100}%, "
                   f"Carbs={distribution['carbohydrates']*100}%, Fats={distribution['fats']*100}%")
        
        return distribution
    
    def _get_protein_grams_per_kg(self, protein_level: str) -> float:
        """Get protein grams per kg based on level"""
        protein_ranges = {
            "muy_baja": 0.65,      # Middle of 0.5-0.8 range
            "conservada": 1.0,     # Middle of 0.8-1.2 range
            "moderada": 1.4,       # Middle of 1.2-1.6 range
            "alta": 1.9,           # Middle of 1.6-2.2 range
            "muy_alta": 2.5,       # Middle of 2.2-2.8 range
            "extrema": 3.25        # Middle of 3.0-3.5 range
        }
        
        level = protein_level.value if hasattr(protein_level, 'value') else protein_level
        return protein_ranges.get(level, 1.0)
    
    async def _generate_day_meals(
        self,
        patient_data: PatientData,
        daily_calories: float,
        macro_distribution: Dict[str, float],
        day_num: int
    ) -> Dict[str, Dict[str, Any]]:
        """Generate meals for a single day"""
        
        # Use enhanced recipe searcher
        from api.services.recipe_searcher import RecipeSearcher
        recipe_searcher = RecipeSearcher(self.chromadb)
        
        # Distribute calories across meals
        meal_distribution = self._get_meal_distribution(
            patient_data.meals_per_day,
            patient_data.distribution_type.value if hasattr(patient_data, 'distribution_type') else "traditional"
        )
        meal_types = self._get_meal_types(patient_data.meals_per_day)
        
        # Find best recipes for each meal
        logger.info("Starting intelligent recipe search...")
        best_recipes = await recipe_searcher.find_best_recipes_for_plan(
            patient_data=patient_data,
            daily_calories=daily_calories,
            meal_distribution=meal_distribution
        )
        
        # Create a dictionary of valid recipe names for validation
        self._valid_recipe_names = set()
        self._recipe_lookup = {}
        
        # Log recipe search results
        for meal_type, recipes in best_recipes.items():
            logger.info(f"{meal_type}: Found {len(recipes)} suitable recipes")
            if recipes:
                logger.info(f"  Top recipe: {recipes[0].get('name', 'Unknown')} - {self._get_recipe_calories(recipes[0])} kcal")
                # Store valid recipe names for validation
                for recipe in recipes:
                    recipe_name = recipe.get('metadata', {}).get('recipe_name', recipe.get('name', ''))
                    if recipe_name:
                        self._valid_recipe_names.add(recipe_name.lower())
                        self._recipe_lookup[recipe_name.lower()] = recipe
        
        # Flatten all recipes for the prompt
        all_day_recipes = []
        for meal_type, recipes in best_recipes.items():
            all_day_recipes.extend(recipes[:3])  # Take top 3 per meal
        
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
            logger.info(f"Sent {len(self._valid_recipe_names)} valid recipes to OpenAI")
            
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
                
                # Validate that all recipes in the plan exist in our database
                validated_meals = self._validate_generated_meals(parsed_meals)
                
                # Log validation results
                logger.info("=" * 60)
                logger.info("RECIPE VALIDATION SUMMARY:")
                logger.info(f"Recipes sent to OpenAI: {len(self._valid_recipe_names)}")
                logger.info(f"Meals generated by OpenAI: {len(parsed_meals)}")
                logger.info(f"Meals validated successfully: {len(validated_meals)}")
                
                # Log which recipes were selected
                for meal_type, meal_data in validated_meals.items():
                    logger.info(f"  {meal_type}: {meal_data.get('name')} ({meal_data.get('calories', 0)} kcal)")
                logger.info("=" * 60)
                
                # Log sample meal for debugging
                if validated_meals:
                    first_meal_key = list(validated_meals.keys())[0]
                    logger.debug(f"Sample meal ({first_meal_key}): {validated_meals[first_meal_key]}")
                
                return validated_meals
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.error(f"Failed to parse OpenAI response: {plan_json[:200]}...")
                return self._generate_placeholder_meals(meal_types, meal_distribution, daily_calories)
        
        # If no recipes found, return placeholder
        return self._generate_placeholder_meals(meal_types, meal_distribution, daily_calories)
    
    def _get_meal_distribution(self, meals_per_day: int, distribution_type: str = "traditional") -> Dict[str, float]:
        """Get calorie distribution across meals"""
        if distribution_type == "equitable":
            # Equal distribution for all meals
            meal_types = self._get_meal_types(meals_per_day)
            equal_percentage = 1.0 / len(meal_types)
            return {meal: equal_percentage for meal in meal_types}
        
        # Traditional distribution
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
        totals = {
            "carbohydrates": 0, 
            "proteins": 0, 
            "fats": 0,
            "carbohydrates_g": 0,
            "carbohydrates_kcal": 0,
            "proteins_g": 0,
            "proteins_kcal": 0,
            "fats_g": 0,
            "fats_kcal": 0
        }
        
        for meal in meals.values():
            if "macros" in meal:
                macros = meal["macros"]
                # Handle both old and new format
                if "carbohidratos_g" in macros:
                    # New format
                    totals["carbohydrates_g"] += macros.get("carbohidratos_g", 0)
                    totals["carbohydrates_kcal"] += macros.get("carbohidratos_kcal", 0)
                    totals["proteins_g"] += macros.get("proteinas_g", 0)
                    totals["proteins_kcal"] += macros.get("proteinas_kcal", 0)
                    totals["fats_g"] += macros.get("grasas_g", 0)
                    totals["fats_kcal"] += macros.get("grasas_kcal", 0)
                    # Also update old format for compatibility
                    totals["carbohydrates"] = totals["carbohydrates_g"]
                    totals["proteins"] = totals["proteins_g"]
                    totals["fats"] = totals["fats_g"]
                else:
                    # Old format - calculate kcal
                    carbs_g = macros.get("carbohydrates", macros.get("carbos", 0))
                    proteins_g = macros.get("proteins", macros.get("proteinas", 0))
                    fats_g = macros.get("fats", macros.get("grasas", 0))
                    
                    totals["carbohydrates"] += carbs_g
                    totals["proteins"] += proteins_g
                    totals["fats"] += fats_g
                    
                    totals["carbohydrates_g"] += carbs_g
                    totals["carbohydrates_kcal"] += carbs_g * 4
                    totals["proteins_g"] += proteins_g
                    totals["proteins_kcal"] += proteins_g * 4
                    totals["fats_g"] += fats_g
                    totals["fats_kcal"] += fats_g * 9
        
        return totals
    
    def _parse_generated_meals(self, plan_data: Dict[str, Any], meal_types: List[str]) -> Dict[str, Dict[str, Any]]:
        """Parse meals from OpenAI response"""
        meals = {}
        
        # Handle "Tres Días y Carga" format first
        if "meal_plan" in plan_data:
            # This is the Tres Días y Carga format
            meal_plan = plan_data["meal_plan"]
            for meal_type in meal_types:
                if meal_type in meal_plan:
                    meal_info = meal_plan[meal_type]
                    # Get the first option (all options are equivalent)
                    if "opciones" in meal_info and meal_info["opciones"]:
                        first_option = meal_info["opciones"][0]
                        meals[meal_type] = {
                            "name": first_option.get("nombre", "Sin nombre"),
                            "description": "",
                            "ingredients": first_option.get("ingredientes", []),
                            "preparation": first_option.get("preparacion", ""),
                            "calories": float(first_option.get("calorias", 0)),
                            "portion": "",
                            "macros": first_option.get("macros", {
                                "carbohydrates": 0,
                                "proteins": 0,
                                "fats": 0
                            })
                        }
                    elif "time" in meal_info:
                        # Simple format with direct meal info
                        meals[meal_type] = meal_info
        
        # Handle list formats
        elif "meals" in plan_data:
            meal_list = plan_data["meals"]
            meals = self._parse_meal_list(meal_list, meal_types)
        elif "day_meals" in plan_data:
            meal_list = plan_data["day_meals"]
            meals = self._parse_meal_list(meal_list, meal_types)
        elif "days" in plan_data and plan_data["days"]:
            # Handle days format
            first_day = plan_data["days"][0]
            if "meals" in first_day:
                meals = first_day["meals"]
        else:
            # Try to find meals in the response
            for key in plan_data:
                if isinstance(plan_data[key], list) and len(plan_data[key]) > 0:
                    meal_list = plan_data[key]
                    meals = self._parse_meal_list(meal_list, meal_types)
                    break
            else:
                logger.error("No meals found in OpenAI response")
                logger.error(f"Response keys: {list(plan_data.keys())}")
                return {}
        
        # Fill any missing meals with defaults
        for meal_type in meal_types:
            if meal_type not in meals:
                logger.warning(f"Missing meal type {meal_type} in generated plan")
        
        return meals
    
    def _parse_meal_list(self, meal_list: List[Dict[str, Any]], meal_types: List[str]) -> Dict[str, Dict[str, Any]]:
        """Parse a list of meals into a dictionary"""
        meals = {}
        
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
        
        return meals
    
    def _validate_generated_meals(self, meals: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Validate that all meals in the generated plan use only recipes from our database
        
        Args:
            meals: Dictionary of meals from OpenAI
            
        Returns:
            Validated meals dictionary
            
        Raises:
            ValueError: If strict validation is enabled and invalid recipes are found
        """
        validated_meals = {}
        invalid_recipes = []
        
        for meal_type, meal_data in meals.items():
            recipe_name = meal_data.get('name', '').lower()
            
            # Check if recipe exists in our valid recipes
            if recipe_name in self._valid_recipe_names:
                validated_meals[meal_type] = meal_data
                if self.log_validation:
                    logger.info(f"✓ Validated recipe for {meal_type}: {meal_data.get('name')}")
            else:
                # Recipe not found in database
                invalid_recipes.append((meal_type, meal_data.get('name')))
                
                if self.strict_validation:
                    logger.warning(f"⚠️ Recipe '{meal_data.get('name')}' for {meal_type} not found in database!")
                    
                    # In strict mode with reject option, raise error
                    if self.reject_invalid:
                        raise ValueError(
                            f"Invalid recipe detected: '{meal_data.get('name')}' for {meal_type}. "
                            f"This recipe does not exist in the database."
                        )
                    
                    # Try to find a substitute
                    substitute = self._find_substitute_recipe(meal_type, meal_data)
                    if substitute:
                        validated_meals[meal_type] = substitute
                        if self.log_validation:
                            logger.info(f"↻ Substituted with valid recipe: {substitute.get('name')}")
                    else:
                        logger.error(f"✗ No valid substitute found for {meal_type}")
                else:
                    # In non-strict mode, accept the recipe but log warning
                    validated_meals[meal_type] = meal_data
                    logger.warning(f"⚠️ Non-strict mode: Accepting unvalidated recipe '{meal_data.get('name')}' for {meal_type}")
        
        # Log summary if enabled
        if self.log_validation and invalid_recipes:
            logger.warning(f"Found {len(invalid_recipes)} invalid recipes: {invalid_recipes}")
        
        return validated_meals
    
    def _find_substitute_recipe(self, meal_type: str, invalid_meal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a substitute recipe from valid recipes when OpenAI suggests an invalid one
        
        Args:
            meal_type: Type of meal (desayuno, almuerzo, etc.)
            invalid_meal: The invalid meal data from OpenAI
            
        Returns:
            A valid substitute recipe or None
        """
        target_calories = invalid_meal.get('calories', 0)
        
        # Find recipes for this meal type from our valid recipes
        best_match = None
        min_calorie_diff = float('inf')
        
        for recipe_name, recipe_data in self._recipe_lookup.items():
            # Check if recipe is suitable for this meal type
            recipe_meal_types = recipe_data.get('metadata', {}).get('meal_types', '[]')
            try:
                import json
                meal_types_list = json.loads(recipe_meal_types) if isinstance(recipe_meal_types, str) else recipe_meal_types
                if meal_type in meal_types_list:
                    # Calculate calorie difference
                    recipe_calories = self._get_recipe_calories(recipe_data)
                    calorie_diff = abs(recipe_calories - target_calories)
                    
                    if calorie_diff < min_calorie_diff:
                        min_calorie_diff = calorie_diff
                        best_match = recipe_data
            except:
                continue
        
        if best_match:
            # Format the substitute recipe
            return {
                "name": best_match.get('metadata', {}).get('recipe_name', 'Substitute Recipe'),
                "description": best_match.get('content', '')[:200],
                "ingredients": self._extract_ingredients_from_content(best_match.get('content', '')),
                "preparation": "Ver preparación en receta original",
                "calories": self._get_recipe_calories(best_match),
                "portion": "",
                "macros": {
                    "carbohydrates": 0,
                    "proteins": 0,
                    "fats": 0
                }
            }
        
        return None
    
    def _extract_ingredients_from_content(self, content: str) -> List[str]:
        """Extract ingredients from recipe content"""
        ingredients = []
        lines = content.split('\n')
        in_ingredients = False
        
        for line in lines:
            if 'ingredientes:' in line.lower():
                in_ingredients = True
                continue
            elif 'preparación:' in line.lower() or 'notas:' in line.lower():
                in_ingredients = False
            elif in_ingredients and line.strip().startswith('-'):
                ingredients.append(line.strip()[1:].strip())
        
        return ingredients[:5]  # Return max 5 ingredients
    
    def _parse_generated_meals(self, plan_data: Dict[str, Any], meal_types: List[str]) -> Dict[str, Dict[str, Any]]:
        """Parse generated meal plan from OpenAI response"""
        meals = {}
        
        logger.info(f"Parsing meals with keys: {list(plan_data.keys())}")
        
        # Handle different response formats
        # Format 1: meal_plan with opciones (Tres Días y Carga format)
        if "meal_plan" in plan_data:
            meal_plan = plan_data["meal_plan"]
            logger.info(f"Found meal_plan with keys: {list(meal_plan.keys())}")
            
            for meal_type in meal_types:
                if meal_type in meal_plan:
                    meal_info = meal_plan[meal_type]
                    
                    # Get the first option (all options are equivalent)
                    if "opciones" in meal_info and meal_info["opciones"]:
                        first_option = meal_info["opciones"][0]
                        
                        # Format ingredients properly
                        ingredients = []
                        for ing in first_option.get("ingredientes", []):
                            if isinstance(ing, dict):
                                ingredients.append({
                                    "alimento": ing.get("alimento", ""),
                                    "cantidad": ing.get("cantidad", ""),
                                    "tipo": ing.get("tipo", "crudo")
                                })
                            else:
                                ingredients.append(str(ing))
                        
                        # Map macros to correct names
                        macros = first_option.get("macros", {})
                        if "carbos" in macros:
                            macros["carbohydrates"] = macros.pop("carbos", 0)
                        if "proteinas" in macros:
                            macros["proteins"] = macros.pop("proteinas", 0)
                        if "grasas" in macros:
                            macros["fats"] = macros.pop("grasas", 0)
                        
                        meals[meal_type] = {
                            "name": first_option.get("nombre", "Sin nombre"),
                            "description": "",
                            "ingredients": ingredients,
                            "preparation": first_option.get("preparacion", ""),
                            "calories": float(first_option.get("calorias", 0)),
                            "portion": "",
                            "macros": macros
                        }
                        logger.info(f"Parsed {meal_type} with {len(ingredients)} ingredients")
                    else:
                        logger.warning(f"No opciones found for {meal_type}")
        
        # Format 2: Direct meals structure
        elif "meals" in plan_data:
            for meal in plan_data["meals"]:
                meal_type = meal.get("meal_type", "").lower()
                if meal_type in meal_types:
                    meals[meal_type] = {
                        "name": meal.get("name", meal.get("recipe_name", "")),
                        "description": meal.get("description", ""),
                        "ingredients": meal.get("ingredients", []),
                        "preparation": meal.get("preparation", meal.get("instructions", "")),
                        "calories": float(meal.get("calories", 0)),
                        "portion": meal.get("portion", ""),
                        "macros": meal.get("macros", {})
                    }
        
        # Format 3: Days structure
        elif "days" in plan_data and plan_data["days"]:
            first_day = plan_data["days"][0]
            if "meals" in first_day:
                if isinstance(first_day["meals"], dict):
                    meals = first_day["meals"]
                elif isinstance(first_day["meals"], list):
                    for meal in first_day["meals"]:
                        meal_type = meal.get("meal_type", "").lower()
                        if meal_type in meal_types:
                            meals[meal_type] = meal
        
        # If no meals found, log the structure
        if not meals:
            logger.error("No meals parsed from OpenAI response")
            logger.error(f"Plan data structure: {json.dumps(plan_data, indent=2)[:1000]}")
            return self._generate_placeholder_meals(meal_types, self._get_meal_distribution(len(meal_types)), 2000)
        
        return meals
    
    def _get_recipe_calories(self, recipe: Dict[str, Any]) -> float:
        """Extract calories from recipe data"""
        # Try different possible fields
        calories = recipe.get('calories', 0)
        if not calories:
            calories = recipe.get('calorias', 0)
        if not calories:
            metadata = recipe.get('metadata', {})
            if isinstance(metadata, dict):
                calories = metadata.get('calories', 0)
        
        return float(calories) if calories else 0
    
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