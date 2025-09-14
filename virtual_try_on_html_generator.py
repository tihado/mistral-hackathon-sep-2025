"""
HTML Generator for Virtual Try-On Results
"""

from typing import Dict, Any, Optional
import json
import base64
from urllib.parse import quote


def generate_virtual_try_on_html(
    product_image_data: str,
    user_image_data: str,
    result_image_data: str,
) -> str:
    """
    Generate HTML for displaying virtual try-on results.

    Args:
        product_image_data: Product image as URL or base64 data
        user_image_data: User image as URL or base64 data
        result_image_data: Generated result image as URL or base64 data
        product_description: Description of the product
        category: Product category (clothing, furniture, phone, other)
        success: Whether the virtual try-on was successful
        ai_generated: Whether the result was AI generated
        error: Error message if any
        **kwargs: Additional data to include

    Returns:
        Complete HTML string for displaying virtual try-on results
    """

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Virtual Try-On Results</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 300;
        }}

        .header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}

        .content {{
            padding: 40px;
        }}

        .image-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }}

        .image-card {{
            background: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .image-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
        }}

        .image-card h3 {{
            color: #333;
            margin-bottom: 15px;
            font-size: 1.3rem;
            font-weight: 600;
        }}

        .image-label {{
            color: #6c757d;
            font-size: 0.9rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
            text-align: center;
        }}

        .image-container {{
            position: relative;
            width: 100%;
            height: 300px;
            border-radius: 10px;
            overflow: hidden;
            background: #e9ecef;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .image-container img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: cover;
            border-radius: 10px;
            transition: transform 0.3s ease;
        }}

        .image-container img:hover {{
            transform: scale(1.05);
        }}

        .loading-placeholder {{
            color: #6c757d;
            font-size: 1.1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
        }}

        .result-card {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(40, 167, 69, 0.3);
            position: relative;
            overflow: hidden;
        }}

        .result-card::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            transform: rotate(45deg);
            animation: shimmer 3s infinite;
        }}

        @keyframes shimmer {{
            0% {{ transform: translateX(-100%) translateY(-100%) rotate(45deg); }}
            100% {{ transform: translateX(100%) translateY(100%) rotate(45deg); }}
        }}

        .result-card h3 {{
            font-size: 1.5rem;
            margin-bottom: 15px;
            position: relative;
            z-index: 1;
        }}

        .result-image-container {{
            position: relative;
            width: 100%;
            height: 400px;
            border-radius: 10px;
            overflow: hidden;
            background: rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1;
        }}

        .result-image-container img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: cover;
            border-radius: 10px;
            transition: transform 0.3s ease;
        }}

        .result-image-container img:hover {{
            transform: scale(1.05);
        }}

        .product-info {{
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            margin-top: 30px;
        }}

        .product-info h4 {{
            color: #333;
            margin-bottom: 15px;
            font-size: 1.4rem;
        }}

        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}

        .info-item {{
            display: flex;
            flex-direction: column;
        }}

        .info-label {{
            font-weight: 600;
            color: #6c757d;
            margin-bottom: 5px;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .info-value {{
            color: #333;
            font-size: 1.1rem;
        }}

        .error-message {{
            background: #f8d7da;
            color: #721c24;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 20px 0;
        }}

        .success-badge {{
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 15px;
        }}

        .category-badge {{
            display: inline-block;
            background: #6c757d;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            margin-left: 10px;
        }}

        @media (max-width: 768px) {{
            .image-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
            
            .content {{
                padding: 20px;
            }}
        }}

        .fade-in {{
            animation: fadeIn 0.6s ease-in;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Virtual Try-On Results</h1>
            <p>See how the product looks on you!</p>
        </div>
        
        <div class="content">
            <div class="image-grid">
                <!-- Product Image Card -->
                <div class="image-card fade-in">
                    <div class="image-container">
                        <img src="{product_image_data}" alt="Product Image">
                    </div>
                </div>

                <!-- User Image Card -->
                <div class="image-card fade-in">
                    <div class="image-container">
                        <img src="{user_image_data}" alt="User Image">
                    </div>
                </div>
            </div>

            <!-- Virtual Try-On Result -->
            <div class="result-card fade-in">
                <h3>Virtual Try-On Result</h3>
                <div class="result-image-container">
                    <img src="{result_image_data}" alt="Virtual Try-On Result">
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""

    return html_template


def generate_virtual_try_on_html_from_result(
    virtual_try_on_result: Dict[str, Any],
    product_image_data: str,
    user_image_data: str,
) -> str:
    """
    Generate HTML from a virtual try-on result dictionary.

    Args:
        virtual_try_on_result: Result from virtual_try_on function
        product_image_data: Product image as URL or base64 data
        user_image_data: User image as URL or base64 data
        product_description: Description of the product

    Returns:
        Complete HTML string for displaying virtual try-on results
    """

    return generate_virtual_try_on_html(
        product_image_data=product_image_data,
        user_image_data=user_image_data,
        result_image_data=virtual_try_on_result.get("result_image_data", ""),
    )
