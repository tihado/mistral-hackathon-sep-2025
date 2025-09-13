"""
Shopping MCP Server with SerpAPI + Virtual Try-On
"""

import os
import json
import base64
import requests
from typing import List, Optional, Dict, Any, Annotated, Literal
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
from search_products import search_products
from virtual_try_on import virtual_try_on

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

@mcp.tool()
def search_products_tool(
    query: Annotated[str, "The search query for the desired products."],
    category: Annotated[Literal["clothing", "furniture", "other"], "The product category to filter results. This should be clothing, furniture, or other."],
    min_price: Annotated[float, "The minimum price for filtering products."] = None,
    max_price: Annotated[float, "The maximum price for filtering products."] = None,
    free_shipping: Annotated[bool, "Whether to filter products with free shipping."] = None,
    on_sale: Annotated[bool, "Whether to filter products on sale."] = None,
    num_results: Annotated[int, "The number of product results to return."] = 10,
):
    """
    Search for products using Google Shopping via SerpAPI.
    Returns:
        List[dict]: A list of product information dictionaries.
    """
    return search_products(query, num_results, min_price, max_price, free_shipping, on_sale, category)

@mcp.tool()
def virtual_try_on_tool(
    product_image_data: Annotated[str, "The image data of the product to try on."], 
    user_image_data: Annotated[str, "The image data of the user to try on."]
  ):
    """Virtually try on a product using AI image generation with both product and user images."""
    return virtual_try_on(product_image_data, user_image_data)

@mcp.prompt()
def shopping_assistant():
    """Generate a helpful shopping assistant prompt based on user query and context."""
    return """You are a helpful shopping assistant. You are given a user query and context. You need to generate a helpful shopping assistant prompt based on user query and context."""

@mcp.prompt()
def compare_products():
    """Compare products side by side."""
    return """You are a helpful shopping assistant. You are given a user query and context. You need to generate a helpful shopping assistant prompt based on user query and context."""

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
