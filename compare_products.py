from typing import Annotated, List, Dict, Any, TypedDict, Optional


class ComparedProduct(TypedDict):
    """Product data for canvas display after comparison and ranking. Fields are mapped from search_products_tool output."""
    
    # Mapped fields for canvas display (from search_products_tool output)
    name: Annotated[str, "Product name/title for display (mapped from title)"]
    price: Annotated[str, "Product price as string for display (mapped from price)"]
    image: Annotated[str, "Product image URL for canvas display (mapped from image_url)"]
    link: Annotated[str, "Product source URL for navigation (mapped from source_url)"]
    rank: Annotated[int, "Product ranking position (1-5)"]
    seller: Annotated[str, "Seller/store name (mapped from seller)"]
    rating: Annotated[Optional[float], "Product rating (mapped from rating)"]
    reviews_count: Annotated[Optional[int], "Number of reviews (mapped from reviews_count)"]


def compare_products(products: List[Dict[str, Any]]) -> List[ComparedProduct]:
    """
    Compares and ranks products to help users select the best options from search results.
    
    Analyzes products based on price, rating, availability, and completeness to return the top 5 best options.
    Returns products with mapped fields (name, price, image, link, rank, seller, rating, reviews_count) 
    formatted for canvas display.
    """
    
    if not products or not isinstance(products, list):
        return []
    
    def calculate_product_score(prod):
        """Calculate a comprehensive score for product ranking."""
        score = 0
        
        # 1. Price scoring (lower is better, but not the only factor)
        try:
            price_str = str(prod.get("price", "0")).replace("$", "").replace(",", "").strip()
            price = float(price_str) if price_str and price_str != "" else float("inf")
            # Normalize price scoring (inverse relationship)
            if price != float("inf"):
                score += max(0, 1000 - price)  # Higher score for lower prices
        except (ValueError, TypeError):
            pass  # Skip price scoring if invalid
        
        # 2. Rating scoring (higher is better)
        rating = prod.get("rating", 0)
        if rating and rating > 0:
            score += rating * 200  # Strong weight for ratings
        
        # 3. Reviews count (more reviews = more trustworthy)
        reviews_count = prod.get("reviews_count", 0)
        if reviews_count and reviews_count > 0:
            score += min(reviews_count * 0.1, 100)  # Cap at 100 points
        
        # 4. Availability scoring
        in_stock = prod.get("in_stock", True)
        if in_stock:
            score += 500  # Strong preference for in-stock items
        
        # 5. Completeness scoring (images and links are crucial for shopping)
        has_image = 1 if (prod.get("image_url") or prod.get("image")) else 0
        has_link = 1 if (prod.get("source_url") or prod.get("link")) else 0
        completeness = has_image + has_link
        score += completeness * 300  # Strong weight for complete product info
        
        # 6. Brand recognition (if available)
        brand = prod.get("brand", "")
        if brand and brand.strip():
            score += 50  # Small bonus for known brands
        
        # 7. Description quality (if available)
        description = prod.get("description", "")
        if description and len(description.strip()) > 20:
            score += 25  # Small bonus for detailed descriptions
        
        return score
    
    # Sort products by score (highest first)
    sorted_products = sorted(products, key=calculate_product_score, reverse=True)
    top_products = sorted_products[:5]  # Return top 5
    
    # Format products for canvas display
    result = []
    for i, prod in enumerate(top_products, 1):
        # Create a copy to preserve original data
        formatted_product = dict(prod)
        
        # Map fields for canvas display (keep original fields too)
        formatted_product["link"] = formatted_product.get("source_url", "")
        formatted_product["name"] = formatted_product.get("title", "")
        formatted_product["price"] = str(formatted_product.get("price", "N/A")) if formatted_product.get("price") else "N/A"
        formatted_product["rank"] = i
        
        # Map image field (try multiple possible field names)
        image_fields = ["image_url", "thumbnail", "image", "img_url", "photo"]
        formatted_product["image"] = ""
        for field in image_fields:
            if formatted_product.get(field):
                formatted_product["image"] = formatted_product[field]
                break
        
        # Create ComparedProduct with mapped fields only
        compared_product: ComparedProduct = {
            # Mapped fields for canvas display
            "name": formatted_product.get("name", "Unknown Product"),
            "price": formatted_product.get("price", "N/A"),
            "image": formatted_product.get("image", ""),
            "link": formatted_product.get("link", ""),
            "rank": i,
            "seller": formatted_product.get("seller", ""),
            "rating": formatted_product.get("rating"),
            "reviews_count": formatted_product.get("reviews_count")
        }
        result.append(compared_product)
    
    return result
