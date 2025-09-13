import os
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

vector_db = None
embedding_model = None


def initialize_vector_db():
    """Initialize Qdrant and embedding model"""
    global vector_db, embedding_model

    try:
        # Get Qdrant URL from environment variable
        qdrant_url = os.getenv("QDRANT_URL")
        if not qdrant_url:
            raise ValueError("QDRANT_URL environment variable not set")

        # Initialize Qdrant client
        vector_db = QdrantClient(url=qdrant_url)

        # Create collection for products if it doesn't exist
        try:
            vector_db.create_collection(
                collection_name="products",
                vectors_config=VectorParams(
                    size=384,
                    distance=Distance.COSINE,  # all-MiniLM-L6-v2 embedding size
                ),
            )
        except Exception:
            # Collection might already exist, that's okay
            pass

        # Initialize embedding model
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        print("Vector database and embedding model initialized successfully")
    except Exception as e:
        print(f"Error initializing vector database: {e}")
        vector_db = None
        embedding_model = None


def save_product_to_db(product: Dict[str, Any]) -> bool:
    """
    Save a product to the vector database with its embedding.

    Args:
        product: Product dictionary containing product information

    Returns:
        bool: True if successful, False otherwise
    """
    global vector_db, embedding_model

    if not vector_db or not embedding_model:
        return False

    try:
        # Create text representation for embedding
        text_parts = []
        if product.get("title"):
            text_parts.append(product["title"])
        if product.get("description"):
            text_parts.append(product["description"])
        if product.get("brand"):
            text_parts.append(product["brand"])
        if product.get("category"):
            text_parts.append(product["category"])
        if product.get("tags"):
            text_parts.extend(product["tags"])

        text_for_embedding = " ".join(text_parts)

        # Generate embedding
        embedding = embedding_model.encode(text_for_embedding).tolist()

        # Create point ID (use source_url as unique identifier or generate UUID)
        point_id = str(uuid.uuid4())

        # Prepare payload (all product data)
        payload = {
            "title": product.get("title", ""),
            "price": product.get("price", ""),
            "currency": product.get("currency", "USD"),
            "image_url": product.get("image_url", ""),
            "source_url": product.get("source_url", ""),
            "seller": product.get("seller", ""),
            "rating": product.get("rating"),
            "reviews_count": product.get("reviews_count"),
            "description": product.get("description", ""),
            "category": product.get("category", ""),
            "brand": product.get("brand", ""),
            "delivery": product.get("delivery", ""),
            "original_price": product.get("original_price"),
            "tags": product.get("tags", []),
            "in_stock": product.get("in_stock", True),
            "text_for_embedding": text_for_embedding,
        }

        # Create point
        point = PointStruct(id=point_id, vector=embedding, payload=payload)

        # Insert point
        vector_db.upsert(collection_name="products", points=[point])

        print(f"Product saved to vector database: {product.get('title', 'Unknown')}")
        return True

    except Exception as e:
        print(f"Error saving product to vector database: {e}")
        return False


def query_products_from_db(
    query: str,
    limit: int = 10,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Query products from vector database using semantic search.

    Args:
        query: Search query string
        limit: Maximum number of results to return
        category: Optional category filter
        min_price: Optional minimum price filter
        max_price: Optional maximum price filter

    Returns:
        List of product dictionaries matching the query
    """
    global vector_db, embedding_model

    if not vector_db or not embedding_model:
        print("Querying vector database failed: Vector database not initialized")
        return []

    try:
        # Generate embedding for query
        query_embedding = embedding_model.encode(query).tolist()

        # Build filter conditions
        filter_conditions = []

        if category:
            filter_conditions.append(
                FieldCondition(key="category", match=MatchValue(value=category))
            )

        if min_price is not None or max_price is not None:
            # Note: Price filtering would need to be implemented differently
            # as Qdrant doesn't have built-in numeric range filtering
            # For now, we'll do the filtering after retrieval
            pass

        # Perform vector search
        search_result = vector_db.search(
            collection_name="products",
            query_vector=query_embedding,
            limit=limit * 2,  # Get more results to account for filtering
            query_filter=Filter(must=filter_conditions) if filter_conditions else None,
        )

        # Convert results to product format
        products = []
        for result in search_result:
            product = result.payload.copy()
            product["score"] = result.score  # Add similarity score

            # Apply price filtering if needed
            if min_price is not None or max_price is not None:
                try:
                    price_str = (
                        product.get("price", "").replace("$", "").replace(",", "")
                    )
                    price = float(price_str) if price_str else 0

                    if min_price is not None and price < min_price:
                        continue
                    if max_price is not None and price > max_price:
                        continue
                except (ValueError, TypeError):
                    # If price parsing fails, include the product
                    pass

            products.append(product)

        # Limit results
        products = products[:limit]

        print(f"Found {len(products)} products for query: {query}")
        return products

    except Exception as e:
        print(f"Error querying products from vector database: {e}")
        return []


def get_all_products_from_db(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get all products from the vector database.

    Args:
        limit: Maximum number of products to return

    Returns:
        List of all product dictionaries
    """
    global vector_db

    if not vector_db:
        print("Vector database not initialized")
        return []

    try:
        # Get all points from collection
        points = vector_db.scroll(collection_name="products", limit=limit)[
            0
        ]  # scroll returns (points, next_page_offset)

        products = []
        for point in points:
            product = point.payload.copy()
            product["id"] = point.id
            products.append(product)

        print(f"Retrieved {len(products)} products from vector database")
        return products

    except Exception as e:
        print(f"Error getting all products from vector database: {e}")
        return []
