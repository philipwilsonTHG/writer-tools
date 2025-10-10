# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Python utilities for interacting with the Horizon GraphQL API to fetch product data from e-commerce subsites (e.g., myprotein.com). These tools are designed to support Python code blocks in Writer AI Studio agents.

The Horizon API is THG's enterprise e-commerce platform GraphQL API. It supports both web and mobile clients, with features like rate limiting, feature switching, and graceful degradation. See: https://horizondocs.thgaltitude.com/guides/guide/

## Architecture

The codebase consists of two main modules:

- **horizon_client.py**: Low-level HTTP client for making GraphQL queries to Horizon API
  - `query_horizon()`: Executes GraphQL queries against `horizon-api.{subsite}/graphql`
  - `get_rocinante_subsites()`: Fetches subsite data from internal Rocinante API

- **horizon_fetcher.py**: High-level utilities for product data retrieval
  - Provides functions to fetch products by ID, product list path, or search term
  - GraphQL query builders for different query types (product, product list, search)
  - Extraction utilities to parse product IDs from API responses (regex-based URL parsing)
  - `get_product_ids()`: Main entry point that auto-detects URL vs search term input

## Key Patterns

- All API functions accept a `subsite` parameter (defaults to `www.myprotein.com`)
- Product URLs follow pattern: `/p/category/product-name/{product_id}/`
- GraphQL queries hardcode GBP currency and GB shipping destination
- Product list queries default to 100 items with RELEVANCE sorting
- Error handling prints to stderr and returns empty lists/exits

## Horizon API Integration

- **Endpoint Pattern**: `https://horizon-api.{subsite}/graphql`
- **Authentication**: Currently using Web API mode (no explicit auth headers in this codebase)
- **Site Determination**: Via subsite domain in URL (e.g., `www.myprotein.com`)
- **Query Types**:
  - `product`: Fetch single product by SKU with full content fields and variants
  - `page`: Fetch product lists from category/collection pages via ProductListWidget
  - `search`: Search products by term with configurable limit

## Writer AI Studio Agent Integration

These utilities are designed to be used within Writer AI Studio agents via Python code blocks. They provide specialized functionality for querying the Horizon e-commerce API to retrieve product information.

### Setup in Writer Agent Builder

1. **Upload Files**: In the Agent Builder code editor, upload both `horizon_client.py` and `horizon_fetcher.py`
2. **Import in Code Blocks**: Reference these modules in Python code blocks within your agent blueprint
3. **Dependencies**: The `requests` library is pre-installed in Writer's Python environment

Note: Writer agents cannot install additional Python packages beyond the pre-installed set (pandas, requests, numpy, etc.). This codebase only uses `requests` and standard library modules.

### Usage Pattern

```python
from horizon_fetcher import get_product_ids, get_product_json
from horizon_client import query_horizon, get_rocinante_subsites

# Fetch product IDs from a category URL
product_ids = get_product_ids("https://www.myprotein.com/c/nutrition/protein/whey-protein/")

# Or search for products by keyword
product_ids = get_product_ids("whey protein", limit=50)

# Fetch detailed product data by SKU
product_data = get_product_json(product_ids[0], "www.myprotein.com")

# Get available subsites
subsites = get_rocinante_subsites()

# Execute custom GraphQL queries
custom_query = "query { __typename }"
result = query_horizon(custom_query, "www.myprotein.com")

# Return results to agent blueprint
set_output(product_data)
```

### Accessing Agent State and Variables

Writer Python code blocks have access to:
- `state["variable_name"]` - Agent state variables
- `vault["SECRET_NAME"]` - Secrets from Writer Vault
- `logger.info()` - Logging for debugging
- `set_output(value)` - Return values from code blocks

Example with state:
```python
from horizon_fetcher import get_product_ids

# Get search term from agent state
search_term = state.get("user_query", "protein powder")
subsite = state.get("target_site", "www.myprotein.com")

# Fetch products
product_ids = get_product_ids(search_term, limit=50)

# Log for debugging
logger.info(f"Found {len(product_ids)} products for '{search_term}'")

# Return to agent
set_output(product_ids)
```

### Common Use Cases

- **Product Discovery**: Search or browse product categories to find relevant items
- **Data Extraction**: Retrieve detailed product information including variants, images, and content
- **Multi-site Operations**: Query across different THG e-commerce subsites
- **Custom Queries**: Execute arbitrary GraphQL queries against Horizon API

See: https://dev.writer.com/agent-builder/python-code

## Dependencies

- `requests`: HTTP client for API calls
- Standard library: `json`, `re`, `urllib.parse`

## Running

Execute scripts directly with Python 3:
```bash
python3 horizon_fetcher.py
python3 horizon_client.py
```

## Testing

Run individual Python files to test functionality:
```bash
python3 -c "from horizon_client import query_horizon; print(query_horizon('query { __typename }', 'www.myprotein.com'))"
```
