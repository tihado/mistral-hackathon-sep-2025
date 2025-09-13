"""
Shopping MCP Server with SerpAPI + Virtual Try-On
"""

import os
import json
import base64
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime
from io import BytesIO

from mcp.server.fastmcp import FastMCP
from pydantic import Field, BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from PIL import Image, ImageDraw, ImageFont
import google.genai as genai
import numpy as np
from dotenv import load_dotenv

import mcp.types as types

load_dotenv()

# Initialize MCP server
mcp = FastMCP("Shopping MCP Server", port=3000, stateless_http=True, debug=True)

# Global variables for vector database and model
vector_db = None
embedding_model = None
gemini_model = None
price_alerts = {}

# Product data models
class Product(BaseModel):
    id: str
    title: str
    price: str
    currency: str
    image_url: str
    source_url: str
    seller: str
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None

class ProductComparison(BaseModel):
    products: List[Product]
    comparison_data: Dict[str, Any]

class PriceAlert(BaseModel):
    product_id: str
    target_price: float
    current_price: float
    created_at: datetime
    is_active: bool = True

def initialize_vector_db():
    """Initialize Qdrant and embedding model"""
    global vector_db, embedding_model
    
    try:
        # Initialize Qdrant client (using in-memory mode for simplicity)
        vector_db = QdrantClient(":memory:")
        
        # Create collection for products
        vector_db.create_collection(
            collection_name="products",
            vectors_config=VectorParams(
                size=384,  # all-MiniLM-L6-v2 embedding size
                distance=Distance.COSINE
            )
        )
        
        # Initialize embedding model
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # print("Vector database and embedding model initialized successfully")
    except Exception as e:
        # print(f"Error initializing vector database: {e}")
        vector_db = None
        embedding_model = None

def get_serpapi_key():
    """Get SerpAPI key from environment variable"""
    return os.getenv('SERPAPI_KEY', 'your_serpapi_key_here')

def get_gemini_api_key():
    """Get Gemini API key from environment variable"""
    return os.getenv('GEMINI_API_KEY', 'your_gemini_api_key_here')

def initialize_gemini():
    """Initialize Google Generative AI with Gemini model"""
    api_key = get_gemini_api_key()
    if api_key == 'your_gemini_api_key_here':
        return None
    
    try:
        # Initialize the client with the API key
        client = genai.Client(api_key=api_key)
        # print("Gemini client initialized successfully")
        return client
    except Exception as e:
        # print(f"Error initializing Gemini: {e}")
        return None

def search_products_serpapi(query: str, num_results: int = 10) -> List[Product]:
    """Search products using SerpAPI Google Shopping"""
    api_key = get_serpapi_key()
    if api_key == 'your_serpapi_key_here':
        # Return mock data for demo purposes
        return [
            Product(
                id=f"mock_{i}",
                title=f"Mock Product {i} - {query}",
                price=f"${(i + 1) * 29.99:.2f}",
                currency="USD",
                image_url="https://via.placeholder.com/300x300?text=Product+Image",
                source_url=f"https://example.com/product/{i}",
                seller=f"Mock Store {i}",
                rating=4.0 + (i % 2) * 0.5,
                reviews_count=100 + i * 50,
                description=f"This is a mock product related to {query}",
                category="Electronics",
                brand=f"Brand {i}"
            )
            for i in range(min(num_results, 5))
        ]
    
    try:
        url = "https://serpapi.com/search"
        params = {
            'api_key': api_key,
            'engine': 'google_shopping',
            'q': query,
            'num': num_results
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        products = []
        if 'shopping_results' in data:
            for i, item in enumerate(data['shopping_results']):
                product = Product(
                    id=f"serp_{i}",
                    title=item.get('title', ''),
                    price=item.get('price', '0'),
                    currency=item.get('currency', 'USD'),
                    image_url=item.get('thumbnail', ''),
                    source_url=item.get('link', ''),
                    seller=item.get('source', ''),
                    rating=item.get('rating'),
                    reviews_count=item.get('reviews'),
                    description=item.get('description', ''),
                    category=item.get('category', ''),
                    brand=item.get('brand', '')
                )
                products.append(product)
        
        return products
    except Exception as e:
        # print(f"Error searching products: {e}")
        return []

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
