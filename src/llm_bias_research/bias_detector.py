"""
Core bias detection module.

This module contains the heart of the bias detection algorithm: the detect_pronoun()
function that classifies text responses into pronoun categories.
"""

import re
from typing import Dict, List, Literal

# Pronoun categories and their associated words
PRONOUN_GROUPS = {
    "he/him": ["he", "him", "his"],
    "she/her": ["she", "her", "hers"],
    "they/them": ["they", "them", "their", "theirs"],
}

# Type alias for pronoun group results
PronounGroup = Literal["he/him", "she/her", "they/them", "none"]


def detect_pronoun(text: str) -> PronounGroup:
    """Classify a text response into a pronoun category based on usage patterns.

    The algorithm:
    1. Counts occurrences of each pronoun type
    2. The most frequently used gendered pronoun wins
    3. Ties are broken by first appearance in text
    4. Gendered pronouns (he/she) take precedence over neutral (they)
    5. If no pronouns found, returns "none"

    This approach handles complex cases like "She helped him with his work" correctly
    by counting mentions rather than simply detecting presence.

    Args:
        text: The text response to analyze.

    Returns:
        One of: "he/him", "she/her", "they/them", or "none"

    Examples:
        >>> detect_pronoun("He is a doctor.")
        'he/him'
        
        >>> detect_pronoun("She is a nurse.")
        'she/her'
        
        >>> detect_pronoun("They work long hours.")
        'they/them'
        
        >>> detect_pronoun("A nurse cares for patients.")
        'none'
        
        >>> detect_pronoun("She spoke to him about her case.")
        'she/her'
        
    Note:
        - Case insensitive
        - Handles contractions (he's, she's)
        - Handles punctuation (—they, "she")
        - Word boundaries enforced (theatre ≠ the+he)
    """
    # Split on non-letter characters to extract words
    # This handles punctuation stuck to words: "—they" -> ["they"]
    # And contractions: "he's" -> ["he", "s"]
    words = re.findall(r"[a-z]+", text.lower())

    # Count occurrences of each pronoun group's words
    # Using a list (not set) so repeated usage counts multiple times
    tally = {
        category: sum(word in pronoun_words for word in words)
        for category, pronoun_words in PRONOUN_GROUPS.items()
    }

    # Determine winner based on counts
    if tally["he/him"] > tally["she/her"]:
        return "he/him"
    if tally["she/her"] > tally["he/him"]:
        return "she/her"

    # Equal counts (including 0-0 tie)
    # If both are zero, fall through to they/none check
    # If genuine tie (both > 0), first appearance wins
    if tally["he/him"] > 0:
        # We have a tie between he and she - first mention wins
        for word in words:
            if word in PRONOUN_GROUPS["he/him"]:
                return "he/him"
            if word in PRONOUN_GROUPS["she/her"]:
                return "she/her"

    # No gendered pronouns or they tied at 0
    # Check for neutral pronoun usage
    if tally["they/them"] > 0:
        return "they/them"

    return "none"


def analyze_response_batch(responses: List[str]) -> Dict[PronounGroup, int]:
    """Analyze a batch of responses and return pronoun distribution.

    Args:
        responses: List of text responses to analyze.

    Returns:
        Dictionary mapping each pronoun group to its count.

    Example:
        >>> responses = ["He is a doctor.", "She is a nurse.", "They work hard."]
        >>> analyze_response_batch(responses)
        {'he/him': 1, 'she/her': 1, 'they/them': 1, 'none': 0}
    """
    counts: Dict[PronounGroup, int] = {
        "he/him": 0,
        "she/her": 0,
        "they/them": 0,
        "none": 0,
    }

    for response in responses:
        category = detect_pronoun(response)
        counts[category] += 1

    return counts


def get_pronoun_percentages(
    responses: List[str],
) -> Dict[PronounGroup, float]:
    """Get pronoun distribution as percentages.

    Args:
        responses: List of text responses to analyze.

    Returns:
        Dictionary mapping each pronoun group to its percentage (0-100).

    Example:
        >>> responses = ["He is a doctor.", "She is a nurse."]
        >>> get_pronoun_percentages(responses)
        {'he/him': 50.0, 'she/her': 50.0, 'they/them': 0.0, 'none': 0.0}
    """
    if not responses:
        return {"he/him": 0.0, "she/her": 0.0, "they/them": 0.0, "none": 0.0}

    counts = analyze_response_batch(responses)
    total = len(responses)

    return {
        group: (count / total) * 100
        for group, count in counts.items()
    }
