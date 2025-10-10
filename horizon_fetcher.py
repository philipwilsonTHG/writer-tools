import json
import re
from urllib.parse import urlparse
from horizon_client import query_horizon

def get_product_json(product_id: int, subsite: str = 'www.myprotein.com'):
    query = get_product_query(product_id)
    return query_horizon(query, subsite)


def get_product_list(product_list_path: str, subsite: str = 'www.myprotein.com', limit: int = 100, offset: int = 0, currency: str = 'GBP', shippingDestination: str = 'GB', sort: str = 'RELEVANCE'):
    """
    Fetch product list data from Horizon API.

    Args:
        product_list_path: The path to the product list (without /c prefix)
        subsite: The subsite domain
        limit: Maximum number of results to return
        offset: Number of results to skip (for pagination)
        currency: Currency code (e.g., 'GBP', 'USD', 'EUR')
        shippingDestination: Country code for shipping (e.g., 'GB', 'US')
        sort: Sort order (e.g., 'RELEVANCE', 'PRICE_LOW_TO_HIGH', 'PRICE_HIGH_TO_LOW')

    Returns:
        JSON response from Horizon API
    """
    query = get_product_list_query(product_list_path, limit, offset, currency, shippingDestination, sort)
    return query_horizon(query, subsite)


def get_search_results(search_term: str, subsite: str = 'www.myprotein.com', limit: int = 100, offset: int = 0, currency: str = 'GBP', shippingDestination: str = 'GB', sort: str = 'RELEVANCE'):
    """
    Search for products using Horizon search API.

    Args:
        search_term: The search query string
        subsite: The subsite domain
        limit: Maximum number of results to return
        offset: Number of results to skip (for pagination)
        currency: Currency code (e.g., 'GBP', 'USD', 'EUR')
        shippingDestination: Country code for shipping (e.g., 'GB', 'US')
        sort: Sort order (e.g., 'RELEVANCE', 'PRICE_LOW_TO_HIGH', 'PRICE_HIGH_TO_LOW')

    Returns:
        JSON response from Horizon API
    """
    query = get_search_query(search_term, limit, offset, currency, shippingDestination, sort)
    return query_horizon(query, subsite)


def get_product_list_query(product_list_path: str, limit: int = 100, offset: int = 0, currency: str = 'GBP', shippingDestination: str = 'GB', sort: str = 'RELEVANCE'):
    """
    Build GraphQL query to fetch product URLs from a product list page.
    Simplified query that only requests the url field.

    Args:
        product_list_path: The path to the product list (without /c prefix)
        limit: Maximum number of results to return
        offset: Number of results to skip (for pagination)
        currency: Currency code (e.g., 'GBP', 'USD', 'EUR')
        shippingDestination: Country code for shipping (e.g., 'GB', 'US')
        sort: Sort order (e.g., 'RELEVANCE', 'PRICE_LOW_TO_HIGH', 'PRICE_HIGH_TO_LOW')
    """
    return f"""query ProductList {{
  page(path: "{product_list_path}") {{
    widgets {{
      ... on ProductListWidget {{
        productList(input: {{
          currency: {currency}
          shippingDestination: {shippingDestination}
          limit: {limit}
          offset: {offset}
          sort: {sort}
          facets: []
        }}) {{
          total
          products {{
            url
          }}
        }}
      }}
    }}
  }}
}}"""

def get_product_query(product_sku: int):
    return f"""query Product {{                                                                                            
  product(sku: {product_sku}, strict: false) {{                                                                            
    sku,                                                                                                                   
    title                                                                                                                  
    content {{                                                                                                             
      key                                                                                                                  
      value {{                                                                                                             
        ... on ProductContentStringValue {{                                                                                
          stringValue: value                                                                                               
        }}                                                                                                                 
        ... on ProductContentStringListValue {{                                                                            
          stringListValue: value                                                                                           
        }}                                                                                                                 
        ... on ProductContentIntValue {{                                                                                   
          intValue: value                                                                                                  
        }}                                                                                                                 
        ... on ProductContentIntListValue {{                                                                               
          intListValue: value                                                                                              
        }}                                                                                                                 
        ... on ProductContentRichContentValue {{                                                                           
          richContentValue: value {{                                                                                       
            content {{                                                                                                     
              type                                                                                                         
              content                                                                                                      
            }}                                                                                                             
          }}                                                                                                               
        }}                                                                                                                 
        ... on ProductContentRichContentListValue {{                                                                       
          richContentListValue: value {{                                                                                   
            content {{                                                                                                     
              type                                                                                                         
              content                                                                                                      
            }}                                                                                                             
          }}                                                                                                               
        }}                                                                                                                 
      }}                                                                                                                   
    }}                                                                                                                     
    variants{{                                                                                                             
      sku                                                                                                                  
      title                                                                                                                
      inStock                                                                                                              
      images(limit: 4){{                                                                                                   
        original                                                                                                           
        thumbnail                                                                                                          
      }}                                                                                                                   
                                                                                                                           
    }}                                                                                                                     
                                                                                                                           
}}                                                                                                                         
}}"""


def get_search_query(search_term: str, limit: int = 100, offset: int = 0, currency: str = 'GBP', shippingDestination: str = 'GB', sort: str = 'RELEVANCE'):
    """
    Build GraphQL query to search for products.
    Returns only product URLs.

    Args:
        search_term: The search query string
        limit: Maximum number of results to return
        offset: Number of results to skip (for pagination)
        currency: Currency code (e.g., 'GBP', 'USD', 'EUR')
        shippingDestination: Country code for shipping (e.g., 'GB', 'US')
        sort: Sort order (e.g., 'RELEVANCE', 'PRICE_LOW_TO_HIGH', 'PRICE_HIGH_TO_LOW')
    """
    return f"""query Search {{
  search(
    options: {{
      currency: {currency}
      shippingDestination: {shippingDestination}
      limit: {limit}
      offset: {offset}
      sort: {sort}
      facets: []
    }}
    query: "{search_term}"
  ) {{
    total
    products {{
      url
    }}
  }}
}}"""




def extract_product_ids_from_list(response_json: str):
    """
    Extract product IDs from a product list API response.

    Args:
        response_json: JSON string response from Horizon API

    Returns:
        List of product IDs (integers)
    """
    try:
        data = json.loads(response_json)
        widgets = data['data']['page']['widgets']

        # Find the widget with productList (may not be at index 0)
        products = None
        for widget in widgets:
            if 'productList' in widget:
                products = widget['productList']['products']
                break

        if products is None:
            print("Error: No productList widget found", file=sys.stderr)
            return []

        product_ids = []
        for product in products:
            url = product['url']
            # Extract product ID from URL pattern: /p/category/product-name/12345678/
            match = re.search(r'/(\d+)/', url)
            if match:
                product_ids.append(int(match.group(1)))

        return product_ids
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Error parsing product list response: {e}", file=sys.stderr)
        return []


def extract_product_ids_from_search(response_json: str):
    """
    Extract product IDs from a search API response.

    Args:
        response_json: JSON string response from Horizon API

    Returns:
        List of product IDs (integers)
    """
    try:
        data = json.loads(response_json)
        products = data['data']['search']['products']

        product_ids = []
        for product in products:
            url = product['url']
            # Extract product ID from URL pattern: /p/category/product-name/12345678/
            match = re.search(r'/(\d+)/', url)
            if match:
                product_ids.append(int(match.group(1)))

        return product_ids
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Error parsing search response: {e}", file=sys.stderr)
        return []


def is_url(input_str: str) -> bool:
    """Check if the input string is a URL."""
    return input_str.startswith('http://') or input_str.startswith('https://')

def get_product_ids(url, limit=100, offset=0, currency='GBP', shippingDestination='GB', sort='RELEVANCE'):
    """
    Fetch product IDs from a URL or search term.

    Args:
        url: Either a product list URL or a search term
        limit: Maximum number of results to return
        offset: Number of results to skip (for pagination)
        currency: Currency code (e.g., 'GBP', 'USD', 'EUR')
        shippingDestination: Country code for shipping (e.g., 'GB', 'US')
        sort: Sort order (e.g., 'RELEVANCE', 'PRICE_LOW_TO_HIGH', 'PRICE_HIGH_TO_LOW')

    Returns:
        List of product IDs (integers)
    """
    input_arg = url
    # Determine if input is a URL or search term
    if is_url(input_arg):
        # URL mode - fetch product list
        parsed = urlparse(input_arg)
        subsite = parsed.netloc
        product_list_path = parsed.path

        # Remove '/c' prefix if present
        if product_list_path.startswith('/c/'):
            product_list_path = product_list_path[2:]

        # Remove trailing slash if present
        if product_list_path.endswith('/'):
            product_list_path = product_list_path[:-1]

        if not subsite or not product_list_path:
            print("Error: Invalid URL. Must include both domain and path.", file=sys.stderr)
            sys.exit(1)

        response = get_product_list(product_list_path, subsite, limit, offset, currency, shippingDestination, sort)
        product_ids = extract_product_ids_from_list(response)

    else:
        # Search mode
        search_term = input_arg
        subsite = 'www.myprotein.com'  # Default to myprotein

        response = get_search_results(search_term, subsite, limit, offset, currency, shippingDestination, sort)
        product_ids = extract_product_ids_from_search(response)

    if not product_ids:
        print("No product IDs found", file=sys.stderr)
        sys.exit(1)

    return product_ids

if __name__ == "__main__":
    main()
