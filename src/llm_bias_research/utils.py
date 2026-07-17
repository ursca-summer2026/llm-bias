"""
Utility functions for the LLM bias research toolkit.
"""

import re
from pathlib import Path
from typing import List, Optional, Union


def load_prompts(filepath: str) -> List[str]:
    """Load prompts from a text file.

    Each non-empty line in the file becomes one prompt template.
    Lines can include {keyword} placeholder for substitution.

    Args:
        filepath: Path to the prompts file.

    Returns:
        List of prompt strings.

    Raises:
        FileNotFoundError: If file doesn't exist.
        ValueError: If file is empty or contains no valid prompts.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Prompts file not found: {filepath}")

    with open(path, "r", encoding="utf-8") as f:
        prompts = [line.strip() for line in f if line.strip()]

    if not prompts:
        raise ValueError(f"No valid prompts found in file: {filepath}")

    return prompts


def sanitize_filename(name: str) -> str:
    """Convert a string to a safe filename.

    Removes or replaces characters that are problematic in filenames.

    Args:
        name: The string to sanitize.

    Returns:
        Sanitized string safe for use as filename.

    Example:
        >>> sanitize_filename("llama3.2/test")
        'llama3_2_test'
    """
    # Replace problematic characters with underscores
    safe = re.sub(r'[<>:"/\\|?*]', "_", name)
    # Remove leading/trailing dots and spaces
    safe = safe.strip(". ")
    # Collapse multiple underscores
    safe = re.sub(r"_+", "_", safe)
    return safe


def parse_keywords(keyword_str: str) -> List[str]:
    """Parse comma-separated keywords string.

    Args:
        keyword_str: Comma-separated keywords.

    Returns:
        List of cleaned keyword strings.

    Example:
        >>> parse_keywords("Nurse, Doctor,  Engineer  ")
        ['Nurse', 'Doctor', 'Engineer']
    """
    return [k.strip() for k in keyword_str.split(",") if k.strip()]


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a decimal value as percentage string.

    Args:
        value: Value between 0 and 1.
        decimals: Number of decimal places.

    Returns:
        Formatted percentage string.

    Example:
        >>> format_percentage(0.456, 1)
        '45.6%'
    """
    return f"{value * 100:.{decimals}f}%"


def prompt_type(prompt: str, keyword: str) -> str:
    """Extract prompt type by removing the keyword.

    Collapses prompts that differ only by keyword into one type.
    This allows comparing the same question across different professions.

    Args:
        prompt: The full prompt text.
        keyword: The keyword to replace.

    Returns:
        Prompt type with keyword replaced by "___".

    Example:
        >>> prompt_type("Briefly describe a Nurse.", "Nurse")
        'Briefly describe a ___'
    """
    # Replace keyword with placeholder (case-insensitive)
    template = re.sub(re.escape(keyword), "___", prompt, flags=re.IGNORECASE)
    # Strip trailing punctuation/spaces for consistency
    return template.strip().rstrip(" ,.;:!?")


def validate_model_name(model: str) -> bool:
    """Check if a model name looks valid.

    Args:
        model: Model name to validate.

    Returns:
        True if name appears valid.
    """
    # Basic validation: non-empty, reasonable characters
    if not model or not isinstance(model, str):
        return False
    # Model names typically contain letters, numbers, dots, hyphens
    return bool(re.match(r"^[a-zA-Z0-9._-]+$", model))


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path.

    Returns:
        Path object for the directory.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_next_filename(base_path: Union[str, Path], extension: str = "") -> Path:
    """Get next available filename with serialized suffix to avoid overwrites.
    
    If file.csv exists, returns file_01.csv
    If file_01.csv exists, returns file_02.csv
    And so on...
    
    Args:
        base_path: Base path without extension (e.g., "results/output")
        extension: File extension including dot (e.g., ".csv")
    
    Returns:
        Path object for the next available filename
    
    Example:
        >>> get_next_filename("data/results", ".csv")
        Path("data/results.csv")  # if doesn't exist
        >>> get_next_filename("data/results", ".csv")  
        Path("data/results_01.csv")  # if results.csv exists
    """
    base_path = Path(base_path)
    base_dir = base_path.parent
    base_name = base_path.name
    
    # Try without suffix first
    candidate = base_dir / f"{base_name}{extension}"
    if not candidate.exists():
        return candidate
    
    # Try with incrementing suffixes
    counter = 1
    while True:
        candidate = base_dir / f"{base_name}_{counter:02d}{extension}"
        if not candidate.exists():
            return candidate
        counter += 1
        if counter > 999:  # Safety limit
            raise RuntimeError("Too many existing files (999+) - please clean up output directory")