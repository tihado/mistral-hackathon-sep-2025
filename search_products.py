import os
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

def get_serpapi_key():
    """Get SerpAPI key from environment variable"""
    return os.getenv('SERPAPI_KEY', 'your_serpapi_key_here')

def mock_search_products():
    return [{
        "title": "Mock Product 1",
        "price": "100",
        "currency": "USD",
        "image_url": "https://via.placeholder.com/150",
        "source_url": "https://www.mockproduct1.com",
    }]

def search_products(
    query: str, 
    num_results: int = 10, 
    min_price: Optional[float] = None, 
    max_price: Optional[float] = None, 
    free_shipping: Optional[bool] = None, 
    on_sale: Optional[bool] = None, 
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for products using Google Shopping via SerpAPI.
    
    Args:
        query: Search query string
        num_results: Number of results to return (default: 10)
        min_price: Minimum price filter
        max_price: Maximum price filter
        free_shipping: Filter for free shipping
        on_sale: Filter for products on sale
        category: Product category filter
    
    Returns:
        List of product dictionaries with search results
    """
    api_key = get_serpapi_key()
    
    if api_key == 'your_serpapi_key_here':
        return mock_search_products()
    
    # Build search parameters
    params = {
        "api_key": api_key,
        "engine": "google_shopping",
        "q": query,
        "num": num_results,
        "google_domain": "google.fr",
        "hl": "fr",
        "gl": "fr",
        "location": "Paris, Ile-de-France, France",
        "tbm": "shop"
    }
    
    # Add optional filters
    if min_price is not None:
        params["min_price"] = str(min_price)
    if max_price is not None:
        params["max_price"] = str(max_price)
    if free_shipping is not None:
        params["free_shipping"] = "true" if free_shipping else "false"
    if on_sale is not None:
        params["on_sale"] = "true" if on_sale else "false"
    if category:
        params["category"] = str(category)
    
    try:
        # Make API request
        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract shopping results
        shopping_results = data.get("shopping_results", [])
        
        # Format results
        products = []
        for item in shopping_results:
            product = {
                "title": item.get("title", ""),
                "price": item.get("price", ""),
                "currency": item.get("currency", "USD"),
                "image_url": item.get("thumbnail", ""),
                "source_url": item.get("link", item.get("product_link", "")),
                "seller": item.get("source", ""),
                "rating": item.get("rating"),
                "reviews_count": item.get("reviews"),
                "description": item.get("description", ""),
                "category": category,
                "brand": item.get("brand", ""),
                "delivery": item.get("delivery", ""),
                "original_price": item.get("old_price"),
                "tags": item.get("tag", "").split(",").strip()
            }
            products.append(product)
        
        return products
        
    except requests.exceptions.RequestException as e:
        return [{
            "error": f"API request failed: {str(e)}",
            "products": []
        }]
    except KeyError as e:
        return [{
            "error": f"Unexpected API response format: {str(e)}",
            "products": []
        }]
    except Exception as e:
        return [{
            "error": f"Unexpected error: {str(e)}",
            "products": []
        }]