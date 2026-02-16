import re

def is_prompt_injection(text: str) -> bool:
    """
    Detects potential prompt injection attempts.
    """
    if not text:
        return False
        
    text_lower = text.lower()
    
    # Heuristic patterns
    patterns = [
        r"ignore previous instructions",
        r"ignore all instructions",
        r"system prompt",
        r"you are now",
        r"reveal your",
        r"your instructions",
        r"your rules",
        r"admin mode",
        r"developer mode",
        r"program mode",
        r"bot token",
        r"api key",
        r"secret key",
        r"override system",
    ]
    
    for pattern in patterns:
        if re.search(pattern, text_lower):
            return True
            
    return False

def sanitize_user_input(text: str) -> str:
    """
    Sanitize user input (basic).
    """
    if text is None:
        return ""
    return str(text).strip()
