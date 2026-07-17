"""
Data collection module for querying Ollama LLMs.

This module handles:
- Querying local LLMs via Ollama API
- Batch processing with multiple keywords and prompts
- Rate limiting and error handling
- Simultaneous CSV and SQLite output
"""

import csv
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import List, Optional, Tuple

import ollama
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from tqdm import tqdm

from llm_bias_research.database import BiasDatabase
from llm_bias_research.utils import load_prompts, sanitize_filename, ensure_directory, get_next_filename

console = Console()


class BiasCollector:
    """Collects LLM responses for bias analysis.

    This class manages the process of querying an Ollama model with various
    prompts and keywords, then saving the results to both CSV and SQLite formats.

    Attributes:
        model: Name of the Ollama model to query.
        rate_limit_delay: Seconds to wait between queries (default: 0.05).
        max_retries: Maximum number of retry attempts for failed queries.
    """

    def __init__(
        self,
        model: str,
        rate_limit_delay: float = 0.05,
        max_retries: int = 3,
        max_tokens: int = 500,
    ) -> None:
        """Initialize the collector.

        Args:
            model: Name of the Ollama model (e.g., "phi3", "llama3.2").
            rate_limit_delay: Seconds to wait between queries.
            max_retries: Maximum retry attempts for failed queries.
            max_tokens: Maximum tokens in response (prevents hallucination overflow).

        Raises:
            ValueError: If model name is invalid.
            RuntimeError: If Ollama is not accessible.
        """
        self.model = model
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.max_tokens = max_tokens

        # Validate model availability
        self._validate_model()

    def _validate_model(self) -> None:
        """Check if the model is available in Ollama.

        Raises:
            RuntimeError: If model is not accessible.
        """
        try:
            # Quick test query
            ollama.chat(model=self.model, messages=[{"role": "user", "content": "test"}])
            console.print(f"✓ Model '{self.model}' is accessible", style="green")
        except Exception as e:
            raise RuntimeError(
                f"Cannot access model '{self.model}'. "
                f"Make sure Ollama is running and the model is installed. "
                f"Error: {e}"
            ) from e

    def query_model(self, prompt: str) -> str:
        """Query the model with a single prompt.

        Extracts only the first two sentences from the response to keep
        outputs focused and comparable. Also limits response by max_tokens.

        Args:
            prompt: The prompt text to send to the model.

        Returns:
            The model's response (first two sentences only, token-limited).

        Raises:
            RuntimeError: If query fails after all retries.
        """
        for attempt in range(self.max_retries):
            try:
                response = ollama.chat(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    options={"num_predict": self.max_tokens},
                )

                # Extract content from response
                text = (
                    response.get("message", {}).get("content")
                    or response.get("content", "")
                ).strip()

                # Keep only first two sentences
                sentences = re.split(r"(?<=[.!?])\s+", text)
                return " ".join(sentences[:2]).strip()

            except Exception as e:
                if attempt < self.max_retries - 1:
                    console.print(
                        f"⚠ Query failed (attempt {attempt + 1}/{self.max_retries}), retrying...",
                        style="yellow",
                    )
                    time.sleep(1)  # Brief pause before retry
                else:
                    raise RuntimeError(
                        f"Model query failed after {self.max_retries} attempts: {e}"
                    ) from e

        # Should never reach here, but for type checking
        raise RuntimeError("Query failed")

    def collect_data(
        self,
        keywords: List[str],
        prompts: List[str],
        output_path: str,
        runs_per_prompt: int = 5,
        create_database: bool = True,
    ) -> Tuple[str, Optional[str]]:
        """Collect responses for multiple keywords and prompts.

        Args:
            keywords: List of keywords to test (e.g., ["Nurse", "Doctor"]).
            prompts: List of prompt templates with {keyword} placeholder.
            output_path: Path for output file (without extension).
            runs_per_prompt: Number of times to repeat each prompt.
            create_database: Whether to create SQLite database (default: True).

        Returns:
            Tuple of (csv_path, database_path). database_path is None if
            create_database is False.

        Raises:
            ValueError: If keywords or prompts are empty.
            OSError: If unable to write output files.
        """
        if not keywords:
            raise ValueError("Keywords list cannot be empty")
        if not prompts:
            raise ValueError("Prompts list cannot be empty")

        # Ensure output directory exists and get next available filenames
        output_path = Path(output_path)
        ensure_directory(output_path.parent)
        
        # Get serialized filenames to avoid overwrites
        csv_path = get_next_filename(output_path, ".csv")
        db_path = get_next_filename(output_path, ".db") if create_database else None

        # Calculate total queries
        total_queries = len(keywords) * len(prompts) * runs_per_prompt

        console.print(f"\n📊 Starting data collection", style="bold blue")
        console.print(f"   Model: {self.model}")
        console.print(f"   Keywords: {len(keywords)}")
        console.print(f"   Prompts: {len(prompts)}")
        console.print(f"   Runs per prompt: {runs_per_prompt}")
        console.print(f"   Total queries: {total_queries}")
        console.print(f"   Max tokens: {self.max_tokens}")
        console.print(f"   Output: {csv_path}")
        if db_path:
            console.print(f"   Database: {db_path}\n")

        # Collect all responses
        rows = []
        row_index = 1

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            # Overall progress bar
            overall_task = progress.add_task(
                "[bold cyan]📊 Overall Progress",
                total=total_queries
            )
            
            # Prompt-level progress bar (will be updated for each prompt)
            prompt_task = progress.add_task(
                "[green]   ⏳ Current prompt",
                total=1,
                visible=False
            )

            for keyword_idx, keyword in enumerate(keywords, 1):
                # Substitute keyword into each prompt
                filled_prompts = [p.replace("{keyword}", keyword) for p in prompts]

                for prompt_idx, prompt in enumerate(filled_prompts, 1):
                    # Update prompt task for current prompt
                    progress.update(
                        prompt_task,
                        description=f"[green]   ⏳ {keyword} (prompt {prompt_idx}/{len(filled_prompts)})",
                        completed=0,
                        total=runs_per_prompt,
                        visible=True
                    )
                    
                    for run_idx in range(runs_per_prompt):
                        try:
                            # Show what we're querying
                            short_prompt = prompt[:60] + "..." if len(prompt) > 60 else prompt
                            progress.console.print(
                                f"      🤖 Run {run_idx + 1}/{runs_per_prompt}: {short_prompt}",
                                style="dim"
                            )
                            
                            response = self.query_model(prompt)
                            rows.append(
                                {
                                    "rowIndex": row_index,
                                    "keyword": keyword,
                                    "prompt": prompt,
                                    "response": response,
                                }
                            )
                            row_index += 1

                            # Rate limiting
                            time.sleep(self.rate_limit_delay)

                        except RuntimeError as e:
                            console.print(f"✗ Error: {e}", style="red")
                            # Continue with other queries even if one fails

                        # Update both progress bars
                        progress.update(prompt_task, advance=1)
                        progress.update(overall_task, advance=1)

        # Write CSV file
        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                fieldnames = ["rowIndex", "keyword", "prompt", "response"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            console.print(f"\n✓ CSV saved: {csv_path}", style="green")
        except OSError as e:
            raise OSError(f"Failed to write CSV file '{csv_path}': {e}") from e

        # Create database if requested
        if create_database and db_path:
            try:
                db = BiasDatabase(str(db_path))
                db.create_schema()
                db.insert_model_data(self.model, rows)
                console.print(f"✓ Database saved: {db_path}", style="green")
            except Exception as e:
                console.print(f"⚠ Database creation failed: {e}", style="yellow")
                db_path = None

        console.print(f"\n✓ Data collection complete: {len(rows)} responses\n", style="bold green")

        return str(csv_path), str(db_path) if db_path else None
