"""
Test script for data processing modules
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_processor.docx_processor import DocxProcessor
from data_processor.recipe_extractor import RecipeExtractor


def test_docx_processor():
    """Test basic DOCX processing"""
    print("\n=== Testing DOCX Processor ===")
    
    # Test with almuerzoscena.docx
    file_path = Path("data/almuerzoscena.docx")
    if file_path.exists():
        processor = DocxProcessor(str(file_path))
        
        # Extract tables
        tables = processor.extract_tables()
        print(f"Found {len(tables)} tables")
        
        if tables:
            # Show first table info
            first_table = tables[0]
            print(f"First table headers: {first_table.headers}")
            print(f"First table has {len(first_table.rows)} rows")
            
            # Show sample row
            if first_table.rows:
                print(f"Sample row: {first_table.rows[0]}")
    else:
        print(f"File not found: {file_path}")


def test_recipe_extractor():
    """Test recipe extraction"""
    print("\n=== Testing Recipe Extractor ===")
    
    extractor = RecipeExtractor()
    
    # Test lunch/dinner extraction
    file_path = Path("data/almuerzoscena.docx")
    if file_path.exists():
        recipes = extractor.extract_from_almuerzos_cena(str(file_path))
        print(f"Extracted {len(recipes)} lunch/dinner recipes")
        
        if recipes:
            # Show first recipe
            first_recipe = recipes[0]
            print(f"\nFirst recipe:")
            print(f"  Name: {first_recipe.name}")
            print(f"  Category: {first_recipe.category.value}")
            print(f"  Meal types: {[mt.value for mt in first_recipe.meal_types]}")
            print(f"  Ingredients: {len(first_recipe.ingredients)}")
            
            if first_recipe.ingredients:
                print("  Sample ingredients:")
                for ing in first_recipe.ingredients[:3]:
                    print(f"    - {ing.name}: {ing.quantity} {ing.unit}")
    
    # Test breakfast extraction
    file_path = Path("data/desayunos.docx")
    if file_path.exists():
        recipes = extractor.extract_from_desayunos(str(file_path))
        print(f"\nExtracted {len(recipes)} breakfast/snack recipes")


def test_preparations():
    """Test recipe preparations extraction"""
    print("\n=== Testing Preparations Extraction ===")
    
    extractor = RecipeExtractor()
    file_path = Path("data/recetas.docx")
    
    if file_path.exists():
        preparations = extractor.extract_from_recetas(str(file_path))
        print(f"Extracted {len(preparations)} recipe preparations")
        
        if preparations:
            # Show first preparation
            first_key = list(preparations.keys())[0]
            print(f"\nFirst preparation: {first_key}")
            print(f"Content preview: {preparations[first_key][:200]}...")


def test_equivalences():
    """Test equivalences extraction"""
    print("\n=== Testing Equivalences Extraction ===")
    
    extractor = RecipeExtractor()
    file_path = Path("data/desayunosequivalentes.docx")
    
    if file_path.exists():
        equivalences = extractor.extract_equivalences(str(file_path))
        print(f"Extracted equivalences for {len(equivalences)} categories")
        
        for category, items in equivalences.items():
            print(f"  {category}: {len(items)} items")


if __name__ == "__main__":
    print("Testing Data Processing Modules")
    print("==============================")
    
    test_docx_processor()
    test_recipe_extractor()
    test_preparations()
    test_equivalences()
    
    print("\n✅ Testing completed!")
    print("\nTo load data into ChromaDB, run:")
    print("  python data_processor/load_to_chromadb.py")