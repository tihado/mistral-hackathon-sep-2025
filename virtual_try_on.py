import os
import requests
import json
import base64
import uuid
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from typing import Literal
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

load_dotenv()


def get_openrouter_api_key():
    """Get OpenRouter API key from environment variable"""
    return os.getenv("OPENROUTER_API_KEY", "your_openrouter_api_key_here")


def get_aws_config():
    """Get AWS configuration from environment variables"""
    return {
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "region_name": os.getenv("AWS_REGION", "us-east-1"),
        "bucket_name": os.getenv("AWS_S3_BUCKET_NAME"),
        "endpoint_url": os.getenv("AWS_ENDPOINT_URL", None),
        "public_url": os.getenv("AWS_PUBLIC_URL"),
    }


def get_s3_client():
    """Get S3 client with proper configuration"""
    config = get_aws_config()

    if not config["aws_access_key_id"] or not config["aws_secret_access_key"]:
        raise NoCredentialsError(
            "AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables."
        )

    if not config["bucket_name"]:
        raise ValueError("AWS_S3_BUCKET_NAME environment variable not set.")

    return boto3.client(
        "s3",
        aws_access_key_id=config["aws_access_key_id"],
        aws_secret_access_key=config["aws_secret_access_key"],
        region_name=config["region_name"],
        endpoint_url=config["endpoint_url"] if config["endpoint_url"] else None,
    )


def generate_image_with_openrouter(
    api_key: str, prompt: str, image_urls: list
) -> Optional[str]:
    """Generate image using OpenRouter with Gemini model"""
    try:
        # Prepare the content array with text and images
        content = [{"type": "text", "text": prompt}]

        # Add image URLs to content
        for i, image_url in enumerate(image_urls):
            content.append({"type": "image_url", "image_url": {"url": image_url}})

        # Prepare the request payload
        payload = {
            "model": "google/gemini-2.5-flash-image-preview",
            "messages": [{"role": "user", "content": content}],
            "temperature": 0.7,
        }

        # Make the request to OpenRouter
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Title": "LeLook MCP Server",
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=60,
        )

        response.raise_for_status()
        result = response.json()

        # Extract the generated image from the response
        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                # The response should contain the generated image data
                images = choice["message"]["images"]

                if images and len(images) > 0:
                    image_url = images[0]["image_url"]["url"]
                    return image_url

        return None

    except Exception as e:
        print(f"Error generating image with OpenRouter: {e}")
        return None


def upload_image_to_s3(image_data: str) -> str:
    """
    Upload image to S3 and return the public URL.

    Args:
        image_data: Image data as URL, base64 string, or data URL

    Returns:
        str: Public URL of the uploaded image

    Raises:
        NoCredentialsError: If AWS credentials are not configured
        ValueError: If required environment variables are missing
        ClientError: If S3 upload fails
    """
    try:
        # If it's already a URL, return it
        if is_url(image_data):
            return image_data

        # Get S3 client and configuration
        s3_client = get_s3_client()
        config = get_aws_config()
        bucket_name = config["bucket_name"]

        # Generate unique key for the image
        image_key = f"virtual-try-on/{uuid.uuid4()}.png"

        # Handle different image data formats
        if image_data.startswith("data:image"):
            # Data URL format: data:image/png;base64,/9j/4AAQSkZJRgABAQAAAQ...
            header, encoded_data = image_data.split(",", 1)
            image_bytes = base64.b64decode(encoded_data)

            # Extract content type from data URL
            content_type = header.split(";")[0].split(":")[1]  # image/png
        else:
            # Assume it's base64 encoded data
            image_bytes = base64.b64decode(image_data)
            content_type = "image/png"

        # Upload to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=image_key,
            Body=image_bytes,
            ContentType=content_type,
            ACL="public-read",  # Make the image publicly accessible
        )

        # Generate public URL
        public_url = f"{config['public_url']}/{image_key}"

        print(f"Successfully uploaded image to S3: {public_url}")
        return public_url

    except NoCredentialsError as e:
        print(f"AWS credentials error: {e}")
        # Fallback: return original data if it's a URL, otherwise return as-is
        return image_data if is_url(image_data) else image_data

    except ValueError as e:
        print(f"Configuration error: {e}")
        # Fallback: return original data if it's a URL, otherwise return as-is
        return image_data if is_url(image_data) else image_data

    except ClientError as e:
        print(f"S3 upload error: {e}")
        # Fallback: return original data if it's a URL, otherwise return as-is
        return image_data if is_url(image_data) else image_data

    except Exception as e:
        print(f"Unexpected error uploading to S3: {e}")
        # Fallback: return original data if it's a URL, otherwise return as-is
        return image_data if is_url(image_data) else image_data


def is_url(image_data: str) -> bool:
    """Check if the input is a URL"""
    return image_data.startswith(("http://", "https://"))


def create_clothing_try_on_prompt(product_description: str = "clothing item") -> str:
    """Create a prompt for clothing virtual try-on"""
    return f"""Create a realistic image showing this person wearing this {product_description}. 
    The person should be wearing the clothing item naturally and comfortably. 
    The image should be high quality, well-lit, and show the clothing fitting properly on the person. 
    Make sure the clothing looks natural and realistic on the person."""


def create_furniture_try_on_prompt(product_description: str = "furniture item") -> str:
    """Create a prompt for furniture virtual try-on/placement"""
    return f"""Create a realistic image showing this {product_description} placed in a modern, well-lit room. 
    The furniture should be positioned naturally in the space and complement the room's decor. 
    The image should be high quality, well-lit, and show the furniture fitting well in the room environment. 
    Make sure the furniture looks natural and realistic in the room setting."""


def create_phone_try_on_prompt(product_description: str = "phone item") -> str:
    """Create a prompt for phone virtual try-on"""
    return f"""Create a realistic image showing this person holding this {product_description}. 
    The person should be holding the phone naturally and comfortably. 
    The image should be high quality, well-lit, and show the phone fitting properly in the person's hand. 
    Make sure the phone looks natural and realistic in the person's hand."""


def create_car_try_on_prompt(product_description: str = "car") -> str:
    """Create a prompt for car virtual try-on/visualization"""
    return f"""Create a realistic image showing this {product_description} parked in a modern, well-lit driveway or street setting. 
    The car should be positioned naturally in the environment and complement the surrounding area. 
    The image should be high quality, well-lit, and show the car fitting well in the realistic setting. 
    Make sure the car looks natural and realistic in the driveway/street environment."""


def create_house_try_on_prompt(product_description: str = "house") -> str:
    """Create a prompt for house virtual try-on/visualization"""
    return f"""Create a realistic image showing this {product_description} placed in a modern, well-lit neighborhood setting. 
    The house should be positioned naturally in the environment and complement the surrounding neighborhood. 
    The image should be high quality, well-lit, and show the house fitting well in the realistic neighborhood setting. 
    Make sure the house looks natural and realistic in the neighborhood environment."""


def create_other_try_on_prompt(product_description: str = "other item") -> str:
    """Create a prompt for other virtual try-on"""
    return f"""Create a realistic image showing this {product_description} placed in a modern, well-lit room. 
    The {product_description} should be positioned naturally in the space and complement the room's decor. 
    The image should be high quality, well-lit, and show the {product_description} fitting well in the room environment. 
    Make sure the {product_description} looks natural and realistic in the room setting."""


def virtual_try_on(
    product_description: str,
    product_image_data: str,
    user_image_data: str,
    category: Literal["clothing", "furniture", "other", "phone", "car", "house"],
) -> Dict[str, Any]:
    """
    Virtually try on a product using AI image generation with both product and user images.

    Args:
        product_image_data: Product image as URL or base64 encoded data
        user_image_data: User image as URL or base64 encoded data (optional)
        category: Type of try-on - "clothing", "furniture", "other", "phone", "car", or "house"

    Returns:
        Dict containing the result image data and metadata
    """
    try:
        # Get OpenRouter API key
        api_key = get_openrouter_api_key()
        if api_key == "your_openrouter_api_key_here":
            # mock data for testing
            return {
                "result_image_data": "https://cdn.tihado.com/virtual-try-on/2c4c2643-64ff-4979-869d-9044dd206003.png",
                "success": True,
                "category": category,
            }

        # Validate and prepare image URLs for OpenRouter
        image_urls = []

        # Process product image - convert to URL if needed
        if is_url(product_image_data):
            image_urls.append(product_image_data)
        else:
            # For base64 data, we need to convert it to a data URL
            if product_image_data.startswith("data:image"):
                image_urls.append(product_image_data)
            else:
                # Convert base64 to data URL
                image_urls.append(f"data:image/jpeg;base64,{product_image_data}")

        # Add user image if provided
        if user_image_data:
            if is_url(user_image_data):
                image_urls.append(user_image_data)
            else:
                # For base64 data, convert to data URL
                if user_image_data.startswith("data:image"):
                    image_urls.append(user_image_data)
                else:
                    # Convert base64 to data URL
                    image_urls.append(f"data:image/jpeg;base64,{user_image_data}")

        # Create appropriate prompt based on try-on type
        if category == "furniture":
            prompt = create_furniture_try_on_prompt(product_description)
        elif category == "other":
            prompt = create_other_try_on_prompt(product_description)
        elif category == "phone":
            prompt = create_phone_try_on_prompt(product_description)
        elif category == "car":
            prompt = create_car_try_on_prompt(product_description)
        elif category == "house":
            prompt = create_house_try_on_prompt(product_description)
        else:
            prompt = create_clothing_try_on_prompt(product_description)

        # Generate image using OpenRouter with URLs
        try:
            generated_image_data = generate_image_with_openrouter(
                api_key, prompt, image_urls
            )

            if generated_image_data:
                # Upload the generated image to S3 for persistent storage
                uploaded_image_url = upload_image_to_s3(generated_image_data)

                return {
                    "result_image_data": uploaded_image_url,
                    "success": True,
                    "category": category,
                    "ai_generated": True,
                    "s3_uploaded": uploaded_image_url != generated_image_data,
                }
            else:
                # Fallback if no image generated
                return {
                    "error": "Failed to generate try-on image",
                    "result_image_data": product_image_data,
                    "fallback": True,
                }

        except Exception as e:
            print(f"Error generating image with OpenRouter: {e}")
            return {
                "error": f"Image generation failed: {str(e)}",
                "result_image_data": product_image_data,
                "fallback": True,
            }

    except Exception as e:
        print(f"Error in virtual_try_on: {e}")
        return {
            "error": f"Virtual try-on failed: {str(e)}",
            "result_image_data": product_image_data,
            "fallback": True,
        }
