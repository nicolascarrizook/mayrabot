"""
Enhanced Recipe Search Service for Professional Nutrition Plans
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from api.services.chromadb_service import ChromaDBService
from api.models.patient import PatientData

logger = logging.getLogger(__name__)


@dataclass
class RecipeSearchCriteria:
    """Criteria for searching recipes"""
    meal_type: str
    target_calories: float
    calorie_tolerance: float = 0.2  # ±20%
    preferences: List[str] = None
    restrictions: List[str] = None
    allergies: List[str] = None
    economic_level: str = "medio"
    max_results: int = 10


class RecipeSearcher:
    """Professional recipe search with intelligent filtering"""
    
    def __init__(self, chromadb: ChromaDBService):
        self.chromadb = chromadb
        
    async def search_recipes_for_meal(
        self,
        criteria: RecipeSearchCriteria
    ) -> List[Dict[str, Any]]:
        """
        Search recipes with intelligent filtering and scoring
        
        Returns:
            List of recipes sorted by relevance score
        """
        logger.info(f"Searching recipes for {criteria.meal_type} with {criteria.target_calories} kcal")
        
        # Calculate calorie range
        min_calories = criteria.target_calories * (1 - criteria.calorie_tolerance)
        max_calories = criteria.target_calories * (1 + criteria.calorie_tolerance)
        
        # 1. Initial broad search
        all_recipes = self._get_all_meal_recipes(criteria.meal_type)
        logger.info(f"Found {len(all_recipes)} total recipes for {criteria.meal_type}")
        
        # 2. Filter by calories
        calorie_filtered = [
            r for r in all_recipes
            if min_calories <= self._get_recipe_calories(r) <= max_calories
        ]
        logger.info(f"After calorie filter: {len(calorie_filtered)} recipes")
        
        # 3. Filter by restrictions and allergies
        safe_recipes = self._filter_by_restrictions(
            calorie_filtered,
            criteria.restrictions or [],
            criteria.allergies or []
        )
        logger.info(f"After restriction filter: {len(safe_recipes)} recipes")
        
        # 4. Score by preferences and economic level
        scored_recipes = self._score_recipes(
            safe_recipes,
            criteria.preferences or [],
            criteria.economic_level,
            criteria.target_calories
        )
        
        # 5. Sort by score and return top results
        scored_recipes.sort(key=lambda x: x[1], reverse=True)
        top_recipes = [recipe for recipe, score in scored_recipes[:criteria.max_results]]
        
        logger.info(f"Returning {len(top_recipes)} top recipes")
        return top_recipes
    
    def _get_all_meal_recipes(self, meal_type: str) -> List[Dict[str, Any]]:
        """Get all recipes for a specific meal type"""
        # Map meal types to search queries
        meal_queries = {
            'desayuno': ['desayuno', 'breakfast', 'mañana'],
            'almuerzo': ['almuerzo', 'lunch', 'mediodía'],
            'merienda': ['merienda', 'snack', 'té'],
            'cena': ['cena', 'dinner', 'noche']
        }
        
        queries = meal_queries.get(meal_type, [meal_type])
        all_recipes = []
        seen_ids = set()
        
        for query in queries:
            results = self.chromadb.search_recipes(
                query=query,
                n_results=50,  # Get more results for better filtering
                filters={"meal_type": meal_type}
            )
            
            for recipe in results:
                recipe_id = recipe.get('id', str(recipe))
                if recipe_id not in seen_ids:
                    seen_ids.add(recipe_id)
                    all_recipes.append(recipe)
        
        return all_recipes
    
    def _get_recipe_calories(self, recipe: Dict[str, Any]) -> float:
        """Extract calories from recipe"""
        # Try different possible fields
        calories = recipe.get('calories', 0)
        if not calories:
            calories = recipe.get('calorias', 0)
        if not calories:
            metadata = recipe.get('metadata', {})
            if isinstance(metadata, dict):
                calories = metadata.get('calories', 0)
        
        return float(calories) if calories else 0
    
    def _filter_by_restrictions(
        self,
        recipes: List[Dict[str, Any]],
        restrictions: List[str],
        allergies: List[str]
    ) -> List[Dict[str, Any]]:
        """Filter out recipes with restricted ingredients"""
        if not restrictions and not allergies:
            return recipes
        
        safe_recipes = []
        all_restrictions = [r.lower() for r in restrictions + allergies]
        
        for recipe in recipes:
            # Get ingredients text
            ingredients_text = self._get_ingredients_text(recipe).lower()
            
            # Check if any restriction is present
            is_safe = True
            for restriction in all_restrictions:
                if restriction and restriction in ingredients_text:
                    logger.debug(f"Recipe '{recipe.get('name', 'Unknown')}' contains restricted ingredient: {restriction}")
                    is_safe = False
                    break
            
            if is_safe:
                safe_recipes.append(recipe)
        
        return safe_recipes
    
    def _get_ingredients_text(self, recipe: Dict[str, Any]) -> str:
        """Extract all ingredient text from recipe"""
        text_parts = []
        
        # Direct ingredients field
        if 'ingredients' in recipe:
            ingredients = recipe['ingredients']
            if isinstance(ingredients, list):
                for ing in ingredients:
                    if isinstance(ing, dict):
                        text_parts.append(ing.get('name', ''))
                        text_parts.append(ing.get('alimento', ''))
                    else:
                        text_parts.append(str(ing))
            else:
                text_parts.append(str(ingredients))
        
        # Check metadata
        metadata = recipe.get('metadata', {})
        if isinstance(metadata, dict) and 'ingredients' in metadata:
            text_parts.append(str(metadata['ingredients']))
        
        # Recipe name might contain ingredients
        text_parts.append(recipe.get('name', ''))
        
        return ' '.join(filter(None, text_parts))
    
    def _score_recipes(
        self,
        recipes: List[Dict[str, Any]],
        preferences: List[str],
        economic_level: str,
        target_calories: float
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Score recipes based on multiple criteria"""
        scored_recipes = []
        
        for recipe in recipes:
            score = 100.0  # Base score
            
            # 1. Preference matching (up to +50 points)
            if preferences:
                ingredients_text = self._get_ingredients_text(recipe).lower()
                recipe_name = recipe.get('name', '').lower()
                
                matches = 0
                for pref in preferences:
                    if pref.lower() in ingredients_text or pref.lower() in recipe_name:
                        matches += 1
                
                if matches > 0:
                    score += min(50, matches * 15)
            
            # 2. Economic level matching (+20 points for exact match)
            recipe_economic = recipe.get('economic_level', 'medio')
            if recipe_economic == economic_level:
                score += 20
            
            # 3. Calorie accuracy (up to +30 points)
            recipe_calories = self._get_recipe_calories(recipe)
            if recipe_calories > 0:
                calorie_diff = abs(recipe_calories - target_calories) / target_calories
                calorie_score = max(0, 30 * (1 - calorie_diff))
                score += calorie_score
            
            # 4. Recipe completeness (+10 points)
            if recipe.get('preparation') or recipe.get('preparacion'):
                score += 5
            if recipe.get('ingredients') and len(recipe.get('ingredients', [])) > 2:
                score += 5
            
            # 5. Nutritional info bonus (+10 points)
            if recipe.get('macros') or recipe.get('protein') or recipe.get('carbs'):
                score += 10
            
            scored_recipes.append((recipe, score))
            
        return scored_recipes
    
    async def find_best_recipes_for_plan(
        self,
        patient_data: PatientData,
        daily_calories: float,
        meal_distribution: Dict[str, float]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find the best recipes for a complete meal plan using optimized batch search
        
        Returns:
            Dictionary with meal_type -> list of recipe options
        """
        logger.info("Starting optimized batch recipe search...")
        
        # Prepare meal requirements
        meal_requirements = {
            meal_type: daily_calories * distribution
            for meal_type, distribution in meal_distribution.items()
        }
        
        # Prepare restrictions list
        all_restrictions = []
        if patient_data.food_dislikes:
            all_restrictions.extend(patient_data.food_dislikes)
        if patient_data.allergies:
            all_restrictions.extend(patient_data.allergies)
        
        # Add pathology-based restrictions
        for pathology in patient_data.pathologies:
            all_restrictions.extend(self._get_pathology_restrictions(pathology))
        
        # Remove duplicates
        all_restrictions = list(set(all_restrictions))
        
        # Use optimized batch search
        try:
            results = self.chromadb.batch_search_recipes(
                meal_requirements=meal_requirements,
                patient_restrictions=all_restrictions,
                preferences=patient_data.food_preferences
            )
            
            # Log results
            for meal_type, recipes in results.items():
                logger.info(f"{meal_type}: Found {len(recipes)} recipes after optimization")
            
            return results
            
        except Exception as e:
            logger.error(f"Batch search failed: {e}, falling back to individual searches")
            
            # Fallback to individual searches
            best_recipes = {}
            for meal_type, calories in meal_requirements.items():
                criteria = RecipeSearchCriteria(
                    meal_type=meal_type,
                    target_calories=calories,
                    preferences=patient_data.food_preferences,
                    restrictions=all_restrictions,
                    allergies=patient_data.allergies,
                    economic_level=patient_data.economic_level.value,
                    max_results=5
                )
                
                recipes = await self.search_recipes_for_meal(criteria)
                best_recipes[meal_type] = recipes
            
            return best_recipes
    
    def _get_pathology_restrictions(self, pathology: str) -> List[str]:
        """Get food restrictions based on pathology"""
        pathology_lower = pathology.lower()
        
        restrictions_map = {
            'diabetes': ['azúcar', 'dulce', 'mermelada', 'miel'],
            'hipertensión': ['sal', 'embutido', 'fiambre', 'snack'],
            'hipertension': ['sal', 'embutido', 'fiambre', 'snack'],
            'colesterol': ['manteca', 'grasa', 'fritura', 'yema'],
            'celíaco': ['gluten', 'trigo', 'harina', 'pan'],
            'celiaco': ['gluten', 'trigo', 'harina', 'pan'],
            'gota': ['mariscos', 'vísceras', 'anchoas'],
            'renal': ['sal', 'potasio', 'fósforo']
        }
        
        for condition, foods in restrictions_map.items():
            if condition in pathology_lower:
                return foods
                
        return []