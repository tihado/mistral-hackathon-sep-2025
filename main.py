"""
Shopping MCP Server with SerpAPI + Virtual Try-On
"""

import os
from typing import Annotated, Literal, List, Dict, Any, TypedDict, Optional

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from search_products import (
    search_products,
)
from virtual_try_on import virtual_try_on
from compare_products import compare_products, ComparedProduct

load_dotenv()


# Product data structure definition
class Product(TypedDict):
    """Product data structure for shopping results and comparisons."""

    title: Annotated[str, "Product name/title"]
    price: Annotated[str, 'Product price as string (e.g., "29.99")']
    currency: Annotated[str, 'Currency code (e.g., "USD", "EUR")']
    image_url: Annotated[str, "URL to product image"]
    source_url: Annotated[str, "URL to product page"]
    seller: Annotated[str, "Seller/store name"]
    rating: Annotated[Optional[float], "Product rating (0.0-5.0)"]
    reviews_count: Annotated[Optional[int], "Number of reviews"]
    description: Annotated[Optional[str], "Product description"]
    category: Annotated[Optional[str], "Product category"]
    brand: Annotated[Optional[str], "Product brand"]
    delivery: Annotated[Optional[str], "Delivery information"]
    original_price: Annotated[Optional[str], "Original price if on sale"]
    tags: Annotated[Optional[List[str]], "Product tags/keywords"]
    in_stock: Annotated[Optional[bool], "Availability status"]


# Initialize MCP server
mcp = FastMCP("Shopping MCP Server", port=3000, stateless_http=True, debug=True)


def get_openrouter_api_key():
    """Get OpenRouter API key from environment variable"""
    return os.getenv("OPENROUTER_API_KEY", "your_openrouter_api_key_here")


@mcp.tool()
def shopping_assistant():
    """
    Always use this prompt for the user wants to find, compare, or try on any shopping-related product.
    The assistant must always use this prompt for all shopping queries.
    Additionally, when displaying the results, always render them in a canvas view (e.g., as a product grid or cards), not as plain text or a normal list.
    """
    return {
        "system_prompt": """# Shopping Assistant

You are a concise, efficient shopping assistant. For any user request related to shopping, you **MUST** follow this exact workflow:

## MANDATORY WORKFLOW

1. **search_products_tool** → Search for products by query, budget, and category
2. **compare_products_tool** → Compare and rank the search results  
3. **virtual_try_on_tool** → Allow users to virtually try on selected products

## AVAILABLE TOOLS

- **search_products_tool**: Search for products by query, budget, and category. Always ensure that the returned results include the product images (if available) and display them in the canvas/grid.
- **compare_products_tool**: Compare a list of products and recommend the best options. Always ensure that the returned results include the product images (if available) and display them in the canvas/grid.
- **virtual_try_on_tool**: Let users virtually try on products using their images.

## WORKFLOW RULES

1. **ALWAYS** clarify and gather essential product preferences (e.g., color, price range, style, brand, size) before calling `search_products_tool`. If the user's request is vague or missing details, ask targeted follow-up questions to ensure relevant results.

2. **ALWAYS** call `search_products_tool` first for any product search request.

3. **ALWAYS** call `compare_products_tool` immediately after `search_products_tool` to help the user compare and select the best options. **NEVER** skip this step.

4. **ONLY** use `virtual_try_on_tool` after the user has selected a specific product from the compared results. **NEVER** call `virtual_try_on_tool` without first going through `search_products_tool` and `compare_products_tool`.

5. **NEVER** call tools out of order. The sequence is **MANDATORY**: `search_products_tool` → `compare_products_tool` → `virtual_try_on_tool`

6. If a user asks to skip steps or go directly to virtual try-on, explain that you must first search and compare products.

## Virtual Try-On Guidelines

- **For clothing**: Use `category="clothing"` to show the person wearing the clothing item
- **For furniture**: Use `category="furniture"` to show the furniture placed in a realistic room setting
- **For phone**: Use `category="phone"` to show the phone item in the person's hand
- **For other items**: Use `category="other"` to show the item in an appropriate context

### Image Requirements
- You must have both the product image and the user's image to use `virtual_try_on_tool`
- If the user image is not available, always ask the user to provide their portrait or a photo of themselves (for clothing), or a photo of their room (for furniture/other), before proceeding with `virtual_try_on_tool`
- Do not proceed with `virtual_try_on_tool` until both images are provided

## Display Guidelines

Guide the user step-by-step through the shopping process, connecting searching, comparing, and trying on products smoothly.

When you present the results from `search_products_tool` or `compare_products_tool`, always display them in a canvas or grid layout, showing product images (if available), names, prices, and links as cards or tiles, rather than as a plain list or text. If an image is not available for a product, indicate this clearly in the card.

## EXAMPLE WORKFLOW (MANDATORY SEQUENCE)

```
User: I'm looking for a dress.
Assistant: "What color, style, or price range do you prefer? Any specific brand?"

User: A red dress under $100.
Assistant: [STEP 1: Call `search_products_tool` with query="red dress", budget_max=100. Present results as a product grid in the canvas, including product images, names, prices, and links as cards or tiles.]
Assistant: [STEP 2: Call `compare_products_tool` with the search results. Present the top options as a product grid in the canvas, including product images, names, prices, and links as cards or tiles.]

User: I like the second dress. Can I see how it looks on me?
Assistant: "Please upload your portrait or provide a URL to your photo so I can show you wearing the dress." [STEP 3: Do not call `virtual_try_on_tool` until both the product image and user image are available. Once both are provided, call `virtual_try_on_tool` with `product_image_data` and `user_image_data`, category="clothing". Show result.]
```

> **IMPORTANT**: This 3-step workflow is **MANDATORY** for ALL shopping requests. Never skip steps or call tools out of order.

## CRITICAL REMINDER

Always clarify needs, fill in missing details, and use the tools in this **EXACT** order: `search_products_tool` → `compare_products_tool` → `virtual_try_on_tool`. This workflow is **MANDATORY** and cannot be skipped or reordered. If a user tries to skip steps, politely explain that you must follow the complete workflow to provide the best shopping experience.
"""
    }


@mcp.tool()
def search_products_tool(
    query: Annotated[str, "The search query for the desired products."],
    category: Annotated[
        Literal["clothing", "furniture", "other", "phone"],
        "The product category to filter results. This should be clothing, furniture, phone, or other.",
    ],
    min_price: Annotated[int, "The minimum price for filtering products."] = None,
    max_price: Annotated[int, "The maximum price for filtering products."] = None,
    free_shipping: Annotated[
        bool, "Whether to filter products with free shipping."
    ] = None,
    on_sale: Annotated[bool, "Whether to filter products on sale."] = None,
    num_results: Annotated[int, "The number of product results to return."] = 10,
):
    """
    Search for products based on a user query and optional filters such as category, price range, free shipping, and sale status.

    This tool returns a list of relevant products that match the search criteria, including details such as product title, price, image, seller, and a link to purchase. You can specify the type of product (e.g., clothing, furniture, or other), set minimum and maximum price limits, and filter for free shipping or items on sale. The number of results returned can also be adjusted.

    Use this tool to help users discover and browse products that fit their preferences and requirements.
    """
    return search_products(
        query, num_results, min_price, max_price, free_shipping, on_sale, category
    )


@mcp.tool()
def virtual_try_on_tool(
    product_description: Annotated[str, "The description of the product to try on."],
    product_image_data: Annotated[
        str, "The product image as URL or base64 encoded data to try on."
    ],
    user_image_data: Annotated[
        str, "The user image as URL or base64 encoded data to try on."
    ],
    category: Annotated[
        Literal["clothing", "furniture", "other", "phone"],
        "The type of virtual try-on: 'clothing' for wearing items, 'furniture' for room placement, 'phone' for holding items, or 'other' for general items.",
    ],
):
    """
    Virtually try on a product using AI image generation.

    For clothing: Shows the person wearing the clothing item
    For furniture: Shows the furniture item placed in a realistic room setting
    For phone: Shows the phone item in the person's hand
    For other: Shows the item in an appropriate context

    Supports both URL and base64 encoded image data for both product and user images.
    Returns a generated image showing the virtual try-on result.
    """
    return virtual_try_on(
        product_description, product_image_data, user_image_data, category
    )


@mcp.tool()
def compare_products_tool(
    products: Annotated[
        List[Product],
        "A list of Product objects to compare and rank. Each Product should contain at least title, price, and image_url fields.",
    ],
) -> List[ComparedProduct]:
    """
    Compares and ranks products to help users select the best options from search results.
    
    Analyzes products based on price, rating, availability, and completeness to return the top 5 best options.
    Returns products with mapped fields (name, price, image, link, rank, seller, rating, reviews_count) 
    formatted for canvas display.
    """
    return compare_products(products)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
