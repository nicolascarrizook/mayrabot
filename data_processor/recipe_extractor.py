"""
Recipe Extractor Module

This module extracts and structures recipe information from DOCX files,
specifically designed for the nutrition planning system.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .docx_processor import DocxProcessor, TableData

logger = logging.getLogger(__name__)


class RecipeCategory(Enum):
    """Recipe categories based on main protein/type"""
    POLLO = "pollo"
    CARNE = "carne"
    VEGETARIANO = "vegetariano"
    CERDO = "cerdo"
    PESCADO_MARISCOS = "pescado_mariscos"
    ENSALADAS = "ensaladas"
    DESAYUNO_DULCE = "desayuno_dulce"
    DESAYUNO_SALADO = "desayuno_salado"
    COLACION = "colacion"
    OTROS = "otros"


class MealType(Enum):
    """Meal types in the day"""
    DESAYUNO = "desayuno"
    ALMUERZO = "almuerzo"
    CENA = "cena"
    MERIENDA = "merienda"
    COLACION = "colacion"


@dataclass
class Ingredient:
    """Represents a single ingredient with quantity"""
    name: str
    quantity: float
    unit: str
    alternatives: List[str] = field(default_factory=list)


@dataclass
class Recipe:
    """Complete recipe representation"""
    name: str
    category: RecipeCategory
    meal_types: List[MealType]
    ingredients: List[Ingredient]
    preparation: str
    calories: Optional[float] = None
    portions: int = 1
    economic_level: str = "standard"
    notes: str = ""
    equivalences: Dict[str, Any] = field(default_factory=dict)


class RecipeExtractor:
    """Extracts and structures recipes from DOCX files"""
    
    # Regex patterns for parsing
    QUANTITY_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*(gr?|grs?|gramos?|cc|ml|unidad|unidades|cda|cdita|taza|pizca)?', re.IGNORECASE)
    CALORIE_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*(?:kcal|cal|calorías?)', re.IGNORECASE)
    
    def __init__(self):
        self.recipes: List[Recipe] = []
        
    def extract_from_almuerzos_cena(self, file_path: str) -> List[Recipe]:
        """Extract lunch and dinner recipes from the DOCX file"""
        processor = DocxProcessor(file_path)
        tables = processor.extract_tables()
        recipes = []
        
        for table in tables:
            # Process each table based on its structure
            recipes.extend(self._process_meal_table(table))
        
        logger.info(f"Extracted {len(recipes)} lunch/dinner recipes")
        return recipes
    
    def extract_from_desayunos(self, file_path: str) -> List[Recipe]:
        """Extract breakfast and snack recipes from the DOCX file"""
        processor = DocxProcessor(file_path)
        tables = processor.extract_tables()
        sections = processor.extract_sections()
        recipes = []
        
        # Process tables
        for table in tables:
            table_recipes = self._process_breakfast_table(table)
            recipes.extend(table_recipes)
        
        # Process sections for additional recipes
        for section_name, content in sections.items():
            if any(keyword in section_name.lower() for keyword in ['dulce', 'salado', 'colación']):
                section_recipes = self._extract_recipes_from_text(content, section_name)
                recipes.extend(section_recipes)
        
        logger.info(f"Extracted {len(recipes)} breakfast/snack recipes")
        return recipes
    
    def extract_from_recetas(self, file_path: str) -> Dict[str, str]:
        """Extract detailed recipe preparations from the DOCX file"""
        processor = DocxProcessor(file_path)
        sections = processor.extract_sections()
        preparations = {}
        
        for section_name, content in sections.items():
            # Each section might be a recipe name
            if content:
                preparation_text = '\n'.join(content)
                preparations[section_name] = preparation_text
        
        logger.info(f"Extracted {len(preparations)} recipe preparations")
        return preparations
    
    def extract_equivalences(self, file_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract caloric equivalences from the DOCX file"""
        processor = DocxProcessor(file_path)
        tables = processor.extract_tables()
        equivalences = {}
        
        for table in tables:
            table_dict = processor.get_table_as_dict(table)
            
            # Group equivalences by category
            for row in table_dict:
                category = self._determine_equivalence_category(row)
                if category not in equivalences:
                    equivalences[category] = []
                equivalences[category].append(row)
        
        logger.info(f"Extracted equivalences for {len(equivalences)} categories")
        return equivalences
    
    def _process_meal_table(self, table: TableData) -> List[Recipe]:
        """Process a table containing meal recipes"""
        recipes = []
        
        # Determine category from headers
        category = self._determine_category_from_headers(table.headers)
        
        for row in table.rows:
            recipe = self._parse_meal_row(row, table.headers, category)
            if recipe:
                recipes.append(recipe)
        
        return recipes
    
    def _process_breakfast_table(self, table: TableData) -> List[Recipe]:
        """Process a table containing breakfast/snack recipes"""
        recipes = []
        
        for row in table.rows:
            recipe = self._parse_breakfast_row(row, table.headers)
            if recipe:
                recipes.append(recipe)
        
        return recipes
    
    def _parse_meal_row(self, row: List[str], headers: List[str], category: RecipeCategory) -> Optional[Recipe]:
        """Parse a single row into a Recipe object"""
        try:
            # Create a dictionary for easier access
            row_dict = {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
            
            # Extract recipe name (usually first column)
            recipe_name = row[0].strip() if row else ""
            if not recipe_name:
                return None
            
            # Extract ingredients
            ingredients = []
            for i in range(1, len(row)):
                if i < len(headers) and row[i].strip():
                    ingredient = self._parse_ingredient(row[i], headers[i])
                    if ingredient:
                        ingredients.append(ingredient)
            
            # Determine meal types
            meal_types = [MealType.ALMUERZO, MealType.CENA]
            
            recipe = Recipe(
                name=recipe_name,
                category=category,
                meal_types=meal_types,
                ingredients=ingredients,
                preparation="",  # Will be filled from recetas.docx
                economic_level=self._extract_economic_level(recipe_name)
            )
            
            return recipe
            
        except Exception as e:
            logger.error(f"Error parsing meal row: {e}")
            return None
    
    def _parse_breakfast_row(self, row: List[str], headers: List[str]) -> Optional[Recipe]:
        """Parse a breakfast/snack row into a Recipe object"""
        try:
            recipe_name = row[0].strip() if row else ""
            if not recipe_name:
                return None
            
            # Determine category based on content
            category = self._determine_breakfast_category(recipe_name, row)
            
            # Extract ingredients
            ingredients = []
            for i in range(1, len(row)):
                if i < len(headers) and row[i].strip():
                    ingredient = self._parse_ingredient(row[i], headers[i])
                    if ingredient:
                        ingredients.append(ingredient)
            
            # Determine meal types
            if category == RecipeCategory.COLACION:
                meal_types = [MealType.COLACION]
            else:
                meal_types = [MealType.DESAYUNO, MealType.MERIENDA]
            
            recipe = Recipe(
                name=recipe_name,
                category=category,
                meal_types=meal_types,
                ingredients=ingredients,
                preparation=""
            )
            
            return recipe
            
        except Exception as e:
            logger.error(f"Error parsing breakfast row: {e}")
            return None
    
    def _parse_ingredient(self, text: str, header: str = "") -> Optional[Ingredient]:
        """Parse ingredient text into an Ingredient object"""
        if not text.strip():
            return None
        
        # Try to extract quantity and unit
        match = self.QUANTITY_PATTERN.search(text)
        
        if match:
            quantity = float(match.group(1))
            unit = match.group(2) or "unidad"
            # Remove the quantity part to get the ingredient name
            name = self.QUANTITY_PATTERN.sub('', text).strip()
        else:
            # No quantity found, use header as ingredient name if available
            quantity = 0
            unit = "al gusto"
            name = header if header else text.strip()
        
        # Clean up the name
        name = name.strip('- ,.')
        
        if name:
            return Ingredient(
                name=name,
                quantity=quantity,
                unit=unit.lower()
            )
        
        return None
    
    def _determine_category_from_headers(self, headers: List[str]) -> RecipeCategory:
        """Determine recipe category from table headers"""
        headers_text = ' '.join(headers).lower()
        
        if 'pollo' in headers_text:
            return RecipeCategory.POLLO
        elif 'carne' in headers_text or 'vacuna' in headers_text:
            return RecipeCategory.CARNE
        elif 'vegetariano' in headers_text or 'vegetal' in headers_text:
            return RecipeCategory.VEGETARIANO
        elif 'cerdo' in headers_text:
            return RecipeCategory.CERDO
        elif 'pescado' in headers_text or 'mariscos' in headers_text:
            return RecipeCategory.PESCADO_MARISCOS
        elif 'ensalada' in headers_text:
            return RecipeCategory.ENSALADAS
        else:
            return RecipeCategory.OTROS
    
    def _determine_breakfast_category(self, name: str, row: List[str]) -> RecipeCategory:
        """Determine breakfast recipe category"""
        text = (name + ' '.join(row)).lower()
        
        if any(word in text for word in ['colación', 'snack']):
            return RecipeCategory.COLACION
        elif any(word in text for word in ['dulce', 'mermelada', 'miel', 'azúcar']):
            return RecipeCategory.DESAYUNO_DULCE
        elif any(word in text for word in ['salado', 'queso', 'jamón', 'huevo']):
            return RecipeCategory.DESAYUNO_SALADO
        else:
            return RecipeCategory.DESAYUNO_DULCE  # Default
    
    def _determine_equivalence_category(self, row: Dict[str, Any]) -> str:
        """Determine equivalence category from row data"""
        # Look for category indicators in the row
        row_text = ' '.join(str(v) for v in row.values()).lower()
        
        if 'lácteo' in row_text or 'leche' in row_text:
            return 'lacteos'
        elif 'fruta' in row_text:
            return 'frutas'
        elif 'cereal' in row_text or 'pan' in row_text:
            return 'cereales'
        elif 'proteína' in row_text or 'carne' in row_text:
            return 'proteinas'
        elif 'grasa' in row_text or 'aceite' in row_text:
            return 'grasas'
        else:
            return 'otros'
    
    def _extract_recipes_from_text(self, content: List[str], section_name: str) -> List[Recipe]:
        """Extract recipes from text content"""
        recipes = []
        current_recipe = None
        
        for line in content:
            # Check if line starts a new recipe
            if self._is_recipe_title(line):
                if current_recipe:
                    recipes.append(current_recipe)
                
                category = self._determine_breakfast_category(line, [section_name])
                current_recipe = Recipe(
                    name=line.strip(),
                    category=category,
                    meal_types=[MealType.DESAYUNO, MealType.MERIENDA],
                    ingredients=[],
                    preparation=""
                )
            elif current_recipe:
                # Try to parse as ingredient
                ingredient = self._parse_ingredient(line)
                if ingredient:
                    current_recipe.ingredients.append(ingredient)
        
        # Add last recipe
        if current_recipe:
            recipes.append(current_recipe)
        
        return recipes
    
    def _is_recipe_title(self, text: str) -> bool:
        """Check if text line is likely a recipe title"""
        # Recipe titles are usually short and don't contain quantities
        if len(text) > 50:
            return False
        if self.QUANTITY_PATTERN.search(text):
            return False
        # Check for title indicators
        return text.strip() and not text.startswith('-')
    
    def _extract_economic_level(self, text: str) -> str:
        """Extract economic level from recipe name or content"""
        text_lower = text.lower()
        
        if 'económico' in text_lower or 'economico' in text_lower:
            return 'economico'
        elif 'premium' in text_lower or 'gourmet' in text_lower:
            return 'premium'
        else:
            return 'standard'
    
    def merge_with_preparations(self, recipes: List[Recipe], preparations: Dict[str, str]) -> List[Recipe]:
        """Merge recipes with their detailed preparations"""
        for recipe in recipes:
            # Try to find matching preparation
            recipe_name_lower = recipe.name.lower()
            
            for prep_name, prep_text in preparations.items():
                if recipe_name_lower in prep_name.lower() or prep_name.lower() in recipe_name_lower:
                    recipe.preparation = prep_text
                    break
            
            # Also look for partial matches
            if not recipe.preparation:
                for prep_name, prep_text in preparations.items():
                    # Check if key words match
                    recipe_words = set(recipe_name_lower.split())
                    prep_words = set(prep_name.lower().split())
                    
                    if len(recipe_words & prep_words) >= 2:  # At least 2 words match
                        recipe.preparation = prep_text
                        break
        
        return recipes