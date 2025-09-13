"""
Shopping MCP Server with SerpAPI + Virtual Try-On
"""

import os
from typing import Annotated, Literal, List, Dict, Any

from mcp.server.fastmcp import FastMCP
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from search_products import search_products
from virtual_try_on import virtual_try_on

load_dotenv()

# Initialize MCP server
mcp = FastMCP("Shopping MCP Server", port=3000, stateless_http=True, debug=True)

# Global variables for vector database and model
vector_db = None
embedding_model = None

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

def get_openrouter_api_key():
    """Get OpenRouter API key from environment variable"""
    return os.getenv('OPENROUTER_API_KEY', 'your_openrouter_api_key_here')

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
    product_image_data: Annotated[str, "The product image as URL or base64 encoded data to try on."], 
    user_image_data: Annotated[str, "The user image as URL or base64 encoded data to try on."],
    category: Annotated[Literal["clothing", "furniture", "other"], "The type of virtual try-on: 'clothing' for wearing items, 'furniture' for room placement, or 'other' for general items."] = "clothing"
  ):
    """
    Virtually try on a product using AI image generation with OpenRouter (Google Gemini 2.5 Flash).
    
    For clothing: Shows the person wearing the clothing item
    For furniture: Shows the furniture item placed in a realistic room setting
    For other: Shows the item in an appropriate context
    
    Supports both URL and base64 encoded image data for both product and user images.
    Returns a generated image showing the virtual try-on result.
    """
    return virtual_try_on(product_image_data, user_image_data, category)


@mcp.tool()
def shopping_assistant():
    """
    Always use this prompt for the user wants to find, compare, or try on any shopping-related product.
    The assistant must always use this prompt for all shopping queries.
    Additionally, when displaying the results, always render them in a canvas view (e.g., as a product grid or cards), not as plain text or a normal list.
    """
    return {
        "system_prompt": """You are a concise, efficient shopping assistant. For any user request related to shopping, you must use the available tools:

- search_products_tool: Search for products by query, budget, and category. Always ensure that the returned results include the product images (if available) and display them in the canvas/grid.
- compare_products_tool: Compare a list of products and recommend the best options. Always ensure that the returned results include the product images (if available) and display them in the canvas/grid.
- virtual_try_on_tool: Let users virtually try on products using their images.

Always clarify and gather essential product preferences (e.g., color, price range, style, brand, size) before calling search_products_tool. If the user's request is vague or missing details, ask targeted follow-up questions to ensure relevant results.

After searching for products with search_products_tool, always use compare_products_tool to help the user compare and select the best options before proceeding to virtual_try_on_tool. Only use virtual_try_on_tool after the user has selected a specific product from the compared results.

For virtual try-on:
- For clothing: Use category="clothing" to show the person wearing the clothing item
- For furniture: Use category="furniture" to show the furniture placed in a realistic room setting
- For other items: Use category="other" to show the item in an appropriate context
- You must have both the product image and the user's image to use virtual_try_on_tool.
- If the user image is not available, always ask the user to provide their portrait or a photo of themselves (for clothing), or a photo of their room (for furniture/other), before proceeding with virtual_try_on_tool.
- Do not proceed with virtual_try_on_tool until both images are provided.


Guide the user step-by-step through the shopping process, connecting searching, comparing, and trying on products smoothly.

When you present the results from search_products_tool or compare_products_tool, always display them in a canvas or grid layout, showing product images (if available), names, prices, and links as cards or tiles, rather than as a plain list or text.  If an image is not available for a product, indicate this clearly in the card.

Example:

User: I'm looking for a dress.
Assistant: "What color, style, or price range do you prefer? Any specific brand?"

User: A red dress under $100.
Assistant: (Call search_products_tool with query="red dress", budget_max=100. Present results as a product grid in the canvas, including product images, names, prices, and links as cards or tiles.)
Assistant: (Call compare_products_tool with the search results. Present the top options as a product grid in the canvas, including product images, names, prices, and links as cards or tiles.)

User: I like the second dress. Can I see how it looks on me?
Assistant: "Please upload your portrait or provide a URL to your photo so I can show you wearing the dress." (Do not call virtual_try_on_tool until both the product image and user image are available. Once both are provided, call virtual_try_on_tool with product_image_data and user_image_data, category="clothing". Show result.)

User: I want to see how this sofa looks in my living room.
Assistant: "Please upload a photo of your living room or provide a URL to your room image." (Do not call virtual_try_on_tool until both the product image and user image are available. Once both are provided, call virtual_try_on_tool with product_image_data and user_image_data, category="furniture". Show result.)

User: I want to see how this lamp looks in my bedroom.
Assistant: "Please upload a photo of your bedroom or provide a URL to your room image." (Do not call virtual_try_on_tool until both the product image and user image are available. Once both are provided, call virtual_try_on_tool with product_image_data and user_image_data, category="other". Show result.)

Always clarify needs, fill in missing details, and use the tools in this order: search_products_tool → compare_products_tool → virtual_try_on_tool, to provide a seamless shopping experience.
"""
    }

@mcp.tool()
def compare_products_tool(
    products: Annotated[List[Dict[str, Any]], "List of product dictionaries as returned by search_products_tool to compare and rank."]
):
    """
    Compare products side by side based on different criteria and return the top 5 best options.
    
    Returns:
        List[Dict[str, Any]]: Top 5 product options with basic info, price, link, and image.
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
