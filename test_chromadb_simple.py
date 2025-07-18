#!/usr/bin/env python3
"""
Test ChromaDB setup without requiring OpenAI API key
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import chromadb
    print("✅ ChromaDB is installed")
    
    # Create a simple client
    client = chromadb.PersistentClient(path="./chroma_db_test")
    print("✅ ChromaDB client created")
    
    # Create a test collection
    collection = client.create_collection(
        name="test_collection",
        metadata={"description": "Test collection"}
    )
    print("✅ Test collection created")
    
    # Add a simple document
    collection.add(
        documents=["This is a test recipe"],
        metadatas=[{"type": "test"}],
        ids=["test1"]
    )
    print("✅ Document added to collection")
    
    # Query the collection
    results = collection.query(
        query_texts=["test"],
        n_results=1
    )
    print(f"✅ Query successful: {len(results['ids'][0])} results found")
    
    # Cleanup
    client.delete_collection(name="test_collection")
    print("✅ Test collection deleted")
    
    print("\n✅ ChromaDB is working correctly!")
    print("\nNote: To load actual recipes, you need to set OPENAI_API_KEY in .env file")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nPlease check your ChromaDB installation")