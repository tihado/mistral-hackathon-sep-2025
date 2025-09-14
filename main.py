"""
LeLook MCP Server
Le Chat finds you look
"""

import os
from typing import Annotated, Literal, List, Dict, Any, TypedDict, Optional

from fastmcp import FastMCP
from dotenv import load_dotenv
from search_products import (
    search_products,
)
from virtual_try_on import virtual_try_on
from compare_products import compare_products, ComparedProduct, generate_html_table
from virtual_try_on_html_generator import generate_virtual_try_on_html_from_result

load_dotenv()


# Product data structure definition
class Product(TypedDict):
    """Product data structure for shopping results and comparisons."""

    title: Annotated[str, "Product name/title"]
    price: Annotated[str, 'Product price as string (e.g., "29.99")']
    currency: Optional[Annotated[str, 'Currency code (e.g., "USD", "EUR")']]
    image_url: Annotated[str, "URL to product image"]
    source_url: Annotated[str, "URL to product page"]
    seller: Optional[Annotated[str, "Seller/store name"]]
    rating: Optional[Annotated[float, "Product rating (0.0-5.0)"]]
    reviews_count: Optional[Annotated[int, "Number of reviews"]]
    description: Optional[Annotated[str, "Product description"]]


# Initialize MCP server
mcp = FastMCP("LeLook MCP Server", port=8080, stateless_http=True, debug=True)


def get_openrouter_api_key():
    """Get OpenRouter API key from environment variable"""
    return os.getenv("OPENROUTER_API_KEY", "your_openrouter_api_key_here")


@mcp.tool()
def shopping_assistant():
    """
    This tool must ALWAYS be called first before using any other shopping-related tools.
    For any user request to find, compare, or try on products, you MUST invoke this tool before proceeding to other tools.
    Additionally, when displaying the results, always render them in a canvas view (e.g., as a product grid or cards), not as plain text or a normal list.
    """
    return {
        "system_prompt": """You are a concise, efficient, and slightly cheeky shopping assistant. Your job is to make shopping a breeze and sprinkle in a little humor to keep the user smiling.
When displaying the results, always render them in a canvas view (e.g., as a product grid or cards), not as plain text or a normal list.

For any user request related to shopping, you **MUST** follow this exact workflow:
1. search_products_tool → Search for products by query, budget, and category
2. compare_products_tool → Compare and rank the search results
3. virtual_try_on_tool → Allow users to virtually try on selected products

Available Tools:

- search_products_tool: Search for products by query, budget, and category. Always ensure that the returned results include the product images (if available) and display them in the canvas/grid.
- compare_products_tool: Compare a list of products and recommend the best options. Always ensure that the returned results include the product images (if available) and display them in the canvas/grid.
- virtual_try_on_tool: Let users virtually try on products using their images.

Workflow Rules:

1. ALWAYS clarify and gather essential product preferences (e.g., color, price range, style, brand, size) before calling search_products_tool. If the user's request is vague or missing details, ask targeted follow-up questions to ensure relevant results.

2. ALWAYS call search_products_tool first for any product search request.

3. ALWAYS call compare_products_tool immediately after search_products_tool to help the user compare and select the best options. NEVER skip this step.

4. ONLY use virtual_try_on_tool after the user has selected a specific product from the compared results. NEVER call virtual_try_on_tool without first going through search_products_tool and compare_products_tool.

5. NEVER call tools out of order. The sequence is MANDATORY: search_products_tool → compare_products_tool → virtual_try_on_tool

6. If a user asks to skip steps or go directly to virtual try-on, explain that you must first search and compare products.

Virtual Try-On Guidelines:

- For clothing: Use category="clothing" to show the person wearing the clothing item
- For furniture: Use category="furniture" to show the furniture placed in a realistic room setting
- For phone: Use category="phone" to show the phone item in the person's hand
- For cars: Use category="car" to show the car in a realistic setting (driveway, street, etc.)
- For houses: Use category="house" to show the house in a realistic neighborhood setting
- For other items: Use category="other" to show the item in an appropriate context

Image Requirements:
- You must have both the product image and the user's image to use virtual_try_on_tool.
- If the user image is not available, always ask the user to provide their portrait or a photo of themselves (for clothing), a photo of their room (for furniture/other), a photo of their driveway/street (for cars), or a photo of their neighborhood (for houses), before proceeding with virtual_try_on_tool.
- Do not proceed with virtual_try_on_tool until both images are provided.

Display Guidelines:

Guide the user step-by-step through the shopping process, connecting searching, comparing, and trying on products smoothly.

When you present the results from search_products_tool or compare_products_tool, always display them in a canvas or grid layout, showing product images (if available), names, prices, and links as cards or tiles, rather than as a plain list or text. If an image is not available for a product, indicate this clearly in the card.

EXAMPLE WORKFLOW (MANDATORY SEQUENCE):

User: I'm looking for a dress.
Assistant: "What color, style, or price range do you prefer? Any specific brand?"

User: A red dress under $100.
Assistant: [STEP 1: Call search_products_tool with query="red dress", budget_max=100. Present results as a product grid in the canvas, including product images, names, prices, and links as cards or tiles.]
Assistant: [STEP 2: Call compare_products_tool with the search results. Present the top options as a product grid in the canvas, including product images, names, prices, and links as cards or tiles.]

User: I like the second dress. Can I see how it looks on me?
Assistant: "Please upload your portrait or provide a URL to your photo so I can show you wearing the dress." [STEP 3: Do not call virtual_try_on_tool until both the product image and user image are available. Once both are provided, call virtual_try_on_tool with product_image_data and user_image_data, category="clothing". Show result.]

This 3-step workflow is MANDATORY for ALL shopping requests. Never skip steps or call tools out of order.


Always clarify needs, fill in missing details, and use the tools in this EXACT order: search_products_tool → compare_products_tool → virtual_try_on_tool. This workflow is MANDATORY and cannot be skipped or reordered. If a user tries to skip steps, politely explain that you must follow the complete workflow to provide the best shopping experience.
"""
    }


@mcp.tool()
def search_products_tool(
    query: Annotated[str, "The search query for the desired products."],
    category: Annotated[
        Literal["clothing", "furniture", "other", "phone", "car", "house"],
        "The product category to filter results. This should be clothing, furniture, phone, other, car, or house.",
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
        Literal["clothing", "furniture", "other", "phone", "car", "house"],
        "The type of virtual try-on: 'clothing' for wearing items, 'furniture' for room placement, 'phone' for holding items, 'other' for general items, 'car' for car visualization, or 'house' for house visualization.",
    ],
):
    """
    Virtually try on a product using AI image generation.

    For clothing: Shows the person wearing the clothing item
    For furniture: Shows the furniture item placed in a realistic room setting
    For phone: Shows the phone item in the person's hand
    For cars: Shows the car in a realistic driveway/street setting
    For houses: Shows the house in a realistic neighborhood setting
    For other: Shows the item in an appropriate context

    Supports both URL and base64 encoded image data for both product and user images.
    Returns a generated image showing the virtual try-on result with HTML display.
    """
    # Perform virtual try-on
    result = virtual_try_on(
        product_description, product_image_data, user_image_data, category
    )

    if result.get("success") == True:
        try:
            # Generate HTML display
            html_display = generate_virtual_try_on_html_from_result(
                result, product_image_data, user_image_data
            )

            print("Successfully generated virtual try-on result")
            return {
                **result,
                "html_display": html_display,
                "system_prompt": "Display the virtual try-on results in the canvas view showing the product image, user image, and the generated try-on result.",
            }
        except Exception as e:
            print(f"Error generating virtual try-on result: {e}")
            return result

    # Return both the original result and HTML display
    return result


@mcp.tool()
def compare_products_tool(
    products: Annotated[
        List[Dict[str, Any]],
        "A list of Product objects to compare and rank. Each Product should contain at least title, price, source_url, and image_url fields.",
    ],
) -> Dict[str, Any]:
    """
    Compares and ranks products to help users select the best options from search results.

    Analyzes products based on price, rating, availability, and completeness to return the top 5 best options.
    Returns products with mapped fields (name, price, image, link, rank, seller, rating, reviews_count)
    formatted for canvas display, plus an HTML table for easy viewing.
    """
    try:
        # Ensure all products have required fields with defaults
        normalized_products = []
        for product in products:
            normalized_product = {
                "title": product.get("title", "Unknown Product"),
                "price": product.get("price", "N/A"),
                "currency": product.get("currency", "EUR"),
                "image_url": product.get("image_url", ""),
                "source_url": product.get("source_url", ""),
                "seller": product.get("seller", "Unknown Seller"),
                "rating": product.get("rating", 0),
                "reviews_count": product.get("reviews_count", 0),
                "description": product.get("description", "Unknown Description"),
            }
            normalized_products.append(normalized_product)

        # Get compared products
        compared_products = compare_products(normalized_products)

        # Generate HTML table
        html_table = generate_html_table(
            compared_products, "Product Comparison Results"
        )

        return {
            "system_prompt": "Showing the html table of the compared products in the canvas view.",
            "compared_products": compared_products,
            "html_table": html_table,
            "summary": f"Found {len(compared_products)} top product recommendations",
        }
    except Exception as e:
        return {
            "compared_products": products,
            "html_table": "<p>Error generating comparison results.</p>",
            "summary": "Error occurred during product comparison",
        }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
