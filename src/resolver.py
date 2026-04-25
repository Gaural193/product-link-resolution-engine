import os
import time
from serpapi import GoogleSearch

RETAILER_DOMAINS = {
    "Ralphs": "ralphs.com",
    "Vons": "vons.com",
    "Smart & Final": "smartandfinal.com",
    "Aldi": "aldi.us",
    "Whole Foods": "wholefoodsmarket.com",
    "Sprouts": "sprouts.com",
    "Walmart": "walmart.com",
    "CVS": "cvs.com"
}

def resolve_product_link(retailer: str, product_name: str, size: str) -> tuple[str, str]:
    """
    Uses SerpApi (Google Search) to find the product on the retailer's website.
    Returns a tuple of (resolved_title, resolved_url) or (None, None) if not found.
    """
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("SERPAPI_KEY is not set correctly in .env!")
        return None, None

    domain = RETAILER_DOMAINS.get(retailer)
    
    if not domain:
        query = f"{retailer} {product_name} {size if size else ''}".strip()
    else:
        query = f"site:{domain} {product_name} {size if size else ''}".strip()

    params = {
      "engine": "google",
      "q": query,
      "api_key": api_key,
      "num": 5
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            
            organic_results = results.get("organic_results", [])
            
            if organic_results:
                # Filter results to ensure they actually point to the correct domain if specified
                valid_results = []
                if domain:
                    valid_results = [r for r in organic_results if domain in r.get("link", "").lower()]
                else:
                    valid_results = organic_results
                    
                if valid_results:
                    top_result = valid_results[0]
                    return top_result.get("title"), top_result.get("link")
            
            # If no exception occurred but no valid results were found, break out of retry loop
            break
                
        except Exception as e:
            print(f"SerpApi error for {query} (Attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1.0) # Wait before retrying on failure
        finally:
            time.sleep(0.5) # Always rate limit requests

    return None, None
