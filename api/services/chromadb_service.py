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
        
        # Initialize cache for frequently accessed data
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache
        self._last_cache_clear = None
        
        # Initialize recipe validation cache
        self._valid_recipes_cache = None
        self._cache_timestamp = None
        
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
    
    def batch_search_recipes(
        self,
        meal_requirements: Dict[str, float],
        patient_restrictions: List[str],
        preferences: List[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Optimized batch search for multiple meals at once
        
        Args:
            meal_requirements: Dict of meal_type -> target_calories
            patient_restrictions: List of ingredients to avoid
            preferences: List of preferred ingredients
            
        Returns:
            Dict of meal_type -> list of suitable recipes
        """
        import time
        from concurrent.futures import ThreadPoolExecutor
        
        # Clear cache if needed
        current_time = time.time()
        if self._last_cache_clear is None or (current_time - self._last_cache_clear) > self._cache_ttl:
            self._cache.clear()
            self._last_cache_clear = current_time
        
        results = {}
        
        # Create search tasks
        def search_for_meal(meal_type: str, target_calories: float):
            cache_key = f"{meal_type}_{target_calories}_{hash(tuple(patient_restrictions))}"
            
            # Check cache first
            if cache_key in self._cache:
                logger.info(f"Cache hit for {meal_type}")
                return meal_type, self._cache[cache_key]
            
            # Search with broader initial criteria
            recipes = self.search_recipes(
                query=meal_type,
                n_results=30,  # Get more results for better filtering
                filters={'meal_type': meal_type}
            )
            
            # Filter by calories and restrictions
            suitable_recipes = []
            min_cal = target_calories * 0.8
            max_cal = target_calories * 1.2
            
            for recipe in recipes:
                # Get calories
                calories = self._extract_calories(recipe)
                if not (min_cal <= calories <= max_cal):
                    continue
                
                # Check restrictions
                if self._has_restrictions(recipe, patient_restrictions):
                    continue
                
                # Score by preferences
                score = self._score_by_preferences(recipe, preferences or [])
                recipe['preference_score'] = score
                
                suitable_recipes.append(recipe)
            
            # Sort by preference score
            suitable_recipes.sort(key=lambda x: x.get('preference_score', 0), reverse=True)
            
            # Cache results
            self._cache[cache_key] = suitable_recipes[:10]
            
            return meal_type, suitable_recipes[:10]
        
        # Execute searches in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for meal_type, calories in meal_requirements.items():
                future = executor.submit(search_for_meal, meal_type, calories)
                futures.append(future)
            
            for future in futures:
                meal_type, recipes = future.result()
                results[meal_type] = recipes
        
        return results
    
    def _extract_calories(self, recipe: Dict[str, Any]) -> float:
        """Extract calories from recipe with multiple fallbacks"""
        # Direct field
        if 'calories' in recipe:
            return float(recipe['calories'])
        
        # From metadata
        metadata = recipe.get('metadata', {})
        if 'calories' in metadata:
            return float(metadata['calories'])
        if 'calorias' in metadata:
            return float(metadata['calorias'])
        
        # From content parsing (last resort)
        content = recipe.get('content', '')
        import re
        cal_match = re.search(r'(\d+)\s*(?:kcal|calorias|calorías)', content, re.IGNORECASE)
        if cal_match:
            return float(cal_match.group(1))
        
        return 0
    
    def _has_restrictions(self, recipe: Dict[str, Any], restrictions: List[str]) -> bool:
        """Check if recipe contains restricted ingredients"""
        if not restrictions:
            return False
        
        # Get all text to search
        search_text = []
        search_text.append(recipe.get('content', ''))
        search_text.append(str(recipe.get('metadata', {})))
        
        combined_text = ' '.join(search_text).lower()
        
        for restriction in restrictions:
            if restriction.lower() in combined_text:
                return True
        
        return False
    
    def _score_by_preferences(self, recipe: Dict[str, Any], preferences: List[str]) -> float:
        """Score recipe based on patient preferences"""
        if not preferences:
            return 0
        
        score = 0
        search_text = []
        search_text.append(recipe.get('content', ''))
        search_text.append(recipe.get('name', ''))
        search_text.append(str(recipe.get('metadata', {})))
        
        combined_text = ' '.join(search_text).lower()
        
        for preference in preferences:
            if preference.lower() in combined_text:
                score += 10
        
        return score
    
    def get_all_valid_recipes(self, force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Get all valid recipes from the database with caching
        
        Args:
            force_refresh: Force refresh the cache
            
        Returns:
            Dictionary of recipe_name -> recipe_data
        """
        import time
        current_time = time.time()
        
        # Check if cache is valid
        if (not force_refresh and 
            self._valid_recipes_cache is not None and 
            self._cache_timestamp is not None and
            (current_time - self._cache_timestamp) < self._cache_ttl):
            logger.info("Using cached valid recipes")
            return self._valid_recipes_cache
        
        logger.info("Building valid recipes cache...")
        
        # Get all recipes from the collection
        all_docs = self.collection.get()
        valid_recipes = {}
        
        if all_docs and 'metadatas' in all_docs:
            for i, metadata in enumerate(all_docs['metadatas']):
                if metadata and 'recipe_name' in metadata:
                    recipe_name = metadata['recipe_name']
                    recipe_data = {
                        'id': all_docs['ids'][i],
                        'content': all_docs['documents'][i],
                        'metadata': metadata
                    }
                    valid_recipes[recipe_name.lower()] = recipe_data
        
        # Update cache
        self._valid_recipes_cache = valid_recipes
        self._cache_timestamp = current_time
        
        logger.info(f"Valid recipes cache built with {len(valid_recipes)} recipes")
        return valid_recipes
    
    def validate_recipe_exists(self, recipe_name: str) -> bool:
        """
        Quick validation to check if a recipe exists in the database
        
        Args:
            recipe_name: Name of the recipe to validate
            
        Returns:
            True if recipe exists, False otherwise
        """
        valid_recipes = self.get_all_valid_recipes()
        return recipe_name.lower() in valid_recipes