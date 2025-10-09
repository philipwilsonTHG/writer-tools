import json
import re
from urllib.parse import urlparse
from horizon_client import query_horizon

def get_product_json(product_id: int, subsite: str = 'www.myprotein.com'):
    query = get_product_query(product_id)
    return query_horizon(query, subsite)


def get_product_list(product_list_path: str, subsite: str = 'www.myprotein.com'):
    """
    Fetch product list data from Horizon API.

    Args:
        product_list_path: The path to the product list (without /c prefix)
        subsite: The subsite domain

    Returns:
        JSON response from Horizon API
    """
    query = get_product_list_query(product_list_path)
    return query_horizon(query, subsite)


def get_search_results(search_term: str, subsite: str = 'www.myprotein.com', limit: int = 100):
    """
    Search for products using Horizon search API.

    Args:
        search_term: The search query string
        subsite: The subsite domain
        limit: Maximum number of results to return

    Returns:
        JSON response from Horizon API
    """
    query = get_search_query(search_term, limit)
    return query_horizon(query, subsite)


def get_product_list_query(product_list_path: str):
    """
    Build GraphQL query to fetch product URLs from a product list page.
    Simplified query that only requests the url field.
    """
    return f"""query ProductList {{
  page(path: "{product_list_path}") {{
    widgets {{
      ... on ProductListWidget {{
        productList(input: {{
          currency: GBP
          shippingDestination: GB
          limit: 100
          offset: 0
          sort: RELEVANCE
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


def get_search_query(search_term: str, limit: int = 100):
    """
    Build GraphQL query to search for products.
    Returns only product URLs.
    """
    return f"""query Search {{
  search(
    options: {{
      currency: GBP
      shippingDestination: GB
      limit: {limit}
      offset: 0
      sort: RELEVANCE
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

def fetch_product_ids(url, limit=100):
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

        response = get_product_list(product_list_path, subsite)
        product_ids = extract_product_ids_from_list(response)

    else:
        # Search mode
        search_term = input_arg
        subsite = 'www.myprotein.com'  # Default to myprotein

        response = get_search_results(search_term, subsite, limit)
        product_ids = extract_product_ids_from_search(response)

    if not product_ids:
        print("No product IDs found", file=sys.stderr)
        sys.exit(1)

    return product_ids

if __name__ == "__main__":
    main()
