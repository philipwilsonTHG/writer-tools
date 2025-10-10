import json
import re
import sys
import argparse
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

def get_product_ids(url, limit=100, offset=0, currency='GBP', shippingDestination='GB', sort='RELEVANCE', subsite='www.myprotein.com'):
    """
    Fetch product IDs from a URL or search term.

    Args:
        url: Either a product list URL or a search term
        limit: Maximum number of results to return
        offset: Number of results to skip (for pagination)
        currency: Currency code (e.g., 'GBP', 'USD', 'EUR')
        shippingDestination: Country code for shipping (e.g., 'GB', 'US')
        sort: Sort order (e.g., 'RELEVANCE', 'PRICE_LOW_TO_HIGH', 'PRICE_HIGH_TO_LOW')
        subsite: Subsite domain for search queries (default: 'www.myprotein.com', ignored for URL queries)

    Returns:
        List of product IDs (integers)
    """
    input_arg = url
    # Determine if input is a URL or search term
    if is_url(input_arg):
        # URL mode - fetch product list
        parsed = urlparse(input_arg)
        url_subsite = parsed.netloc
        product_list_path = parsed.path

        # Remove '/c' prefix if present
        if product_list_path.startswith('/c/'):
            product_list_path = product_list_path[2:]

        # Remove trailing slash if present
        if product_list_path.endswith('/'):
            product_list_path = product_list_path[:-1]

        if not url_subsite or not product_list_path:
            print("Error: Invalid URL. Must include both domain and path.", file=sys.stderr)
            sys.exit(1)

        response = get_product_list(product_list_path, url_subsite, limit, offset, currency, shippingDestination, sort)
        product_ids = extract_product_ids_from_list(response)

    else:
        # Search mode - use the subsite parameter
        search_term = input_arg

        response = get_search_results(search_term, subsite, limit, offset, currency, shippingDestination, sort)
        product_ids = extract_product_ids_from_search(response)

    if not product_ids:
        print("No product IDs found", file=sys.stderr)
        sys.exit(1)

    return product_ids


def main():
    """Command-line interface for Horizon API utilities."""
    parser = argparse.ArgumentParser(
        description='Horizon API command-line utility for fetching product data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Get product IDs from a search term
  %(prog)s ids "whey protein" --limit 20

  # Get product IDs from a category URL with pagination
  %(prog)s ids "https://www.myprotein.com/c/nutrition/protein/" --limit 50 --offset 50

  # Search with custom currency and shipping
  %(prog)s search "creatine" --currency USD --shipping US --limit 10

  # Get product details by ID
  %(prog)s product 10530943 --subsite www.myprotein.com

  # Get product list with sorting
  %(prog)s list "nutrition/protein/whey-protein/" --sort PRICE_LOW_TO_HIGH --limit 25
        '''
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Common arguments for pagination and filtering
    def add_common_args(subparser):
        subparser.add_argument('--subsite', default='www.myprotein.com', help='Subsite domain (default: www.myprotein.com)')
        subparser.add_argument('--limit', type=int, default=100, help='Maximum number of results (default: 100)')
        subparser.add_argument('--offset', type=int, default=0, help='Number of results to skip (default: 0)')
        subparser.add_argument('--currency', default='GBP', help='Currency code (default: GBP)')
        subparser.add_argument('--shipping', dest='shippingDestination', default='GB', help='Shipping destination country code (default: GB)')
        subparser.add_argument('--sort', default='RELEVANCE', help='Sort order (default: RELEVANCE)')

    # get_product_ids command
    parser_ids = subparsers.add_parser('ids', help='Get product IDs from URL or search term')
    parser_ids.add_argument('query', help='Product list URL or search term')
    add_common_args(parser_ids)

    # get_product_json command
    parser_product = subparsers.add_parser('product', help='Get product details by SKU')
    parser_product.add_argument('sku', type=int, help='Product SKU')
    parser_product.add_argument('--subsite', default='www.myprotein.com', help='Subsite domain (default: www.myprotein.com)')
    parser_product.add_argument('--pretty', action='store_true', help='Pretty-print JSON output')

    # get_search_results command
    parser_search = subparsers.add_parser('search', help='Search for products')
    parser_search.add_argument('term', help='Search term')
    parser_search.add_argument('--pretty', action='store_true', help='Pretty-print JSON output')
    add_common_args(parser_search)

    # get_product_list command
    parser_list = subparsers.add_parser('list', help='Get products from category page')
    parser_list.add_argument('path', help='Product list path (without /c prefix)')
    parser_list.add_argument('--pretty', action='store_true', help='Pretty-print JSON output')
    add_common_args(parser_list)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'ids':
            # Get product IDs
            product_ids = get_product_ids(
                args.query,
                limit=args.limit,
                offset=args.offset,
                currency=args.currency,
                shippingDestination=args.shippingDestination,
                sort=args.sort,
                subsite=args.subsite
            )
            print(json.dumps(product_ids, indent=2))

        elif args.command == 'product':
            # Get product details
            result = get_product_json(args.sku, args.subsite)
            if args.pretty:
                print(json.dumps(json.loads(result), indent=2))
            else:
                print(result)

        elif args.command == 'search':
            # Search for products
            result = get_search_results(
                args.term,
                args.subsite,
                limit=args.limit,
                offset=args.offset,
                currency=args.currency,
                shippingDestination=args.shippingDestination,
                sort=args.sort
            )
            if args.pretty:
                print(json.dumps(json.loads(result), indent=2))
            else:
                print(result)

        elif args.command == 'list':
            # Get product list
            result = get_product_list(
                args.path,
                args.subsite,
                limit=args.limit,
                offset=args.offset,
                currency=args.currency,
                shippingDestination=args.shippingDestination,
                sort=args.sort
            )
            if args.pretty:
                print(json.dumps(json.loads(result), indent=2))
            else:
                print(result)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
