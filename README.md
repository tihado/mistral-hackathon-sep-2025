# Shopping MCP Server with SerpAPI + Virtual Try-On

A comprehensive Model Context Protocol (MCP) server that provides intelligent shopping assistance with real-time product search, virtual try-on capabilities, and personalized recommendations.

## Overview

This MCP server integrates with Google Shopping via SerpAPI to provide real-time product search, comparison, and recommendations. It features semantic search using vector embeddings, virtual try-on for clothing and furniture, and price tracking capabilities. The server is designed to work seamlessly with any MCP-compatible chat client (ChatGPT, Gemini, etc.).

## Features

### 🔍 **Real-Time Product Search**

- Search products using Google Shopping via SerpAPI
- Filter by price range, category, and other criteria
- Returns detailed product information including images, prices, and seller details

### 🧠 **Semantic Search & Recommendations**

- Vector database powered by Qdrant for intelligent product matching
- Personalized recommendations based on user preferences
- Semantic search using sentence transformers

### 📊 **Product Comparison**

- Side-by-side comparison of multiple products
- Price analysis and feature comparison
- Rating and review aggregation

### 👗 **Virtual Try-On**

- AI-powered virtual try-on for clothing and furniture using Google Gemini
- Generate realistic try-on images using both product and user images
- Multi-modal AI generation with personalized results
- Support for both clothing and furniture placement with high-quality image generation

### 💰 **Price Tracking**

- Set up price alerts for products
- Track price changes over time
- Get notifications when prices drop

## Prerequisites

- Install uv (https://docs.astral.sh/uv/getting-started/installation/)
- Python 3.13+
- SerpAPI key (optional, for real product search)

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

```bash
export SERPAPI_KEY="your_serpapi_key_here"
export GEMINI_API_KEY="your_gemini_api_key_here"
```

## Usage

Start the server on port 3000:

```bash
uv run main.py
```

The server will start with mock data if no API keys are provided, making it perfect for testing and development. For full functionality, provide both SerpAPI and Gemini API keys.

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

### `search_products`

Search for products using Google Shopping via SerpAPI.

**Parameters:**

- `query` (string): The search query for products
- `num_results` (int, optional): Number of results to return (default: 10)
- `budget_min` (float, optional): Minimum price filter
- `budget_max` (float, optional): Maximum price filter
- `category` (string, optional): Product category filter

### `compare_products`

Compare multiple products side by side.

**Parameters:**

- `product_ids` (list): List of product IDs to compare

### `recommend_products`

Get personalized product recommendations based on user preferences.

**Parameters:**

- `user_preferences` (string): User preferences, style, or search query
- `num_recommendations` (int, optional): Number of recommendations to return (default: 5)

### `virtual_try_on`

Virtually try on clothing or furniture using AI image generation with both product and user images.

**Parameters:**

- `product_id` (string): ID of the product to try on
- `user_image_data` (string, optional): Base64 encoded user image for try-on
- `try_on_type` (string, optional): Type of try-on: 'clothing' or 'furniture' (default: 'clothing')

### `track_price`

Set up price alerts for products.

**Parameters:**

- `product_id` (string): ID of the product to track
- `target_price` (float): Target price for the alert
- `current_price` (float): Current price of the product

### `get_alerts`

Get all active price alerts.

**Parameters:** None

## Available MCP Resources

### `product://{product_id}`

Get detailed information about a specific product.

## Available MCP Prompts

### `shopping_assistant`

Generate a helpful shopping assistant prompt based on user query and context.

**Parameters:**

- `user_query` (string): User's shopping query or request
- `context` (string, optional): Additional context about the user's needs

## Development

### Architecture

The server uses:

- **FastMCP**: For MCP server implementation
- **Qdrant**: For vector database and semantic search
- **Sentence Transformers**: For text embeddings
- **SerpAPI**: For Google Shopping integration
- **Google Generative AI**: For AI-powered virtual try-on image generation
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
