"""
Motor 3: Meal replacement
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import logging

from api.models.patient import MealReplacementRequest
from api.services.chromadb_service import ChromaDBService
from api.services.meal_replacer import MealReplacerService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_chromadb_service() -> ChromaDBService:
    """Dependency to get ChromaDB service"""
    return ChromaDBService()


@router.post("/replace-meal")
async def replace_meal(
    request: MealReplacementRequest,
    chromadb: ChromaDBService = Depends(get_chromadb_service)
) -> Dict[str, Any]:
    """
    Replace a specific meal with alternatives
    
    This endpoint implements Motor 3: Quick meal replacements
    """
    try:
        logger.info(f"Processing meal replacement for patient: {request.patient_data.name}")
        
        # Initialize meal replacer service
        meal_replacer = MealReplacerService(chromadb)
        
        # Find suitable replacements
        replacements = await meal_replacer.find_replacements(request)
        
        if not replacements:
            raise HTTPException(
                status_code=404,
                detail="No suitable meal replacements found with the given constraints"
            )
        
        return {
            "status": "success",
            "patient_name": request.patient_data.name,
            "original_meal": request.meal_to_replace,
            "meal_type": request.meal_type,
            "reason": request.reason,
            "replacements": replacements[:5],  # Return top 5 options
            "nutritional_notes": generate_nutritional_notes(request, replacements[0]),
            "preparation_tips": generate_preparation_tips(request.meal_type)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error replacing meal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error replacing meal: {str(e)}")


from pydantic import BaseModel

class AlternativesRequest(BaseModel):
    meal_type: str
    category: str
    avoid_ingredients: List[str] = []
    economic_level: str = "standard"

@router.post("/find-alternatives")
async def find_meal_alternatives(
    request: AlternativesRequest,
    chromadb: ChromaDBService = Depends(get_chromadb_service)
) -> Dict[str, Any]:
    """
    Find alternative meals for a specific meal type and category
    
    Useful for quick searches without full patient context
    """
    try:
        # Validate meal type
        valid_meal_types = ['desayuno', 'almuerzo', 'merienda', 'cena', 'colacion']
        if request.meal_type.lower() not in valid_meal_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid meal type. Must be one of: {', '.join(valid_meal_types)}"
            )
        
        # Search for alternatives
        filters = {
            "meal_types": request.meal_type.lower(),
            "category": request.category.lower(),
            "economic_level": request.economic_level.lower()
        }
        
        # Build search query
        query = f"{request.meal_type} {request.category}"
        if request.avoid_ingredients:
            query += f" sin {' sin '.join(request.avoid_ingredients)}"
        
        results = chromadb.search_recipes(query, n_results=10, filters=filters)
        
        # Filter out recipes with avoided ingredients
        filtered_results = []
        for recipe in results:
            content_lower = recipe['content'].lower()
            if not any(ing.lower() in content_lower for ing in request.avoid_ingredients):
                filtered_results.append({
                    "recipe_name": recipe['metadata'].get('recipe_name', 'Unknown'),
                    "category": recipe['metadata'].get('category', 'Unknown'),
                    "preview": recipe['content'][:200] + "...",
                    "match_score": round(1 - recipe.get('distance', 0), 2)
                })
        
        return {
            "status": "success",
            "meal_type": request.meal_type,
            "category": request.category,
            "avoided_ingredients": request.avoid_ingredients,
            "alternatives_found": len(filtered_results),
            "alternatives": filtered_results[:10]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding alternatives: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error finding alternatives: {str(e)}")


@router.get("/meal-categories")
async def get_meal_categories() -> Dict[str, Any]:
    """Get available meal categories for replacements"""
    return {
        "status": "success",
        "meal_types": {
            "desayuno": ["desayuno_dulce", "desayuno_salado"],
            "almuerzo": ["pollo", "carne", "pescado_mariscos", "vegetariano", "cerdo", "ensaladas"],
            "cena": ["pollo", "carne", "pescado_mariscos", "vegetariano", "cerdo", "ensaladas"],
            "merienda": ["desayuno_dulce", "desayuno_salado", "colacion"],
            "colacion": ["colacion", "frutas", "lacteos"]
        },
        "economic_levels": ["economico", "standard", "premium"],
        "common_restrictions": [
            "sin gluten",
            "sin lactosa",
            "sin huevo",
            "sin frutos secos",
            "vegetariano",
            "vegano"
        ]
    }


def generate_nutritional_notes(
    request: MealReplacementRequest,
    replacement: Dict[str, Any]
) -> List[str]:
    """Generate nutritional notes for the replacement"""
    notes = []
    
    if request.maintain_calories:
        notes.append("Esta alternativa mantiene un valor calórico similar al original")
    
    # Add notes based on meal type
    if request.meal_type == "desayuno":
        notes.append("Incluye una fuente de proteína para mayor saciedad matutina")
    elif request.meal_type in ["almuerzo", "cena"]:
        notes.append("Combina con una porción de vegetales para completar el plato")
    elif request.meal_type == "colacion":
        notes.append("Ideal para consumir entre comidas principales")
    
    # Add notes for specific dietary needs
    if request.patient_data.pathologies:
        if "diabetes" in str(request.patient_data.pathologies).lower():
            notes.append("Opción apta para control glucémico")
        if "hipertension" in str(request.patient_data.pathologies).lower():
            notes.append("Preparación baja en sodio recomendada")
    
    return notes


def generate_preparation_tips(meal_type: str) -> List[str]:
    """Generate preparation tips based on meal type"""
    tips = {
        "desayuno": [
            "Prepare la noche anterior para ahorrar tiempo",
            "Acompañe con una infusión sin azúcar",
            "Incluya frutas frescas de temporada"
        ],
        "almuerzo": [
            "Cocine al vapor, horno o plancha para reducir grasas",
            "Prepare porciones extra para congelar",
            "Acompañe con agua o agua saborizada natural"
        ],
        "cena": [
            "Opte por preparaciones ligeras y de fácil digestión",
            "Cene al menos 2 horas antes de dormir",
            "Evite frituras en la noche"
        ],
        "merienda": [
            "Prepare porciones individuales para la semana",
            "Combine con una bebida caliente sin azúcar",
            "Ideal para media tarde"
        ],
        "colacion": [
            "Mantenga porciones listas en recipientes pequeños",
            "Ideal para llevar al trabajo o actividades",
            "Consuma entre comidas principales"
        ]
    }
    
    return tips.get(meal_type, ["Siga las indicaciones de su plan nutricional"])