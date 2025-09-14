# 👗 LeLook: Your AI Shopping Buddy

_Le Chat finds you look_ ✨

A smart Model Context Protocol (MCP) server that turns your chat client into a shopping powerhouse. Search, compare, and virtually try on products without ever leaving your conversation. It's like having a shopping assistant who's always available, never gets tired, and actually remembers what you're looking for.

## What's the Deal? 🤔

This isn't your average "search and find" tool. We've built a **3-step shopping pipeline** that's smoother than a freshly ironed shirt:

1. **🔍 Search** → Find products that actually match what you want
2. **⚖️ Compare** → Let our AI do the heavy lifting of ranking the best options
3. **👗 Try-On** → See how it looks on you (or in your space) before you buy

No more endless scrolling through 47 pages of "similar items" that look nothing like what you searched for. Our AI actually understands what you want and finds the good stuff.

## The Magic Features ✨

### 🔍 **Smart Product Search**

- **Google Shopping Integration**: Real-time product search via SerpAPI
- **Smart Filtering**: Price range, category, free shipping, sale items - you name it
- **Category Support**: Clothing, furniture, phones, and everything else under the sun
- **Rich Data**: Images, prices, ratings, reviews, seller info - the whole shebang

### ⚖️ **AI-Powered Comparison**

- **Smart Ranking**: Our AI actually understands what makes a product good
- **Multi-Criteria Scoring**: Price, ratings, availability, completeness - we consider it all
- **Top 5 Results**: No more decision paralysis from 200+ options
- **Canvas-Ready**: Formatted perfectly for visual comparison grids

### 👗 **Virtual Try-On Magic**

- **AI Image Generation**: Powered by OpenRouter (Google Gemini 2.5 Flash)
- **Multi-Category Support**: Clothing, furniture, phones, and more
- **Flexible Input**: URLs or base64 images - we're not picky
- **Realistic Results**: See how it actually looks on you (or in your space)
- **Cloud Storage**: Generated images saved to AWS S3 for permanent access

### 🧠 **Shopping Assistant**

- **Mandatory Workflow**: Ensures you get the complete shopping experience every time
- **Smart Clarification**: Asks the right questions before searching
- **Canvas Display**: Always shows results in beautiful product grids
- **Image Requirements**: Makes sure you have what you need for try-on

## Prerequisites (The Boring Stuff) 📋

- **uv** (https://docs.astral.sh/uv/getting-started/installation/) - Because pip is so 2020
- **Python 3.13+** - We like our Python fresh and modern
- **SerpAPI key** (optional) - For real product search magic
- **OpenRouter API key** (optional) - For virtual try-on wizardry
- **AWS S3** (optional) - For storing your virtual try-on masterpieces

_Don't have API keys? No worries! The server runs with mock data so you can test everything without spending a dime._

## Installation (Let's Get This Party Started) 🚀

1. **Clone the repository** (obviously):

```bash
git clone <repository-url>
cd mistral-hackathon-sep-2025
```

2. **Install everything** (uv makes this stupidly easy):

```bash
uv python install
uv sync --locked
```

3. **Set up your API keys** (optional but recommended):

Create a `.env` file in the project root:

```bash
# SerpAPI Configuration - Get your key from: https://serpapi.com/
SERPAPI_KEY=your_serpapi_key_here

# OpenRouter API Configuration - Get your key from: https://openrouter.ai/keys
OPENROUTER_API_KEY=your_openrouter_api_key_here

# AWS S3 Configuration (for virtual try-on image storage)
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_S3_BUCKET_NAME=your_s3_bucket_name_here
AWS_REGION=auto
AWS_ENDPOINT_URL="https://..."
AWS_PUBLIC_URL="https://..."
```

_Pro tip: You can also export these as environment variables if you prefer the command line route._

## Usage (Time to Shop!) 🛒

Start the server on port 3000:

```bash
uv run main.py
```

The server will start with mock data if no API keys are provided, making it perfect for testing and development. For full functionality, provide both SerpAPI and OpenRouter API keys.

## Testing Your Shopping Assistant 🧪

### Requirements

- Node.js: ^22.7.5

### Quick Start (UI mode)

To test your shopping assistant with a nice UI:

```bash
npx @modelcontextprotocol/inspector
```

The inspector will be available at http://localhost:6274.

Connect to your server:

- **Transport Type**: Streamable HTTP
- **URL**: http://127.0.0.1:3000/mcp

_Now you can chat with your shopping assistant and see the magic happen!_

## Available MCP Tools (The Shopping Arsenal) 🛠️

### `search_products_tool` 🔍

_The product hunter that actually finds what you're looking for_

**Parameters:**

- `query` (string): What you're looking for (be specific!)
- `category` (string): "clothing", "furniture", "phone", or "other"
- `min_price` (int, optional): Your budget's floor
- `max_price` (int, optional): Your budget's ceiling
- `free_shipping` (bool, optional): Because shipping costs are the worst
- `on_sale` (bool, optional): Who doesn't love a good deal?
- `num_results` (int, optional): How many options you want (default: 10)

**Returns:** A list of products with all the juicy details

### `compare_products_tool` ⚖️

_The AI that does the heavy lifting so you don't have to_

**Parameters:**

- `products` (List[Product]): The products from your search to compare

**Returns:** Top 5 best options with mapped fields (name, price, image, link, rank, seller, rating, reviews_count)

**What it does:** Analyzes products based on price, rating, availability, and completeness to return the top 5 best options formatted for canvas display.

### `virtual_try_on_tool` 👗

_See how it looks before you buy (because returns are annoying)_

**Parameters:**

- `product_description` (string): What the product is
- `product_image_data` (string): Product image (URL or base64)
- `user_image_data` (string): Your image (URL or base64)
- `category` (string): "clothing", "furniture", "phone", or "other"

**Returns:** A generated image showing the virtual try-on result

**Magic:** For clothing (wearing), furniture (room placement), phone (holding), or other (appropriate context)

### `shopping_assistant` 🧠

_The brain that orchestrates your entire shopping experience_

**Parameters:** None (it's smart enough to figure out what you need)

**Returns:** The system prompt that makes everything work together

**The Mandatory 3-Step Workflow:**

1. **🔍 Search** → Find products that match your needs
2. **⚖️ Compare** → Rank and filter to the best options
3. **👗 Try-On** → See how it looks on you (or in your space)

**Key Features:**

- Always displays results in beautiful canvas grids
- Asks the right questions before searching
- Makes sure you have what you need for try-on
- Never skips steps (because incomplete shopping is sad shopping)

**Example Shopping Flow:**

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

## Development (For the Nerds) 🔧

### Architecture

The server is built with modern Python and follows a clean separation of concerns:

- **FastMCP**: MCP server implementation (because we like things fast)
- **SerpAPI**: Google Shopping integration (the real deal)
- **OpenRouter**: AI-powered virtual try-on using Google Gemini 2.5 Flash
- **AWS S3**: Cloud storage for generated images (because local storage is so 2010)
- **Pydantic**: Data validation (because type safety is sexy)
- **TypedDict**: Type hints that actually work (no more runtime surprises)

### File Structure

```
├── main.py                    # MCP server with tool decorators
├── search_products.py         # Product search logic
├── compare_products.py        # Product comparison & ranking
├── virtual_try_on.py          # AI image generation
└── README.md                  # This masterpiece
```

### Mock Data Mode

No API keys? No problem! The server runs with realistic mock data, so you can test everything without spending a penny. Perfect for development and demos.

### Extending the Server

Want to add more shopping superpowers? Easy peasy:

1. **New Tools**: Add `@mcp.tool` decorated functions
2. **New Logic**: Create new Python files following the same pattern
3. **New Features**: The sky's the limit (wishlist, order tracking, price alerts, etc.)

The architecture is designed to be easily extensible. Just follow the existing patterns and you'll be adding features faster than you can say "add to cart"!

## Contributors (The Dream Team) 👥

This shopping assistant wouldn't exist without these amazing developers:

- **[@nvti](https://github.com/nvti)**
- **[@honghanhh](https://github.com/honghanhh)**

_Want to join the team? We're always looking for more shopping enthusiasts!_ 🛍️
