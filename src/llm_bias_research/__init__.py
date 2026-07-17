"""
LLM Bias Research - A toolkit for measuring gender bias in Large Language Models.

This package provides tools for:
- Querying local LLMs via Ollama with customizable prompts
- Analyzing pronoun usage to detect gender bias
- Storing results in CSV and SQLite databases
- Visualizing patterns through interactive dashboards
- Statistical analysis and machine learning predictions

Example:
    >>> from llm_bias_research import BiasCollector, BiasAnalyzer
    >>> collector = BiasCollector(model="phi3")
    >>> results = collector.query(keywords=["Nurse", "Doctor"])
    >>> analyzer = BiasAnalyzer(results)
    >>> analyzer.get_pronoun_distribution()
"""

__version__ = "0.2.2"
__author__ = "URSCA Research Team"
__license__ = "MIT"

from llm_bias_research.bias_detector import detect_pronoun, PRONOUN_GROUPS
from llm_bias_research.collector import BiasCollector
from llm_bias_research.database import BiasDatabase
from llm_bias_research.analyzer import BiasAnalyzer

__all__ = [
    "detect_pronoun",
    "PRONOUN_GROUPS",
    "BiasCollector",
    "BiasDatabase",
    "BiasAnalyzer",
    "__version__",
]
