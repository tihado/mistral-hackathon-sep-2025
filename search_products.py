import os
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from vector_database import (
    initialize_vector_db,
    save_product_to_db,
    query_products_from_db,
)

load_dotenv()

# Initialize vector database on module load
initialize_vector_db()


def get_serpapi_key():
    """Get SerpAPI key from environment variable"""
    return os.getenv("SERPAPI_KEY", "your_serpapi_key_here")


def mock_search_products():
    return [
        {
            "title": "Mock Product 1",
            "price": "100",
            "currency": "USD",
            "image_url": "https://via.placeholder.com/150",
            "source_url": "https://www.mockproduct1.com",
        }
    ]


def search_products_serpapi(
    query: str,
    num_results: int = 10,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    free_shipping: Optional[bool] = None,
    on_sale: Optional[bool] = None,
    category: Optional[str] = None,
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

    if api_key == "your_serpapi_key_here":
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
        "tbm": "shop",
    }

    # Add optional filters
    if min_price is not None:
        params["min_price"] = str(int(min_price))
    if max_price is not None:
        params["max_price"] = str(int(max_price))
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
                "tags": [
                    tag.strip() for tag in item.get("tag", "").split(",") if tag.strip()
                ],
            }
            products.append(product)

            # Save product to vector database
            try:
                save_product_to_db(product)
            except Exception as e:
                print(f"Warning: Failed to save product to vector database: {e}")

        return products

    except requests.exceptions.RequestException as e:
        return [{"error": f"API request failed: {str(e)}", "products": []}]
    except KeyError as e:
        return [{"error": f"Unexpected API response format: {str(e)}", "products": []}]
    except Exception as e:
        return [{"error": f"Unexpected error: {str(e)}", "products": []}]


def search_products_from_db(
    query: str,
    num_results: int = 10,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    free_shipping: Optional[bool] = None,
    on_sale: Optional[bool] = None,
    category: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search for products from the vector database using semantic search.

    Args:
        query: Search query string
        num_results: Number of results to return (default: 10)
        min_price: Minimum price filter
        max_price: Maximum price filter
        free_shipping: Filter for free shipping (not implemented in vector search)
        on_sale: Filter for products on sale (not implemented in vector search)
        category: Product category filter

    Returns:
        List of product dictionaries with search results from vector database
    """
    try:
        # Convert price filters to float for vector database
        min_price_float = float(min_price) if min_price is not None else None
        max_price_float = float(max_price) if max_price is not None else None

        # Query products from vector database
        products = query_products_from_db(
            query=query,
            limit=num_results,
            category=category,
            min_price=min_price_float,
            max_price=max_price_float,
        )

        print(f"search_products_from_db: Vector results: {len(products)}")

        if not products or len(products) == 0:
            return []

        # Apply additional filters that aren't supported by vector search
        filtered_products = []
        for product in products:
            # Apply free shipping filter if specified
            if free_shipping is not None:
                delivery = product.get("delivery", "").lower()
                has_free_shipping = "free" in delivery or "gratuit" in delivery
                if free_shipping and not has_free_shipping:
                    continue
                if not free_shipping and has_free_shipping:
                    continue

            # Apply on sale filter if specified
            if on_sale is not None:
                has_original_price = product.get("original_price") is not None
                if on_sale and not has_original_price:
                    continue
                if not on_sale and has_original_price:
                    continue

            filtered_products.append(product)

        return filtered_products

    except Exception as e:
        return [{"error": f"Vector database search failed: {str(e)}", "products": []}]


def search_products(
    query: str,
    num_results: int = 10,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    free_shipping: Optional[bool] = None,
    on_sale: Optional[bool] = None,
    category: Optional[str] = None,
    vector_db_weight: float = 0.6,
) -> List[Dict[str, Any]]:
    """
    Combined search function that searches both vector database and internet, then merges results.

    Args:
        query: Search query string
        num_results: Number of results to return (default: 10)
        min_price: Minimum price filter
        max_price: Maximum price filter
        free_shipping: Filter for free shipping
        on_sale: Filter for products on sale
        category: Product category filter
        vector_db_weight: Weight for vector database results (0.0-1.0, default: 0.6)

    Returns:
        List of product dictionaries with combined search results
    """
    try:
        # Search from both sources
        vector_results = search_products_from_db(
            query,
            num_results * 2,
            min_price,
            max_price,
            free_shipping,
            on_sale,
            category,
        )
        internet_results = search_products_serpapi(
            query,
            num_results * 2,
            min_price,
            max_price,
            free_shipping,
            on_sale,
            category,
        )

        print(f"Vector results: {len(vector_results)}")

        if not vector_results or len(vector_results) == 0:
            return internet_results

        if not internet_results or len(internet_results) == 0:
            return vector_results

        # Remove error responses
        vector_results = [r for r in vector_results if not r.get("error")]
        internet_results = [r for r in internet_results if not r.get("error")]

        # Deduplicate results based on source_url
        seen_urls = set()
        combined_results = []

        # Add vector database results first (they have semantic scores)
        for product in vector_results:
            source_url = product.get("source_url", "")
            if source_url and source_url not in seen_urls:
                product["source"] = "vector_db"
                combined_results.append(product)
                seen_urls.add(source_url)

        # Add internet results that aren't duplicates
        for product in internet_results:
            source_url = product.get("source_url", "")
            if source_url and source_url not in seen_urls:
                product["source"] = "internet"
                # Add a default score for internet results
                if "score" not in product:
                    product["score"] = 0.5
                combined_results.append(product)
                seen_urls.add(source_url)

        # Sort by combined score (vector DB results get higher weight)
        def combined_score(product):
            base_score = product.get("score", 0.5)
            source = product.get("source", "internet")

            if source == "vector_db":
                return base_score * vector_db_weight + (1 - vector_db_weight) * 0.5
            else:
                return base_score * (1 - vector_db_weight) + vector_db_weight * 0.3

        combined_results.sort(key=combined_score, reverse=True)

        # Limit results
        final_results = combined_results[:num_results]

        print(
            f"Combined search: {len(vector_results)} vector + {len(internet_results)} internet = {len(final_results)} unique results"
        )
        return final_results

    except Exception as e:
        print(f"Error in combined search: {e}")
        # Fallback to internet search only
        return search_products_serpapi(
            query, num_results, min_price, max_price, free_shipping, on_sale, category
        )
