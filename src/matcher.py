from rapidfuzz import fuzz, utils

def calculate_confidence(original_product: str, original_size: str, search_result_title: str) -> float:
    """
    Calculates a confidence score between 0 and 100 for how well the search result matches
    the original product and size.
    """
    if not original_product:
        return 0.0
        
    # Normalize strings (lowercase, remove special chars)
    original_str = f"{original_product} {original_size if original_size else ''}".strip()
    
    # We use token_set_ratio because retailers often add extra words 
    # (like brand names or "Frozen") that lower the score artificially.
    # token_set_ratio handles subset matches much better.
    score = fuzz.token_set_ratio(
        utils.default_process(original_str), 
        utils.default_process(search_result_title)
    )
    
    return round(score, 2)

def validate_url(url: str) -> tuple[bool, str]:
    """
    Validates if a URL is a direct product page rather than a search page.
    """
    if not url:
        return False, "No URL provided"
        
    if "search?" in url or "/search" in url or "q=" in url:
        return False, "URL is a search page, not a product page"
        
    # Checking common product page patterns
    if "/product/" in url or "/products/" in url or "/ip/" in url or "/p/" in url or "product-details" in url:
        return True, "Direct product URL confirmed"
        
    # If it doesn't clearly look like a search page, we'll tentatively allow it,
    # but for strictness we could reject it. Let's tentatively allow.
    return True, "URL format acceptable"

def evaluate_match(score: float, url: str = None):
    """
    Evaluates the score and returns the status and notes.
    """
    if url:
        is_valid, url_note = validate_url(url)
        if not is_valid:
            return "unresolved", f"Rejected: {url_note}"

    if score >= 85:
        return "resolved", "High confidence match"
    elif score >= 70:
        return "resolved", f"Acceptable near match (Score: {score})"
    else:
        return "unresolved", f"Low confidence match (Score: {score})"
