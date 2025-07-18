#!/usr/bin/env python3
"""
Simple verification of ChromaDB data loading
"""

import os
import sys
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verify_chromadb_simple():
    """Simple verification without embedding queries"""
    
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(
        path=os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db"),
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Get collection
    collection_name = os.getenv("CHROMA_COLLECTION_NAME", "nutrition_recipes")
    collection = client.get_collection(name=collection_name)
    
    print(f"✅ Connected to collection: {collection_name}")
    print(f"📊 Total documents: {collection.count()}")
    
    # Get sample documents
    print("\n📄 Sample recipes:")
    sample = collection.get(limit=5)
    
    for i, (doc_id, doc, metadata) in enumerate(zip(sample['ids'], sample['documents'], sample['metadatas'])):
        print(f"\n{i+1}. Recipe: {metadata.get('recipe_name', 'Unknown')}")
        print(f"   Category: {metadata.get('category', 'Unknown')}")
        print(f"   Meal types: {metadata.get('meal_types', 'Unknown')}")
        print(f"   Doc ID: {doc_id}")
        print(f"   Preview: {doc[:150]}...")
    
    # Show category distribution
    print("\n📈 Category distribution:")
    all_docs = collection.get()
    categories = {}
    recipe_types = {}
    
    for metadata in all_docs['metadatas']:
        cat = metadata.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
        
        # Check for equivalence tables
        if metadata.get('type') == 'equivalence_table':
            recipe_types['equivalence_tables'] = recipe_types.get('equivalence_tables', 0) + 1
        else:
            recipe_types['recipes'] = recipe_types.get('recipes', 0) + 1
    
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   {cat}: {count} documents")
    
    print(f"\n📊 Document types:")
    for doc_type, count in recipe_types.items():
        print(f"   {doc_type}: {count}")
    
    # Check specific recipe types
    print("\n🍳 Breakfast recipes:")
    breakfast_docs = collection.get(
        where={"category": {"$in": ["desayuno_dulce", "desayuno_salado"]}}
    )
    print(f"   Found {len(breakfast_docs['ids'])} breakfast recipes")
    
    print("\n🥗 Lunch/Dinner recipes:")
    main_docs = collection.get(
        where={"category": {"$in": ["pollo", "carne", "vegetariano", "cerdo", "pescado_mariscos"]}}
    )
    print(f"   Found {len(main_docs['ids'])} main course recipes")
    
    print("\n✅ ChromaDB verification completed successfully!")
    print("\n💡 Note: To perform semantic search, use the OpenAI embeddings as configured in load_to_chromadb.py")

if __name__ == "__main__":
    verify_chromadb_simple()