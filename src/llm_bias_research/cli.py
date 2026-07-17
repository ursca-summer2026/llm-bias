"""
Command-line interface for LLM Bias Research toolkit.

Provides commands for:
- Querying models (query)
- Launching dashboard (dashboard)
- Exporting reports (export)
- Database statistics (stats)
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from llm_bias_research import __version__
from llm_bias_research.collector import BiasCollector
from llm_bias_research.database import BiasDatabase
from llm_bias_research.utils import load_prompts, parse_keywords, ensure_directory

console = Console()


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """LLM Bias Research - A toolkit for measuring gender bias in LLMs.

    This toolkit helps you systematically test and analyze gender bias
    in Large Language Models through automated querying and statistical analysis.
    """
    pass


@main.command()
@click.option(
    "--model",
    "-m",
    required=True,
    help="Ollama model name (e.g., phi3, llama3.2)",
)
@click.option(
    "--keywords",
    "-k",
    required=True,
    help="Comma-separated keywords to test (e.g., 'Nurse,Doctor,Engineer')",
)
@click.option(
    "--prompt-file",
    "-p",
    type=click.Path(exists=True),
    required=True,
    help="Path to file containing prompt templates (one per line)",
)
@click.option(
    "--output",
    "-o",
    default="0_out/output",
    help="Output path (without extension, will create .csv and .db) - default: 0_out/output",
)
@click.option(
    "--runs",
    "-r",
    default=1,
    type=int,
    help="Number of times to run each prompt (for statistical power)",
)
@click.option(
    "--csv-only",
    is_flag=True,
    help="Output CSV only, skip database creation",
)
@click.option(
    "--rate-limit",
    default=0.05,
    type=float,
    help="Seconds to wait between queries (default: 0.05)",
)
@click.option(
    "--max-tokens",
    default=500,
    type=int,
    help="Maximum tokens in model response (prevents hallucination overflow, default: 500)",
)
def query(
    model: str,
    keywords: str,
    prompt_file: str,
    output: str,
    runs: int,
    csv_only: bool,
    rate_limit: float,
    max_tokens: int,
) -> None:
    """Query an Ollama model and collect responses for bias analysis.

    This command systematically queries the specified model with various
    prompts and keywords, then saves results to both CSV and SQLite formats
    (unless --csv-only is specified).

    Example:

        llm-bias query \\
            --model phi3 \\
            --keywords "Nurse,Doctor,Engineer" \\
            --prompt-file prompts/default_prompts.txt \\
            --runs 5 \\
            --output results/phi3_test
    """
    try:
        # Parse keywords
        keyword_list = parse_keywords(keywords)
        console.print(f"Keywords to test: {', '.join(keyword_list)}", style="cyan")

        # Load prompts
        prompts = load_prompts(prompt_file)
        console.print(f"Loaded {len(prompts)} prompts from {prompt_file}", style="cyan")

        # Initialize collector
        collector = BiasCollector(
            model=model,
            rate_limit_delay=rate_limit,
            max_tokens=max_tokens,
        )

        # Collect data
        csv_path, db_path = collector.collect_data(
            keywords=keyword_list,
            prompts=prompts,
            output_path=output,
            runs_per_prompt=runs,
            create_database=not csv_only,
        )

        console.print("\n✓ Collection complete!", style="bold green")
        console.print(f"  CSV: {csv_path}")
        if db_path:
            console.print(f"  Database: {db_path}")

    except Exception as e:
        console.print(f"✗ Error: {e}", style="bold red")
        sys.exit(1)


@main.command()
@click.option(
    "--database",
    "-d",
    type=click.Path(path_type=Path),
    help="Path to specific database file to analyze",
)
@click.option(
    "--port",
    "-p",
    default=8501,
    type=int,
    help="Port for Streamlit server (default: 8501)",
)
@click.option(
    "--compare",
    is_flag=True,
    help="Launch multi-database comparison dashboard",
)
def dashboard(
    database: Optional[Path],
    port: int,
    compare: bool,
) -> None:
    """Launch the interactive Streamlit dashboard.

    Opens a web browser with the analysis dashboard for exploring
    bias patterns, viewing statistics, and generating visualizations.

    Example:

        llm-bias dashboard --database 0_out/phi3_test.db
    """
    try:
        import subprocess

        # Prepare streamlit command
        dashboard_dir = Path(__file__).parent.parent.parent / "dashboard"

        if not dashboard_dir.exists():
            console.print(
                f"✗ Dashboard directory not found: {dashboard_dir}",
                style="bold red",
            )
            sys.exit(1)

        cmd = ["streamlit", "run", str(dashboard_dir / "app.py"), "--server.port", str(port)]

        # Pass database path if specified (convert to absolute path and validate)
        if database:
            # Resolve to absolute path from current working directory
            if not database.is_absolute():
                database_abs = (Path.cwd() / database).resolve()
            else:
                database_abs = database
            
            # Validate path exists
            if not database_abs.exists():
                console.print(
                    f"✗ Database file not found: {database_abs}",
                    style="bold red",
                )
                sys.exit(1)
            
            cmd.extend(["--", "--database", str(database_abs)])

        console.print(f"🚀 Launching dashboard on port {port}...", style="bold blue")
        subprocess.run(cmd)

    except KeyboardInterrupt:
        console.print("\n✓ Dashboard stopped", style="green")
    except Exception as e:
        console.print(f"✗ Error launching dashboard: {e}", style="bold red")
        sys.exit(1)


@main.command()
@click.argument("database", type=click.Path(exists=True))
def stats(database: str) -> None:
    """Display statistics for a database.

    Shows record counts, available models/keywords, and response distributions.

    Example:

        llm-bias stats results/phi3_test.db
    """
    try:
        db = BiasDatabase(database)
        statistics = db.get_statistics()

        console.print(f"\n📊 Database Statistics: {database}\n", style="bold blue")

        # Create summary table
        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Total Models", str(statistics["total_models"]))
        table.add_row("Total Keywords", str(statistics["total_keywords"]))
        table.add_row("Total Responses", str(statistics["total_responses"]))

        console.print(table)

        # Models
        console.print("\n📦 Models:", style="bold")
        for model in statistics["models"]:
            count = statistics["responses_per_model"].get(model, 0)
            console.print(f"  • {model}: {count} responses")

        # Keywords
        console.print("\n🔑 Keywords:", style="bold")
        for keyword in statistics["keywords"]:
            count = statistics["responses_per_keyword"].get(keyword, 0)
            console.print(f"  • {keyword}: {count} responses")

        console.print()

    except Exception as e:
        console.print(f"✗ Error: {e}", style="bold red")
        sys.exit(1)


@main.command()
@click.argument("database", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    required=True,
    help="Output file path (e.g., report.pdf)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["pdf", "html", "png"]),
    default="pdf",
    help="Output format (default: pdf)",
)
def export(database: str, output: str, format: str) -> None:
    """Export analysis report from database.

    Generates a comprehensive report with statistics, charts, and findings.

    Example:

        llm-bias export results/phi3_test.db --output report.pdf
    """
    try:
        console.print(
            f"📄 Export functionality coming soon!",
            style="yellow",
        )
        console.print(
            f"Will generate {format.upper()} report from {database} to {output}",
            style="dim",
        )

        # TODO: Implement export functionality
        # This would use matplotlib/plotly to generate static reports

    except Exception as e:
        console.print(f"✗ Error: {e}", style="bold red")
        sys.exit(1)


if __name__ == "__main__":
    main()
