from typing import Annotated, List, Dict, Any, TypedDict, Optional
import html


class ComparedProduct(TypedDict):
    """Product data for canvas display after comparison and ranking. Fields are mapped from search_products_tool output."""

    # Mapped fields for canvas display (from search_products_tool output)
    name: Annotated[str, "Product name/title for display (mapped from title)"]
    price: Annotated[str, "Product price as string for display (mapped from price)"]
    image: Annotated[
        str, "Product image URL for canvas display (mapped from image_url)"
    ]
    link: Annotated[str, "Product source URL for navigation (mapped from source_url)"]
    rank: Annotated[int, "Product ranking position (1-5)"]
    seller: Annotated[str, "Seller/store name (mapped from seller)"]
    rating: Annotated[Optional[float], "Product rating (mapped from rating)"]
    reviews_count: Annotated[
        Optional[int], "Number of reviews (mapped from reviews_count)"
    ]


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
            price_str = (
                str(prod.get("price", "0")).replace("$", "").replace(",", "").strip()
            )
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
        formatted_product["price"] = (
            str(formatted_product.get("price", "N/A"))
            if formatted_product.get("price")
            else "N/A"
        )
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
            "reviews_count": formatted_product.get("reviews_count"),
        }
        result.append(compared_product)

    return result


def generate_html_table(
    compared_products: List[ComparedProduct], title: str = "Product Comparison Results"
) -> str:
    """
    Generate an HTML table from compared products for display.

    Args:
        compared_products: List of ComparedProduct objects
        title: Title for the HTML table

    Returns:
        HTML string containing a styled table with product information
    """
    if not compared_products:
        return "<p>No products to display.</p>"

    # Start building the HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{html.escape(title)}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2em;
                font-weight: 300;
            }}
            .table-container {{
                overflow-x: auto;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 0;
            }}
            th {{
                background-color: #f8f9fa;
                color: #495057;
                font-weight: 600;
                padding: 15px 10px;
                text-align: left;
                border-bottom: 2px solid #dee2e6;
                position: sticky;
                top: 0;
            }}
            td {{
                padding: 15px 10px;
                border-bottom: 1px solid #dee2e6;
                vertical-align: top;
            }}
            td:nth-child(3) {{
                text-align: center;
            }}
            tr:hover {{
                background-color: #f8f9fa;
            }}
            .product-image {{
                width: 100px;
                height: 100px;
                object-fit: cover;
                border-radius: 8px;
                border: 2px solid #e9ecef;
                display: block;
                margin: 0 auto;
            }}
            .product-name {{
                font-weight: 600;
                color: #212529;
                margin-bottom: 5px;
                line-height: 1.4;
            }}
            .product-price {{
                font-size: 1.2em;
                font-weight: 700;
                color: #28a745;
                margin-bottom: 5px;
            }}
            .product-seller {{
                color: #6c757d;
                font-size: 0.9em;
            }}
            .product-rating {{
                display: flex;
                align-items: center;
                gap: 5px;
                margin-bottom: 5px;
            }}
            .stars {{
                color: #ffc107;
                font-size: 1.1em;
            }}
            .rating-text {{
                color: #6c757d;
                font-size: 0.9em;
            }}
            .rank-badge {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 8px 12px;
                border-radius: 20px;
                font-weight: 600;
                font-size: 0.9em;
                text-align: center;
                min-width: 40px;
            }}
            .product-link {{
                display: inline-block;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 0.9em;
                font-weight: 500;
                transition: background-color 0.3s;
            }}
            .product-link:hover {{
                background-color: #0056b3;
                text-decoration: none;
                color: white;
            }}
            .no-image {{
                width: 100px;
                height: 100px;
                background-color: #e9ecef;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #6c757d;
                font-size: 0.8em;
                text-align: center;
                margin: 0 auto;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #6c757d;
                border-top: 1px solid #dee2e6;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{html.escape(title)}</h1>
                <p>Top {len(compared_products)} Product Recommendations</p>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Price</th>
                            <th>Image</th>
                            <th>Link</th>
                            <th>Seller</th>
                            <th>Rating</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    # Add product rows
    for product in compared_products:
        # Handle product image
        image_html = ""
        if product.get("image"):
            image_html = f'<img src="{html.escape(product["image"])}" alt="{html.escape(product.get("name", "Product"))}" class="product-image" onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'flex\';">'
            image_html += f'<div class="no-image" style="display:none;">No Image</div>'
        else:
            image_html = '<div class="no-image">No Image</div>'

        # Handle rating display
        rating_html = ""
        if product.get("rating") and product["rating"] > 0:
            stars = "★" * int(product["rating"])
            reviews_text = (
                f"({product.get('reviews_count', 0)} reviews)"
                if product.get("reviews_count")
                else ""
            )
            rating_html = f"""
                <div class="product-rating">
                    <span class="stars">{stars}</span>
                    <span class="rating-text">{product["rating"]:.1f} {reviews_text}</span>
                </div>
            """
        else:
            rating_html = '<div class="rating-text">No rating</div>'

        # Handle product link
        link_html = ""
        if product.get("link"):
            link_html = f'<a href="{html.escape(product["link"])}" target="_blank" class="product-link">View Product</a>'
        else:
            link_html = '<span class="rating-text">No link available</span>'

        # Add the row
        html_content += f"""
                        <tr>
                            <td><div class="product-name">{html.escape(product.get("name", "Unknown Product"))}</div></td>
                            <td><div class="product-price">{html.escape(product.get("price", "N/A"))}</div></td>
                            <td>{image_html}</td>
                            <td>{link_html}</td>
                            <td><div class="product-seller">{html.escape(product.get("seller", "Unknown Seller"))}</div></td>
                            <td>{rating_html}</td>
                        </tr>
        """

    # Close the HTML
    html_content += """
                    </tbody>
                </table>
            </div>
            <div class="footer">
                <p>Generated by Shopping Assistant • Click "View Product" to visit the store</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html_content
