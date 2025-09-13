# Shopping MCP Server with SerpAPI + Virtual Try-On

A comprehensive Model Context Protocol (MCP) server that provides intelligent shopping assistance with real-time product search, virtual try-on capabilities, and personalized recommendations.

## Overview

This MCP server integrates with Google Shopping via SerpAPI to provide real-time product search, comparison, and recommendations. It features semantic search using vector embeddings, virtual try-on for clothing and furniture, and price tracking capabilities. The server is designed to work seamlessly with any MCP-compatible chat client (ChatGPT, Gemini, etc.).

## Features

### 🔍 **Real-Time Product Search**

- Search products using Google Shopping via SerpAPI
- Filter by price range, category, and other criteria
- Returns detailed product information including images, prices, and seller details

### 🧠 **Semantic Search & Vector Database**

- **Vector Database Integration**: Powered by Qdrant for intelligent product matching and storage
- **Semantic Search**: Find products using natural language queries with sentence transformers
- **Product Persistence**: Automatically save searched products to vector database for future retrieval
- **Hybrid Search**: Choose between searching saved products (vector DB) or discovering new ones (internet)
- **Smart Filtering**: Filter by category, price range, and other criteria with semantic understanding

### 📊 **Product Comparison**

- Side-by-side comparison of multiple products
- Price analysis and feature comparison
- Rating and review aggregation

### 👗 **Virtual Try-On**

- AI-powered virtual try-on for clothing, furniture, and other items using OpenRouter (Google Gemini 2.5 Flash)
- Generate realistic try-on images using both product and user images
- Multi-modal AI generation with personalized results
- Support for both clothing and furniture placement with high-quality image generation
- Flexible image input: supports both URLs and base64 encoded data for product and user images
- **Persistent Storage**: Generated images are automatically uploaded to AWS S3 for permanent storage and public access

### 💰 **Price Tracking**

- Set up price alerts for products
- Track price changes over time
- Get notifications when prices drop

## Prerequisites

- Install uv (https://docs.astral.sh/uv/getting-started/installation/)
- Python 3.13+
- SerpAPI key (optional, for real product search)
- Qdrant vector database (local or cloud instance)

### Setting up Qdrant Vector Database

**Option 1: Local Qdrant (Recommended for development)**

```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant

# Or using Docker Compose
echo "version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant
    ports:
      - '6333:6333'
    volumes:
      - qdrant_storage:/qdrant/storage
volumes:
  qdrant_storage:" > docker-compose.yml
docker-compose up -d
```

**Option 2: Cloud Qdrant (For production)**

1. Sign up at [Qdrant Cloud](https://cloud.qdrant.io/)
2. Create a cluster
3. Get your cluster URL and API key
4. Set the environment variables in your `.env` file

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd shopping-mcp
```

2. Install python version & dependencies:

```bash
uv python install
uv sync --locked
```

3. Set up environment variables (optional):

Create a `.env` file in the project root:

```bash
# SerpAPI Configuration
# Get your API key from: https://serpapi.com/
SERPAPI_KEY=your_serpapi_key_here

# OpenRouter API Configuration
# Get your API key from: https://openrouter.ai/keys
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Qdrant Vector Database Configuration
# For local Qdrant instance (default)
QDRANT_URL=http://localhost:6333

# For cloud Qdrant instance (optional)
# QDRANT_URL=https://your-cluster-url.eu-central.aws.cloud.qdrant.io:6333
# QDRANT_API_KEY=your_qdrant_api_key_here

# AWS S3 Configuration (for virtual try-on image storage)
# Get your credentials from: https://aws.amazon.com/
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_S3_BUCKET_NAME=your_s3_bucket_name_here
AWS_REGION=auto
AWS_ENDPOINT_URL="https://..."
AWS_PUBLIC_URL="https://..."
```

Or export them directly:

```bash
export SERPAPI_KEY="your_serpapi_key_here"
export OPENROUTER_API_KEY="your_openrouter_api_key_here"
export AWS_ACCESS_KEY_ID="your_aws_access_key_here"
export AWS_SECRET_ACCESS_KEY="your_aws_secret_key_here"
export AWS_S3_BUCKET_NAME="your_s3_bucket_name_here"
export AWS_REGION="auto"
export AWS_ENDPOINT_URL="https://..."
export AWS_PUBLIC_URL="https://..."
```

## Usage

Start the server on port 3000:

```bash
uv run main.py
```

The server will start with mock data if no API keys are provided, making it perfect for testing and development. For full functionality, provide both SerpAPI and OpenRouter API keys.

## Running the Inspector

### Requirements

- Node.js: ^22.7.5

### Quick Start (UI mode)

To get up and running right away with the UI, just execute the following:

```bash
npx @modelcontextprotocol/inspector
```

The inspector server will start up and the UI will be accessible at http://localhost:6274.

You can test your server locally by selecting:

- Transport Type: Streamable HTTP
- URL: http://127.0.0.1:3000/mcp

## Available MCP Tools

### `search_products_tool`

Search for products using Google Shopping via SerpAPI.

**Parameters:**

- `query` (string): The search query for the desired products
- `category` (string): The product category to filter results. Must be "clothing", "furniture", or "other"
- `min_price` (int, optional): The minimum price for filtering products
- `max_price` (int, optional): The maximum price for filtering products
- `free_shipping` (bool, optional): Whether to filter products with free shipping
- `on_sale` (bool, optional): Whether to filter products on sale
- `num_results` (int, optional): The number of product results to return (default: 10)

**Returns:**

- `List[dict]`: A list of product information dictionaries

### `compare_products_tool`

Compare products side by side based on different criteria and return the top 5 best options.

**Parameters:**

- `products` (List[Dict[str, Any]]): List of product dictionaries as returned by search_products_tool to compare and rank

**Returns:**

- `List[Dict[str, Any]]`: Top 5 product options with basic info, price, link, and image

### `virtual_try_on_tool`

Virtually try on a product using AI image generation with OpenRouter (Google Gemini 2.5 Flash).

**Parameters:**

- `product_image_data` (string): The product image as URL or base64 encoded data to try on
- `user_image_data` (string): The user image as URL or base64 encoded data to try on
- `category` (string, optional): The type of virtual try-on: 'clothing' for wearing items, 'furniture' for room placement, or 'other' for general items (default: 'clothing')

**Features:**

- For clothing: Shows the person wearing the clothing item
- For furniture: Shows the furniture item placed in a realistic room setting
- For other: Shows the item in an appropriate context
- Supports both URL and base64 encoded image data for both product and user images

### `shopping_assistant`

Always use this prompt for users who want to find, compare, or try on any shopping-related product. The assistant must always use this prompt for all shopping queries.

**Parameters:** None

**Returns:**

- `dict`: Contains the system prompt for the shopping assistant

**Workflow:**
The shopping assistant follows a specific workflow:

1. **search_products_tool** → Search for products based on user query
2. **compare_products_tool** → Compare and rank the search results
3. **virtual_try_on_tool** → Allow users to virtually try on selected products

**Key Features:**

- Always displays results in a canvas/grid layout with product images, names, prices, and links as cards or tiles
- Clarifies user preferences before searching (color, price range, style, brand, size)
- Requires both product and user images for virtual try-on
- Supports different categories: clothing, furniture, and other items
- Asks for user photos when needed (portrait for clothing, room photos for furniture/other)
- Never proceeds with virtual try-on until both images are provided

**Example Usage Flow:**

```
User: "I'm looking for a dress"
Assistant: "What color, style, or price range do you prefer? Any specific brand?"

User: "A red dress under $100"
Assistant: [Calls search_products_tool] → [Calls compare_products_tool] → Shows product grid

User: "I like the second dress. Can I see how it looks on me?"
Assistant: "Please upload your portrait or provide a URL to your photo"
User: [Provides photo]
Assistant: [Calls virtual_try_on_tool with both images, category="clothing"]
```

## Development

### Architecture

The server uses:

- **FastMCP**: For MCP server implementation
- **Qdrant**: For vector database and semantic search
- **Sentence Transformers**: For text embeddings
- **SerpAPI**: For Google Shopping integration
- **OpenRouter**: For AI-powered virtual try-on image generation using Google Gemini 2.5 Flash
- **AWS S3**: For persistent storage of generated virtual try-on images
- **PIL**: For image processing and fallback virtual try-on
- **Pydantic**: For data validation and serialization

### Mock Data Mode

When no SerpAPI key is provided, the server runs in mock data mode, providing realistic sample data for testing and development. This makes it easy to test the MCP tools without requiring API keys.

### Extending the Server

To add new functionality:

1. **New Tools**: Add new `@mcp.tool` decorated functions
2. **New Resources**: Add new `@mcp.resource` decorated functions
3. **New Prompts**: Add new `@mcp.prompt` decorated functions

The server is designed to be easily extensible with additional shopping features like wishlist management, order tracking, or integration with other e-commerce APIs.
