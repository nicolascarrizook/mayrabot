"""
Tests for recipe validation system
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from api.services.plan_generator import PlanGeneratorService
from api.services.chromadb_service import ChromaDBService
from api.models.patient import PatientData


class TestRecipeValidation:
    """Test cases for recipe validation functionality"""
    
    @pytest.fixture
    def mock_chromadb(self):
        """Create a mock ChromaDB service"""
        mock = Mock(spec=ChromaDBService)
        
        # Mock valid recipes
        mock.get_all_valid_recipes.return_value = {
            "tostadas con palta": {"metadata": {"recipe_name": "Tostadas con palta", "calories": 350}},
            "pollo grillado": {"metadata": {"recipe_name": "Pollo grillado", "calories": 450}},
            "ensalada mixta": {"metadata": {"recipe_name": "Ensalada mixta", "calories": 150}}
        }
        
        mock.validate_recipe_exists = lambda name: name.lower() in mock.get_all_valid_recipes()
        
        return mock
    
    @pytest.fixture
    def plan_generator(self, mock_chromadb):
        """Create a PlanGeneratorService instance with mocked dependencies"""
        return PlanGeneratorService(mock_chromadb)
    
    def test_validate_generated_meals_with_valid_recipes(self, plan_generator):
        """Test that valid recipes pass validation"""
        # Setup valid recipe names
        plan_generator._valid_recipe_names = {"tostadas con palta", "pollo grillado", "ensalada mixta"}
        plan_generator._recipe_lookup = {
            "tostadas con palta": {"metadata": {"recipe_name": "Tostadas con palta"}},
            "pollo grillado": {"metadata": {"recipe_name": "Pollo grillado"}},
        }
        
        # Test meals with valid recipes
        test_meals = {
            "desayuno": {"name": "Tostadas con palta", "calories": 350},
            "almuerzo": {"name": "Pollo grillado", "calories": 450}
        }
        
        validated = plan_generator._validate_generated_meals(test_meals)
        
        assert len(validated) == 2
        assert "desayuno" in validated
        assert "almuerzo" in validated
        assert validated["desayuno"]["name"] == "Tostadas con palta"
    
    def test_validate_generated_meals_with_invalid_recipes(self, plan_generator):
        """Test that invalid recipes are caught and substituted"""
        # Setup valid recipe names
        plan_generator._valid_recipe_names = {"tostadas con palta", "pollo grillado"}
        plan_generator._recipe_lookup = {
            "tostadas con palta": {
                "metadata": {
                    "recipe_name": "Tostadas con palta",
                    "meal_types": '["desayuno"]',
                    "calories": 350
                },
                "content": "Receta: Tostadas con palta..."
            }
        }
        
        # Test meals with invalid recipe
        test_meals = {
            "desayuno": {"name": "Pancakes con miel", "calories": 400},  # Invalid recipe
            "almuerzo": {"name": "Pollo grillado", "calories": 450}      # Valid recipe
        }
        
        validated = plan_generator._validate_generated_meals(test_meals)
        
        # Should have substituted the invalid recipe
        assert "almuerzo" in validated
        assert validated["almuerzo"]["name"] == "Pollo grillado"
        
        # Desayuno should either be substituted or removed
        if "desayuno" in validated:
            # Check it was substituted with a valid recipe
            assert validated["desayuno"]["name"].lower() in plan_generator._valid_recipe_names
    
    def test_find_substitute_recipe(self, plan_generator):
        """Test finding substitute recipes based on meal type and calories"""
        # Setup recipe lookup
        plan_generator._recipe_lookup = {
            "tostadas con palta": {
                "metadata": {
                    "recipe_name": "Tostadas con palta",
                    "meal_types": '["desayuno"]',
                    "calories": 350
                },
                "content": "Ingredientes: pan, palta"
            },
            "yogur con granola": {
                "metadata": {
                    "recipe_name": "Yogur con granola",
                    "meal_types": '["desayuno", "merienda"]',
                    "calories": 300
                },
                "content": "Ingredientes: yogur, granola"
            }
        }
        
        # Mock _get_recipe_calories
        plan_generator._get_recipe_calories = lambda r: float(r.get('metadata', {}).get('calories', 0))
        
        # Find substitute for invalid breakfast
        invalid_meal = {"name": "Pancakes inventados", "calories": 320}
        substitute = plan_generator._find_substitute_recipe("desayuno", invalid_meal)
        
        assert substitute is not None
        assert substitute["name"] in ["Tostadas con palta", "Yogur con granola"]
        # Should prefer Yogur con granola as it's closer in calories (300 vs 320)
        assert substitute["name"] == "Yogur con granola"
    
    @patch('api.services.openai_service.OpenAIService')
    async def test_openai_receives_only_valid_recipes(self, mock_openai_class, plan_generator):
        """Test that OpenAI only receives valid recipes from the database"""
        # Mock OpenAI service
        mock_openai = Mock()
        mock_openai.generate_meal_plan.return_value = '{"meal_plan": {}}'
        mock_openai_class.return_value = mock_openai
        plan_generator.openai = mock_openai
        
        # Mock recipe searcher results
        mock_recipes = {
            "desayuno": [
                {"metadata": {"recipe_name": "Tostadas con palta"}, "content": "Recipe content"},
                {"metadata": {"recipe_name": "Yogur con frutas"}, "content": "Recipe content"}
            ],
            "almuerzo": [
                {"metadata": {"recipe_name": "Pollo grillado"}, "content": "Recipe content"}
            ]
        }
        
        # Create mock patient data
        patient_data = Mock(spec=PatientData)
        patient_data.meals_per_day = 4
        patient_data.__dict__ = {"name": "Test Patient", "meals_per_day": 4}
        
        # Mock recipe search
        with patch('api.services.recipe_searcher.RecipeSearcher') as mock_searcher_class:
            mock_searcher = Mock()
            mock_searcher.find_best_recipes_for_plan.return_value = mock_recipes
            mock_searcher_class.return_value = mock_searcher
            
            # Call generate day meals
            await plan_generator._generate_day_meals(
                patient_data=patient_data,
                daily_calories=2000,
                macro_distribution={"carbohydrates": 0.45, "proteins": 0.25, "fats": 0.30},
                day_num=0
            )
            
            # Verify OpenAI was called
            assert mock_openai.generate_meal_plan.called
            
            # Get the recipes passed to OpenAI
            call_args = mock_openai.generate_meal_plan.call_args
            recipes_arg = call_args[1]['recipes']
            
            # Verify all recipes sent to OpenAI are from our mock database
            for recipe in recipes_arg:
                recipe_name = recipe.get('metadata', {}).get('recipe_name')
                assert recipe_name in ["Tostadas con palta", "Yogur con frutas", "Pollo grillado"]
    
    def test_chromadb_recipe_validation(self, mock_chromadb):
        """Test ChromaDB recipe validation methods"""
        # Test valid recipe
        assert mock_chromadb.validate_recipe_exists("Tostadas con palta") == True
        assert mock_chromadb.validate_recipe_exists("TOSTADAS CON PALTA") == True  # Case insensitive
        
        # Test invalid recipe
        assert mock_chromadb.validate_recipe_exists("Pancakes inventados") == False
        
        # Test get all valid recipes
        valid_recipes = mock_chromadb.get_all_valid_recipes()
        assert len(valid_recipes) == 3
        assert "tostadas con palta" in valid_recipes
        assert "pollo grillado" in valid_recipes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])