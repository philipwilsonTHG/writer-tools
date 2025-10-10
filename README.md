# Horizon API Python Utilities for Writer Agents

Python utilities for querying the Horizon GraphQL API from Writer AI Studio agent code blocks. These tools simplify product data retrieval from THG e-commerce subsites (MyProtein, Lookfantastic, etc.).

## Overview

The Horizon API is THG's enterprise e-commerce platform GraphQL API. These utilities provide easy-to-use Python functions for:

- Searching for products by keyword
- Fetching product lists from category pages
- Retrieving detailed product information
- Executing custom GraphQL queries

## Quick Start

### 1. Upload to Writer Agent Builder

In your Writer agent's code editor (Little `> Code` button on the bottom left):
1. Upload `horizon_client.py`
2. Upload `horizon_fetcher.py`

### 2. Use in Python Code Blocks

Add a Python code block to your agent blueprint and import the utilities:

```python
from horizon_fetcher import get_product_ids, get_product_json

# Search for products
product_ids = get_product_ids("whey protein", limit=50)

# Get detailed product data
product_data = get_product_json(product_ids[0])

# Return to agent
set_output(product_data)
```

## Common Patterns

### Fetching Product IDs from a PLP URL

This pattern fetches product IDs from a Product List Page (PLP) URL stored in agent state, saves them back to state, and returns them as output:

```python
from horizon_fetcher import get_product_ids

# Get PLP URL from agent state
product_ids = get_product_ids(state['plp_url'], 100)

# Store in state for use in subsequent blocks
state['product_id_list'] = product_ids

# Return to agent
set_output(product_ids)
```

**Use case:** The agent collects a category URL from the user (e.g., `https://www.myprotein.com/c/nutrition/protein/whey-protein/`), fetches all product IDs from that page, stores them in state for later processing, and returns the list to display or use in subsequent blueprint blocks.

### Fetching Product Details with Fallback

This pattern retrieves detailed product data for a specific product ID, with a fallback to a default product if no ID is provided in state:

```python
from horizon_fetcher import get_product_json

# Check if product ID is in state, otherwise use default
if "item_to_fetch" in state:
    product_id = state["item_to_fetch"]
else:
    product_id = 10530943

try:
    # Ensure product_id is an integer
    product_id = int(product_id)
    product_json = get_product_json(product_id)
    set_output(product_json)

except Exception as e:
    logger.info(f"Error: {e}")
```

**Use case:** The agent fetches full product details (title, variants, images, content fields) for a specific product. If the user or a previous blueprint block has set `item_to_fetch` in state, it uses that product ID; otherwise, it falls back to a default product for demonstration or testing purposes.

**Error handling:** Wraps the API call in a try-except block to handle invalid product IDs, network errors, or API issues gracefully by logging the error.

## Core Functions

### `get_product_ids(url_or_search_term, limit=100, offset=0, currency='GBP', shippingDestination='GB', sort='RELEVANCE')`

Auto-detects whether input is a URL or search term and returns matching product IDs.

**Examples:**

```python
# Search by keyword
product_ids = get_product_ids("protein powder")

# Fetch from category URL
product_ids = get_product_ids("https://www.myprotein.com/c/nutrition/protein/whey-protein/")

# Limit results
product_ids = get_product_ids("creatine", limit=20)

# Use pagination and custom currency
product_ids = get_product_ids("whey protein", limit=50, offset=50, currency='USD', shippingDestination='US')
```

**Returns:** List of product IDs (integers)

### `get_product_json(product_id, subsite='www.myprotein.com')`

Fetches complete product data including title, content fields, variants, and images.

**Example:**

```python
product_data = get_product_json(12345678, "www.myprotein.com")
```

**Returns:** JSON string with full product details

### `get_product_list(product_list_path, subsite='www.myprotein.com', limit=100, offset=0, currency='GBP', shippingDestination='GB', sort='RELEVANCE')`

Fetches products from a category/collection page.

**Examples:**

```python
# Basic usage - Remove /c prefix from URL path
response = get_product_list("nutrition/protein/whey-protein/", "www.myprotein.com")

# With pagination and custom settings
response = get_product_list(
    "nutrition/vitamins/",
    "www.myprotein.com",
    limit=50,
    offset=50,
    currency='USD',
    shippingDestination='US',
    sort='PRICE_LOW_TO_HIGH'
)
```

**Returns:** JSON string with product list data

### `get_search_results(search_term, subsite='www.myprotein.com', limit=100, offset=0, currency='GBP', shippingDestination='GB', sort='RELEVANCE')`

Searches for products using Horizon's search API.

**Examples:**

```python
# Basic search
response = get_search_results("vitamin c", "www.lookfantastic.com", limit=30)

# With pagination and custom currency
response = get_search_results(
    "protein powder",
    "www.myprotein.com",
    limit=25,
    offset=25,
    currency='EUR',
    shippingDestination='DE',
    sort='PRICE_HIGH_TO_LOW'
)
```

**Returns:** JSON string with search results

### `query_horizon(query, subsite='www.myprotein.com')`

Executes custom GraphQL queries against the Horizon API.

**Example:**

```python
custom_query = """
query {
  product(sku: 11234482, strict: false) {
    sku
    title
    variants {
      sku
      title
      inStock
    }
  }
}
"""
result = query_horizon(custom_query, "www.myprotein.com")
```

**Returns:** JSON string response

### `get_rocinante_subsites()`

Fetches list of available THG subsites from Rocinante API.

**Example:**

```python
subsites = get_rocinante_subsites()
```

**Returns:** JSON array of subsite data

## Working with Agent State

Access state variables and return results to your agent:

```python
from horizon_fetcher import get_product_ids, get_product_json
import json

# Get user input from agent state
user_query = state.get("search_query", "protein")
target_site = state.get("site", "www.myprotein.com")
max_results = state.get("max_products", 10)

# Fetch products
logger.info(f"Searching for '{user_query}' on {target_site}")
product_ids = get_product_ids(user_query, limit=max_results)

# Get details for first product
if product_ids:
    product_json = get_product_json(product_ids[0], target_site)
    product = json.loads(product_json)

    logger.info(f"Found product: {product['data']['product']['title']}")
    set_output(product)
else:
    logger.warning("No products found")
    set_output({"error": "No products found"})
```

## Supported Subsites

Common THG e-commerce sites:
- `www.myprotein.com`
- `www.myprotein.jp`
- `www.myvitamins.com`
- `www.lookfantastic.com`
- `www.cultbeauty.co.uk`
- `www.dermstore.com`


Use `get_rocinante_subsites()` to fetch the complete list.

## Data Formats

### Product ID Extraction

Product IDs are extracted from Horizon URLs using the pattern:
```
/p/category/product-name/{product_id}/
```

### GraphQL Query Defaults

All product retrieval functions (`get_product_ids`, `get_product_list`, `get_search_results`) support these configurable parameters:
- **Currency:** GBP (default) - accepts any currency code (e.g., 'USD', 'EUR', 'JPY')
- **Shipping Destination:** GB (default) - accepts any country code (e.g., 'US', 'DE', 'JP')
- **Sort:** RELEVANCE (default) - other options include 'PRICE_LOW_TO_HIGH', 'PRICE_HIGH_TO_LOW'
- **Limit:** 100 (default) - maximum number of results to return
- **Offset:** 0 (default) - number of results to skip (useful for pagination)

These can be customized per function call without modifying the source code.

## Error Handling

The utilities print errors to stderr and return empty lists when:
- No products found
- Invalid URL format
- JSON parsing errors
- API errors

Add error handling in your code blocks:

```python
from horizon_fetcher import get_product_ids

try:
    product_ids = get_product_ids(state.get("query"))

    if not product_ids:
        set_output({"status": "error", "message": "No products found"})
    else:
        set_output({"status": "success", "product_ids": product_ids})

except Exception as e:
    logger.error(f"Error fetching products: {e}")
    set_output({"status": "error", "message": str(e)})
```

## Advanced Usage

### Custom GraphQL Queries

Build custom queries for specific data needs:

```python
from horizon_client import query_horizon

# Fetch only specific fields
query = """
query {
  search(
    options: {
      currency: GBP
      shippingDestination: GB
      limit: 5
    }
    query: "creatine"
  ) {
    total
    products {
      url
      title
      sku
      price {
        rrp
        price
      }
    }
  }
}
"""

result = query_horizon(query, "www.myprotein.com")
```

### Processing Multiple Subsites

Fetch products across multiple sites:

```python
from horizon_fetcher import get_product_ids
import json

sites = ["www.myprotein.com", "www.lookfantastic.com"]
search_term = "vitamin d"
all_results = {}

for site in sites:
    product_ids = get_product_ids(search_term, limit=10)
    all_results[site] = product_ids
    logger.info(f"{site}: {len(product_ids)} products")

set_output(all_results)
```

## Limitations

- **No Package Installation:** Writer agents only support pre-installed packages (pandas, requests, numpy). This codebase only requires `requests` and standard library modules.
- **Rate Limiting:** Horizon API implements rate limiting. Handle potential CAPTCHA or throttling errors.

## Documentation

- **Horizon API:** https://horizondocs.thgaltitude.com/guides/guide/
- **Writer Python Code:** https://dev.writer.com/agent-builder/python-code
- **Writer Agent Builder:** https://dev.writer.com/agent-builder/quickstart

## Example: Complete Agent Code Block

```python
from horizon_fetcher import get_product_ids, get_product_json
import json

# Get user's search query from agent state
query = state.get("user_query", "protein powder")
num_results = state.get("num_results", 5)

logger.info(f"Searching Horizon API for: {query}")

# Search for products
product_ids = get_product_ids(query, limit=num_results)

if not product_ids:
    set_output({
        "status": "no_results",
        "message": f"No products found for '{query}'"
    })
else:
    # Fetch details for all products
    products = []
    for pid in product_ids[:num_results]:
        try:
            product_json = get_product_json(pid)
            product_data = json.loads(product_json)

            # Extract key fields
            product = product_data['data']['product']
            products.append({
                "sku": product['sku'],
                "title": product['title'],
                "variants": len(product.get('variants', []))
            })
        except Exception as e:
            logger.error(f"Error fetching product {pid}: {e}")

    logger.info(f"Successfully fetched {len(products)} products")
    set_output({
        "status": "success",
        "count": len(products),
        "products": products
    })
```

## Command-Line Interface

The `horizon_fetcher.py` script can also be used from the command line for testing and data exploration.

### Available Commands

```bash
# Get help
python3 horizon_fetcher.py --help

# Get product IDs from search term or URL
python3 horizon_fetcher.py ids "whey protein" --limit 20
python3 horizon_fetcher.py ids "https://www.myprotein.com/c/nutrition/protein/" --limit 50 --offset 50

# Get product details by SKU
python3 horizon_fetcher.py product 10530943 --subsite www.myprotein.com --pretty

# Search for products
python3 horizon_fetcher.py search "creatine" --currency USD --shipping US --limit 10 --pretty

# Get products from category page
python3 horizon_fetcher.py list "nutrition/protein/whey-protein/" --sort PRICE_LOW_TO_HIGH --limit 25
```

### CLI Options

All commands support the following options where applicable:

- `--limit LIMIT` - Maximum number of results (default: 100)
- `--offset OFFSET` - Number of results to skip for pagination (default: 0)
- `--currency CURRENCY` - Currency code like USD, EUR, GBP (default: GBP)
- `--shipping DESTINATION` - Shipping country code like US, GB, DE (default: GB)
- `--sort SORT` - Sort order: RELEVANCE, PRICE_LOW_TO_HIGH, PRICE_HIGH_TO_LOW (default: RELEVANCE)
- `--subsite SUBSITE` - Subsite domain (default: www.myprotein.com)
- `--pretty` - Pretty-print JSON output

### CLI Examples

**Search with pagination:**
```bash
# Get first 10 results
python3 horizon_fetcher.py ids "protein" --limit 10

# Get next 10 results
python3 horizon_fetcher.py ids "protein" --limit 10 --offset 10
```

**Multi-currency product lookup:**
```bash
# Get product in USD for US market
python3 horizon_fetcher.py search "whey protein" --currency USD --shipping US --limit 5 --pretty
```

**Category browsing:**
```bash
# Get products from a category URL
python3 horizon_fetcher.py ids "https://www.myprotein.com/c/nutrition/vitamins/" --limit 20
```

## Support

For issues with:
- **Horizon API:** See https://horizondocs.thgaltitude.com
- **Writer Agents:** See https://dev.writer.com
- **This Code:** Review source code in `horizon_client.py` and `horizon_fetcher.py`
