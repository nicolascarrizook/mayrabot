#!/usr/bin/env python3
"""
Verify ChromaDB data loading
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

def verify_chromadb():
    """Verify ChromaDB data was loaded correctly"""
    
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
    
    # Test queries
    print("\n🔍 Testing semantic search queries:")
    
    # Test 1: Search for chicken recipes
    print("\n1. Searching for 'pollo' (chicken) recipes:")
    results = collection.query(
        query_texts=["pollo al horno con verduras"],
        n_results=3
    )
    
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"   Result {i+1}: {metadata.get('recipe_name', 'Unknown')}")
        print(f"   Category: {metadata.get('category', 'Unknown')}")
        print(f"   Preview: {doc[:100]}...\n")
    
    # Test 2: Search for breakfast recipes
    print("2. Searching for 'desayuno' (breakfast) recipes:")
    results = collection.query(
        query_texts=["desayuno dulce con frutas"],
        n_results=3
    )
    
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"   Result {i+1}: {metadata.get('recipe_name', 'Unknown')}")
        print(f"   Category: {metadata.get('category', 'Unknown')}")
        print(f"   Meal types: {metadata.get('meal_types', 'Unknown')}\n")
    
    # Test 3: Search for equivalences
    print("3. Searching for 'lácteos' (dairy) equivalences:")
    results = collection.query(
        query_texts=["lácteos leche yogur"],
        n_results=1,
        where={"type": "equivalence_table"}
    )
    
    if results['documents'][0]:
        doc = results['documents'][0][0]
        metadata = results['metadatas'][0][0]
        print(f"   Found: {metadata.get('category', 'Unknown')} equivalences")
        print(f"   Preview: {doc[:200]}...\n")
    
    # Show category distribution
    print("📈 Category distribution:")
    all_docs = collection.get()
    categories = {}
    
    for metadata in all_docs['metadatas']:
        cat = metadata.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   {cat}: {count} documents")
    
    print("\n✅ ChromaDB verification completed!")

if __name__ == "__main__":
    verify_chromadb()