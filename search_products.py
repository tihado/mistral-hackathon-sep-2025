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


def get_openrouter_api_key():
    """Get OpenRouter API key from environment variable"""
    return os.getenv("OPENROUTER_API_KEY", "your_openrouter_api_key_here")


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


def rerank_products_with_llm(
    products: List[Dict[str, Any]], query: str, max_products: int = 10
) -> List[Dict[str, Any]]:
    """
    Rerank products using LLM via OpenRouter API.

    Args:
        products: List of product dictionaries to rerank
        query: Original search query for context
        max_products: Maximum number of products to return

    Returns:
        List of reranked product dictionaries
    """
    if not products or len(products) == 0:
        return products

    api_key = get_openrouter_api_key()

    if api_key == "your_openrouter_api_key_here":
        print("Warning: OpenRouter API key not configured, skipping LLM reranking")
        return products[:max_products]

    try:
        # Prepare product data for LLM
        product_summaries = []
        for i, product in enumerate(products):
            summary = {
                "index": i,
                "title": product.get("title", ""),
                "price": product.get("price", ""),
                "currency": product.get("currency", ""),
                "rating": product.get("rating", 0),
                "reviews_count": product.get("reviews_count", 0),
                "description": product.get("description", ""),
                "brand": product.get("brand", ""),
                "seller": product.get("seller", ""),
                "delivery": product.get("delivery", ""),
                "original_price": product.get("original_price", ""),
                "tags": product.get("tags", []),
            }
            product_summaries.append(summary)

        # Create prompt for LLM
        prompt = f"""
You are a shopping assistant that needs to rerank products based on relevance to a user's search query.

Search Query: "{query}"

Products to rank:
{product_summaries}

Please analyze each product and rank them from most relevant to least relevant for the search query "{query}".

Consider these factors:
1. Title relevance to the search query
2. Price value and competitiveness
3. Product rating and review count
4. Brand reputation
5. Seller reliability
6. Delivery options
7. Product completeness (description, images, etc.)
8. Special offers (original price vs current price)

Return the ranked product indices in order of relevance (most relevant first).
"""

        # Define the response schema for structured output
        response_schema = {
            "type": "object",
            "properties": {
                "ranked_indices": {
                    "type": "array",
                    "items": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": len(products) - 1,
                    },
                    "description": "Array of product indices in order of relevance (most relevant first)",
                },
                "reasoning": {
                    "type": "string",
                    "description": "Brief explanation of the ranking decisions",
                },
            },
            "required": ["ranked_indices"],
        }

        # Make API request to OpenRouter with structured output
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/tihado/mistral-hackathon",
            "X-Title": "Shopping MCP Server",
        }

        payload = {
            "model": "google/gemini-2.5-flash-lite",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "product_ranking", "schema": response_schema},
            },
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code != 200:
            print(f"OpenRouter API error: {response.status_code} - {response.text}")
            return products[:max_products]

        response.raise_for_status()

        result = response.json()

        # Parse structured response
        try:
            import json

            # Get the structured response content
            response_content = result["choices"][0]["message"]["content"]

            # Parse the JSON response (should be valid JSON due to structured output)
            if isinstance(response_content, str):
                structured_data = json.loads(response_content)
            else:
                structured_data = response_content

            # Extract ranked indices from structured response
            ranked_indices = structured_data.get("ranked_indices", [])
            reasoning = structured_data.get("reasoning", "No reasoning provided")

            print(f"LLM reasoning: {reasoning}")

            # Validate indices
            if not isinstance(ranked_indices, list):
                raise ValueError("ranked_indices is not a list")

            # Validate that all indices are valid
            valid_indices = []
            for idx in ranked_indices:
                if isinstance(idx, int) and 0 <= idx < len(products):
                    valid_indices.append(idx)
                else:
                    print(f"Warning: Invalid index {idx}, skipping")

            # Create reranked products using valid indices
            reranked_products = []
            for idx in valid_indices:
                reranked_products.append(products[idx])

            # Add any remaining products that weren't ranked
            ranked_indices_set = set(valid_indices)
            for i, product in enumerate(products):
                if i not in ranked_indices_set:
                    reranked_products.append(product)

            # Limit to max_products
            final_products = reranked_products[:max_products]

            print(f"LLM reranking: {len(products)} -> {len(final_products)} products")
            return final_products

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Error parsing structured LLM response: {e}")
            print(
                f"Response content: {result.get('choices', [{}])[0].get('message', {}).get('content', 'No content')}"
            )
            return products[:max_products]

    except requests.exceptions.RequestException as e:
        print(f"OpenRouter API request failed: {e}")
        return products[:max_products]
    except Exception as e:
        print(f"Error in LLM reranking: {e}")
        return products[:max_products]


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

        # Apply LLM reranking to improve relevance
        print(f"Applying LLM reranking to {len(combined_results)} products...")
        reranked_results = rerank_products_with_llm(
            combined_results, query, num_results
        )

        print(
            f"Combined search: {len(vector_results)} vector + {len(internet_results)} internet = {len(combined_results)} unique results -> {len(reranked_results)} after LLM reranking"
        )
        return reranked_results

    except Exception as e:
        print(f"Error in combined search: {e}")
        # Fallback to internet search only
        return search_products_serpapi(
            query, num_results, min_price, max_price, free_shipping, on_sale, category
        )
