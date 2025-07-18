"""
ChromaDB Loader Module

This module loads processed recipes into ChromaDB for semantic search
and retrieval in the nutrition planning system.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_processor.recipe_extractor import RecipeExtractor, Recipe, RecipeCategory, MealType

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChromaDBLoader:
    """Handles loading recipes into ChromaDB"""
    
    def __init__(self, persist_directory: str = None, collection_name: str = None):
        """
        Initialize ChromaDB loader
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the collection to create/use
        """
        self.persist_directory = persist_directory or os.getenv(
            "CHROMA_PERSIST_DIRECTORY", 
            "./chroma_db"
        )
        self.collection_name = collection_name or os.getenv(
            "CHROMA_COLLECTION_NAME",
            "nutrition_recipes"
        )
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model="text-embedding-3-small"
        )
        
        # Text splitter for long content
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Get or create collection
        self._setup_collection()
    
    def _setup_collection(self):
        """Setup ChromaDB collection"""
        try:
            # Delete existing collection if it exists (for fresh start)
            try:
                self.client.delete_collection(self.collection_name)
                logger.info(f"Deleted existing collection: {self.collection_name}")
            except:
                pass
            
            # Create new collection
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Nutrition recipes for meal planning"}
            )
            logger.info(f"Created collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Error setting up collection: {e}")
            raise
    
    def recipe_to_document(self, recipe: Recipe) -> List[Document]:
        """
        Convert a Recipe object to Langchain Documents
        
        Args:
            recipe: Recipe object
            
        Returns:
            List of Document objects (may be split if content is long)
        """
        # Create recipe content
        content_parts = [
            f"Receta: {recipe.name}",
            f"Categoría: {recipe.category.value}",
            f"Tipos de comida: {', '.join([mt.value for mt in recipe.meal_types])}",
            f"Porciones: {recipe.portions}",
            f"Nivel económico: {recipe.economic_level}",
            ""
        ]
        
        # Add ingredients
        if recipe.ingredients:
            content_parts.append("Ingredientes:")
            for ing in recipe.ingredients:
                ing_text = f"- {ing.name}: {ing.quantity} {ing.unit}"
                if ing.alternatives:
                    ing_text += f" (alternativas: {', '.join(ing.alternatives)})"
                content_parts.append(ing_text)
            content_parts.append("")
        
        # Add preparation
        if recipe.preparation:
            content_parts.append("Preparación:")
            content_parts.append(recipe.preparation)
            content_parts.append("")
        
        # Add notes
        if recipe.notes:
            content_parts.append(f"Notas: {recipe.notes}")
        
        # Add calories if available
        if recipe.calories:
            content_parts.append(f"Calorías: {recipe.calories} kcal")
        
        # Join content
        full_content = "\n".join(content_parts)
        
        # Create metadata
        metadata = {
            "recipe_name": recipe.name,
            "category": recipe.category.value,
            "meal_types": json.dumps([mt.value for mt in recipe.meal_types]),
            "economic_level": recipe.economic_level,
            "has_preparation": bool(recipe.preparation),
            "ingredient_count": len(recipe.ingredients),
            "main_ingredients": json.dumps([ing.name for ing in recipe.ingredients[:5]]),
        }
        
        if recipe.calories:
            metadata["calories"] = recipe.calories
        
        # Create documents (split if necessary)
        if len(full_content) > 1000:
            # Split long content
            splits = self.text_splitter.split_text(full_content)
            documents = []
            for i, split in enumerate(splits):
                doc_metadata = metadata.copy()
                doc_metadata["chunk_index"] = i
                doc_metadata["total_chunks"] = len(splits)
                documents.append(Document(page_content=split, metadata=doc_metadata))
            return documents
        else:
            # Single document
            return [Document(page_content=full_content, metadata=metadata)]
    
    def load_recipes(self, recipes: List[Recipe]) -> None:
        """
        Load recipes into ChromaDB
        
        Args:
            recipes: List of Recipe objects
        """
        logger.info(f"Loading {len(recipes)} recipes into ChromaDB")
        
        all_documents = []
        for recipe in recipes:
            try:
                documents = self.recipe_to_document(recipe)
                all_documents.extend(documents)
            except Exception as e:
                logger.error(f"Error converting recipe {recipe.name}: {e}")
        
        if all_documents:
            # Prepare for ChromaDB
            texts = [doc.page_content for doc in all_documents]
            metadatas = [doc.metadata for doc in all_documents]
            ids = [f"doc_{i}" for i in range(len(all_documents))]
            
            # Generate embeddings
            logger.info("Generating embeddings...")
            embeddings_list = self.embeddings.embed_documents(texts)
            
            # Add to collection
            logger.info("Adding documents to collection...")
            self.collection.add(
                embeddings=embeddings_list,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Successfully loaded {len(all_documents)} documents")
    
    def load_equivalences(self, equivalences: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Load caloric equivalences into ChromaDB
        
        Args:
            equivalences: Dictionary of equivalences by category
        """
        logger.info(f"Loading equivalences for {len(equivalences)} categories")
        
        documents = []
        
        for category, items in equivalences.items():
            # Create a document for each equivalence category
            content_parts = [
                f"Tabla de Equivalencias: {category.title()}",
                "",
                "Opciones equivalentes:"
            ]
            
            for item in items:
                item_text = " - ".join([f"{k}: {v}" for k, v in item.items() if v])
                content_parts.append(f"- {item_text}")
            
            content = "\n".join(content_parts)
            
            metadata = {
                "type": "equivalence_table",
                "category": category,
                "item_count": len(items)
            }
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        if documents:
            # Prepare for ChromaDB
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            ids = [f"equiv_{i}" for i in range(len(documents))]
            
            # Generate embeddings
            embeddings_list = self.embeddings.embed_documents(texts)
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings_list,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Successfully loaded {len(documents)} equivalence documents")
    
    def verify_collection(self) -> Dict[str, Any]:
        """Verify collection contents"""
        count = self.collection.count()
        
        # Get sample documents
        sample = self.collection.get(limit=5)
        
        # Get category distribution
        all_docs = self.collection.get()
        categories = {}
        
        if all_docs and 'metadatas' in all_docs:
            for metadata in all_docs['metadatas']:
                if metadata and 'category' in metadata:
                    cat = metadata['category']
                    categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_documents": count,
            "categories": categories,
            "sample_documents": sample
        }


def main():
    """Main function to load all recipes into ChromaDB"""
    try:
        # Initialize extractor and loader
        extractor = RecipeExtractor()
        loader = ChromaDBLoader()
        
        # Paths to DOCX files
        data_dir = Path("data")
        almuerzos_path = data_dir / os.getenv("DOCX_ALMUERZOS_CENA", "almuerzoscena.docx")
        desayunos_path = data_dir / os.getenv("DOCX_DESAYUNOS", "desayunos.docx")
        equivalentes_path = data_dir / os.getenv("DOCX_EQUIVALENTES", "desayunosequivalentes.docx")
        recetas_path = data_dir / os.getenv("DOCX_RECETAS", "recetas.docx")
        
        all_recipes = []
        
        # Extract lunch/dinner recipes
        if almuerzos_path.exists():
            logger.info(f"Processing {almuerzos_path}")
            lunch_dinner_recipes = extractor.extract_from_almuerzos_cena(str(almuerzos_path))
            all_recipes.extend(lunch_dinner_recipes)
        else:
            logger.warning(f"File not found: {almuerzos_path}")
        
        # Extract breakfast/snack recipes
        if desayunos_path.exists():
            logger.info(f"Processing {desayunos_path}")
            breakfast_recipes = extractor.extract_from_desayunos(str(desayunos_path))
            all_recipes.extend(breakfast_recipes)
        else:
            logger.warning(f"File not found: {desayunos_path}")
        
        # Extract detailed preparations
        if recetas_path.exists():
            logger.info(f"Processing {recetas_path}")
            preparations = extractor.extract_from_recetas(str(recetas_path))
            
            # Merge preparations with recipes
            all_recipes = extractor.merge_with_preparations(all_recipes, preparations)
        else:
            logger.warning(f"File not found: {recetas_path}")
        
        # Load recipes into ChromaDB
        if all_recipes:
            loader.load_recipes(all_recipes)
            logger.info(f"Loaded {len(all_recipes)} recipes into ChromaDB")
        
        # Extract and load equivalences
        if equivalentes_path.exists():
            logger.info(f"Processing {equivalentes_path}")
            equivalences = extractor.extract_equivalences(str(equivalentes_path))
            loader.load_equivalences(equivalences)
        else:
            logger.warning(f"File not found: {equivalentes_path}")
        
        # Verify collection
        stats = loader.verify_collection()
        logger.info(f"Collection statistics: {json.dumps(stats, indent=2)}")
        
        logger.info("ChromaDB loading completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()