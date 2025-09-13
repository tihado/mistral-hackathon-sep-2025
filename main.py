"""
Shopping MCP Server with SerpAPI + Virtual Try-On
"""

import os
from typing import List, Optional, Dict, Any, Annotated, Literal
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from pydantic import Field, BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import google.genai as genai
from dotenv import load_dotenv
from search_products import search_products
from virtual_try_on import virtual_try_on

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
    min_price: Annotated[int, "The minimum price for filtering products."] = None,
    max_price: Annotated[int, "The maximum price for filtering products."] = None,
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


@mcp.tool()
def shopping_assistant():
    """
    Always use this prompt for the user wants to find, compare, or try on any shopping-related product.
    The assistant must always use this prompt for all shopping queries.
    """
    return {
        "system_prompt": """You are a concise, efficient shopping assistant. For any user request related to shopping, you must use the available tools:

- search_products: Search for products by query, budget, and category.
- compare_products: Compare a list of products and recommend the best options.
- virtual_try_on: Let users virtually try on products using their images.

Always clarify and gather essential product preferences (e.g., color, price range, style, brand, size) before calling search_products. If the user's request is vague or missing details, ask targeted follow-up questions to ensure relevant results.

After searching for products with search_products, always use compare_products to help the user compare and select the best options before proceeding to virtual_try_on. Only use virtual_try_on after the user has selected a specific product from the compared results.

If the user wants to try on a product, request their photo (if not already provided) and use virtual_try_on with the correct product_id and image.

Guide the user step-by-step through the shopping process, connecting searching, comparing, and trying on products smoothly.

Example:

User: I'm looking for a dress.
Assistant: "What color, style, or price range do you prefer? Any specific brand?"

User: A red dress under $100.
Assistant: (Call search_products with query="red dress", budget_max=100. Present results.)
Assistant: (Call compare_products with the search results. Present the top options.)

User: I like the second dress. Can I see how it looks on me?
Assistant: "Please upload your photo." (Call virtual_try_on with product_id and user image. Show result.)

Always clarify needs, fill in missing details, and use the tools in this order: search_products → compare_products → virtual_try_on, to provide a seamless shopping experience."""
    }


@mcp.tool()
def compare_products(products: list):
    """
    Compare products side by side based on different criteria and return the top 5 best options.
    Args:
        products (list): List of product dictionaries as returned by search_products_tool.
    Returns:
        list: Top 5 product options with basic info, price, link, and image.
    """
    if not products or not isinstance(products, list):
        return []

    # Example criteria: prioritize lower price, higher rating (if available), and in-stock status
    def product_score(prod):
        # Lower price is better, higher rating is better, in-stock preferred
        price = prod.get("price", float("inf"))
        rating = prod.get("rating", 0)
        in_stock = 1 if prod.get("in_stock", True) else 0
        # Weighted score: adjust as needed
        return (in_stock * 1000) + (rating * 10) - price

    # Sort products by score descending
    sorted_products = sorted(products, key=product_score, reverse=True)
    top_products = sorted_products[:5]

    # Prepare output with required fields
    result = []
    for prod in top_products:
        result.append({
            "name": prod.get("name"),
            "price": prod.get("price"),
            "link": prod.get("link"),
            "image": prod.get("image"),
            "seller": prod.get("seller"),
            "rating": prod.get("rating"),
            "in_stock": prod.get("in_stock", True),
        })
    return result

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
