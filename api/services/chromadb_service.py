"""
ChromaDB Service for recipe retrieval
"""

import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from api.config import settings

logger = logging.getLogger(__name__)


class ChromaDBService:
    """Service for interacting with ChromaDB"""
    
    def __init__(self):
        """Initialize ChromaDB client and collection"""
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        try:
            self.collection = self.client.get_collection(
                name=settings.chroma_collection_name
            )
            logger.info(f"Found existing collection: {settings.chroma_collection_name}")
        except ValueError:
            # La colección no existe, crearla vacía
            logger.warning(f"Collection {settings.chroma_collection_name} not found, creating new one")
            self.collection = self.client.create_collection(
                name=settings.chroma_collection_name,
                embedding_function=OpenAIEmbeddings(
                    openai_api_key=settings.openai_api_key,
                    model="text-embedding-3-small"
                )
            )
        
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key,
            model="text-embedding-3-small"
        )
        
        logger.info(f"ChromaDB service initialized with {self.collection.count()} documents")
    
    def search_recipes(
        self,
        query: str,
        n_results: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for recipes using semantic search
        
        Args:
            query: Search query
            n_results: Number of results to return
            filters: Optional filters (e.g., category, meal_type)
            
        Returns:
            List of recipe documents with metadata
        """
        try:
            # Generate embedding for query
            query_embedding = self.embeddings.embed_query(query)
            
            # Prepare where clause - simplified approach
            where_clause = None
            if filters:
                # Only use simple equality filters that ChromaDB supports
                if 'category' in filters:
                    where_clause = {"category": filters['category']}
                elif 'economic_level' in filters:
                    where_clause = {"economic_level": filters['economic_level']}
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause if where_clause else None
            )
            
            # Format results
            recipes = []
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]
                
                # Post-process filtering for meal_types if needed
                if filters and 'meal_types' in filters:
                    meal_types_str = metadata.get('meal_types', '[]')
                    try:
                        import json
                        meal_types_list = json.loads(meal_types_str)
                        if filters['meal_types'] not in meal_types_list:
                            continue
                    except:
                        continue
                
                recipe = {
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': metadata,
                    'distance': results['distances'][0][i] if 'distances' in results else None
                }
                recipes.append(recipe)
            
            logger.info(f"Found {len(recipes)} recipes for query: {query}")
            return recipes
            
        except Exception as e:
            logger.error(f"Error searching recipes: {e}")
            raise
    
    def get_recipes_by_category(
        self,
        category: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recipes by category
        
        Args:
            category: Recipe category
            limit: Maximum number of results
            
        Returns:
            List of recipes in the category
        """
        try:
            results = self.collection.get(
                where={"category": category},
                limit=limit
            )
            
            recipes = []
            for i in range(len(results['ids'])):
                recipe = {
                    'id': results['ids'][i],
                    'content': results['documents'][i],
                    'metadata': results['metadatas'][i]
                }
                recipes.append(recipe)
            
            return recipes
            
        except Exception as e:
            logger.error(f"Error getting recipes by category: {e}")
            raise
    
    def get_equivalences(self, category: str) -> Optional[Dict[str, Any]]:
        """
        Get equivalence table for a category
        
        Args:
            category: Equivalence category (lacteos, frutas, etc.)
            
        Returns:
            Equivalence table data or None
        """
        try:
            results = self.collection.get(
                where={
                    "type": "equivalence_table",
                    "category": category
                },
                limit=1
            )
            
            if results['ids']:
                return {
                    'id': results['ids'][0],
                    'content': results['documents'][0],
                    'metadata': results['metadatas'][0]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting equivalences: {e}")
            raise
    
    def find_similar_recipes(
        self,
        recipe_name: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find recipes similar to a given recipe
        
        Args:
            recipe_name: Name of the recipe to find similar ones
            n_results: Number of similar recipes to return
            
        Returns:
            List of similar recipes
        """
        try:
            # First, find the recipe
            original = self.collection.get(
                where={"recipe_name": recipe_name},
                limit=1
            )
            
            if not original['ids']:
                logger.warning(f"Recipe not found: {recipe_name}")
                return []
            
            # Search for similar recipes using the recipe content
            return self.search_recipes(
                original['documents'][0],
                n_results=n_results + 1  # Add 1 to exclude the original
            )[1:]  # Skip the first result (the original recipe)
            
        except Exception as e:
            logger.error(f"Error finding similar recipes: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            all_docs = self.collection.get()
            
            categories = {}
            meal_types = {}
            
            for metadata in all_docs['metadatas']:
                # Count categories
                cat = metadata.get('category', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1
                
                # Count meal types
                if 'meal_types' in metadata:
                    import json
                    types = json.loads(metadata['meal_types'])
                    for meal_type in types:
                        meal_types[meal_type] = meal_types.get(meal_type, 0) + 1
            
            return {
                'total_documents': len(all_docs['ids']),
                'categories': categories,
                'meal_types': meal_types
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            raise