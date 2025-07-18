"""
Meal Replacer Service - Finds suitable meal replacements
"""

import logging
from typing import Dict, Any, List

from api.models.patient import MealReplacementRequest
from api.services.chromadb_service import ChromaDBService
from api.services.openai_service import OpenAIService
from prompts.motor3_prompt import Motor3PromptTemplate

logger = logging.getLogger(__name__)


class MealReplacerService:
    """Service for finding meal replacements"""
    
    def __init__(self, chromadb_service: ChromaDBService):
        self.chromadb = chromadb_service
        self.openai = OpenAIService()
    
    async def find_replacements(
        self,
        request: MealReplacementRequest
    ) -> List[Dict[str, Any]]:
        """
        Find suitable meal replacements
        
        Args:
            request: Meal replacement request
            
        Returns:
            List of suitable replacement options
        """
        logger.info(f"Finding replacements for {request.meal_to_replace}")
        
        # Build search query
        query = self._build_search_query(request)
        
        # Set up filters
        filters = {
            "meal_types": request.meal_type,
            "economic_level": request.patient_data.economic_level
        }
        
        # Search for alternatives
        candidates = self.chromadb.search_recipes(
            query=query,
            n_results=20,
            filters=filters
        )
        
        # Filter based on constraints
        filtered_candidates = self._filter_candidates(
            candidates,
            request
        )
        
        if not filtered_candidates:
            return []
        
        # Generate replacement options using GPT-4
        prompt = Motor3PromptTemplate.generate_replacement_prompt(
            replacement_request=request.__dict__,
            candidate_recipes=filtered_candidates[:10],  # Top 10 candidates
            original_meal_nutrition=None  # Would include if available
        )
        
        # Get replacements from OpenAI
        replacements_json = await self.openai.find_meal_replacement(prompt)
        
        # For now, use the formatted replacements
        replacements = self._format_replacements(
            filtered_candidates,
            request
        )
        
        return replacements
    
    def _build_search_query(self, request: MealReplacementRequest) -> str:
        """Build search query for finding replacements"""
        query_parts = [request.meal_type]
        
        # Add preferences
        if request.alternative_ingredients:
            query_parts.extend(request.alternative_ingredients)
        
        # Add dietary restrictions
        if request.patient_data.pathologies:
            for pathology in request.patient_data.pathologies:
                if "diabetes" in pathology.lower():
                    query_parts.append("bajo indice glucemico")
                elif "hipertension" in pathology.lower():
                    query_parts.append("bajo sodio")
        
        return " ".join(query_parts)
    
    def _filter_candidates(
        self,
        candidates: List[Dict[str, Any]],
        request: MealReplacementRequest
    ) -> List[Dict[str, Any]]:
        """Filter candidates based on constraints"""
        filtered = []
        
        for candidate in candidates:
            content_lower = candidate['content'].lower()
            
            # Check avoided ingredients
            has_avoided = False
            for ingredient in request.avoid_ingredients:
                if ingredient.lower() in content_lower:
                    has_avoided = True
                    break
            
            if has_avoided:
                continue
            
            # Check allergies
            has_allergen = False
            for allergy in request.patient_data.allergies:
                if allergy.lower() in content_lower:
                    has_allergen = True
                    break
            
            if has_allergen:
                continue
            
            filtered.append(candidate)
        
        return filtered
    
    def _format_replacements(
        self,
        candidates: List[Dict[str, Any]],
        request: MealReplacementRequest
    ) -> List[Dict[str, Any]]:
        """Format replacement options for response"""
        replacements = []
        
        for candidate in candidates[:10]:  # Top 10 options
            replacement = {
                "recipe_name": candidate['metadata'].get('recipe_name', 'Unknown'),
                "category": candidate['metadata'].get('category', 'Unknown'),
                "description": candidate['content'][:300] + "...",
                "match_score": round(1 - candidate.get('distance', 0), 2),
                "nutritional_match": self._calculate_nutritional_match(candidate, request),
                "preparation_time": "15-30 minutos",  # Placeholder
                "difficulty": "Fácil",  # Placeholder
                "special_notes": self._generate_special_notes(candidate, request)
            }
            
            replacements.append(replacement)
        
        # Sort by match score
        replacements.sort(key=lambda x: x['match_score'], reverse=True)
        
        return replacements
    
    def _calculate_nutritional_match(self, candidate: Dict[str, Any], request: MealReplacementRequest) -> str:
        """Calculate how well the replacement matches nutritionally"""
        # Placeholder - in production would compare actual nutritional values
        if request.maintain_calories:
            return "Calorías similares"
        return "Apto para el plan"
    
    def _generate_special_notes(self, candidate: Dict[str, Any], request: MealReplacementRequest) -> List[str]:
        """Generate special notes for the replacement"""
        notes = []
        
        # Check if it addresses the replacement reason
        if "monoton" in request.reason.lower() or "variedad" in request.reason.lower():
            notes.append("Nueva opción para variar el menú")
        
        if "allergi" in request.reason.lower() or "alergia" in request.reason.lower():
            notes.append("Libre de alérgenos identificados")
        
        if "prefer" in request.reason.lower():
            notes.append("Alternativa según preferencias")
        
        return notes