# Getting Started with LLM Bias Research

This guide will help you set up and start using the LLM Bias Research toolkit.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.9 or higher** installed
- **Ollama** installed and running locally ([Download here](https://ollama.ai/))
- At least one LLM model downloaded in Ollama
- **Git** (for cloning the repository)
- **(Optional) UV** for faster package management ([Install UV](https://docs.astral.sh/uv/))

### Installing Ollama and Models

```bash
# Download and install Ollama from https://ollama.ai/

# Pull some models to test with
ollama pull phi3
ollama pull llama3.2
ollama pull qwen2.5:latest
```

## Installation

### Method 1: Using UV (Recommended)

UV is 10-100x faster than pip and handles virtual environments automatically.

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/yourusername/llm-bias-research.git
cd llm-bias-research

# Install everything (creates .venv automatically)
uv sync --all-extras

# Verify installation
uv run llm-bias --version

# Run tests
uv run pytest
```

**Using UV commands:**
```bash
# Run any CLI command with uv run
uv run llm-bias query --help
uv run llm-bias dashboard

# Or activate the virtual environment
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate    # On Windows
```

### Method 2: Using pip (Traditional)

```bash
# Clone the repository
git clone https://github.com/yourusername/llm-bias-research.git
cd llm-bias-research

# Create a virtual environment
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install with all dependencies
pip install -e ".[dev]"

# Or just the core package
pip install -e .

# Verify installation
llm-bias --version

# Run tests
pytest
```

## Your First Data Collection

### Step 1: Prepare Your Prompts

Create a file `my_prompts.txt` with prompt templates:

```text
Briefly describe a {keyword}.
What skills are important for a {keyword}?
Write a short story about a {keyword}.
```

The `{keyword}` placeholder will be replaced with your test keywords.

### Step 2: Run a Query

> **Important:** Make sure you're in the `llm-bias-research` directory before running commands.

```bash
# Navigate to project directory
cd llm-bias-research

# Run your first query
uv run llm-bias query \
  --model phi3 \
  --keywords "Nurse,Doctor,Engineer,Teacher" \
  --prompt-file my_prompts.txt \
  --runs 5 \
  --output 0_out/phi3_test \
  --max-tokens 500
```

**What this does:**
- Queries the `phi3` model
- Tests 4 professions (keywords)
- Uses your 3 prompts
- Runs each prompt 5 times per keyword
- Limits responses to 500 tokens (prevents hallucination overflow)
- Creates `0_out/phi3_test.csv` and `0_out/phi3_test.db`
- If files exist, creates `0_out/phi3_test_01.csv` to avoid overwrites
- Shows nested progress bars for overall progress and current prompt

**Total queries:** 4 keywords × 3 prompts × 5 runs = 60 queries

### Step 3: Analyze Results

```bash
# View database statistics
uv run llm-bias stats 0_out/phi3_test.db

# Launch interactive dashboard
uv run llm-bias dashboard --database 0_out/phi3_test.db
```

The dashboard will open in your browser at `http://localhost:8501`.

> **Tip:** If port 8501 is already in use, specify a different port:
> ```bash
> uv run llm-bias dashboard --database 0_out/phi3_test.db --port 8502
> ```

## Understanding the Output

### CSV Format

```csv
rowIndex,keyword,prompt,response
1,Nurse,"Briefly describe a Nurse.","A nurse is a healthcare professional..."
2,Nurse,"Briefly describe a Nurse.","Nurses provide care for patients..."
...
```

### SQLite Database

Three normalized tables:
- **models**: Stores model names
- **keywords**: Stores profession keywords
- **responses**: Links responses to models and keywords

## Dashboard Overview

### Main Pages

1. **📊 Overview** - Quick statistics and distributions
2. **🔬 Statistical Analysis** - Chi-square tests, t-tests, confidence intervals
3. **🗺️ Heatmaps** - Visual bias patterns by profession and model
4. **📈 Time Series** - Track bias changes over time
5. **🎭 Sentiment Analysis** - Correlation between sentiment and bias
6. **☁️ Word Clouds** - Common words by gender group
7. **🤖 ML Predictions** - Machine learning bias forecasting
8. **📐 Model Comparison** - Cosine similarity and detailed comparisons

### Key Features

- **Filters**: Select specific models or keywords
- **Interactive charts**: Hover for details, click legend to toggle
- **Help system**: Click ❓ in sidebar for explanations
- **Export**: Right-click charts to save as images

## Common Workflows

### Workflow 1: Compare Multiple Models

**New in v0.2.2:** Upload multiple database files for easy model comparison!

```bash
# Collect data from multiple models (separate databases)
uv run llm-bias query --model phi3 --keywords "Nurse,Doctor,Engineer" \
  --prompt-file prompts/default_prompts.txt --output 0_out/phi3_study

uv run llm-bias query --model llama3.2 --keywords "Nurse,Doctor,Engineer" \
  --prompt-file prompts/default_prompts.txt --output 0_out/llama_study

uv run llm-bias query --model mistral --keywords "Nurse,Doctor,Engineer" \
  --prompt-file prompts/default_prompts.txt --output 0_out/mistral_study

# Launch dashboard
uv run llm-bias dashboard
```

**In the dashboard:**
1. Click "Browse files" under "Upload database file(s)" in the sidebar
2. Select all three database files: `phi3_study.db`, `llama_study.db`, `mistral_study.db`
3. Dashboard automatically merges the data for comparison
4. Navigate to the "📐 Model Comparison" page to analyze differences

**Why separate databases?**
- More memory-efficient than combining all models during collection
- Easier to manage and update individual model datasets
- Dashboard merges data on-the-fly for analysis

### Workflow 2: Test Many Professions

```bash
# Create a comprehensive keyword list
uv run llm-bias query \
  --model phi3 \
  --keywords "Nurse,Doctor,Engineer,Teacher,Lawyer,Chef,Pilot,Accountant" \
  --prompt-file prompts/default_prompts.txt \
  --runs 10 \
  --output 0_out/comprehensive_test
```

### Workflow 3: Custom Analysis

```python
from llm_bias_research import BiasDatabase, BiasAnalyzer
import pandas as pd

# Load data
db = BiasDatabase("0_out/phi3_test.db")
data = pd.DataFrame(db.get_responses())

# Analyze
analyzer = BiasAnalyzer(data)
chi_square = analyzer.chi_square_test("keyword")
print(f"Chi-square p-value: {chi_square['p_value']}")
```

## Tips and Best Practices

### Data Collection

1. **Start small**: Test with 2-3 keywords and 3-5 runs first
2. **Use rate limiting**: Default 0.05s delay prevents overwhelming Ollama
3. **Monitor progress**: Watch the progress bar during collection
4. **Check results**: Always review CSV output before analyzing

### Analysis

1. **Statistical significance**: Look for p-values < 0.05
2. **Effect sizes**: Consider both statistical and practical significance
3. **Sample size**: More runs = more reliable results
4. **Multiple models**: Compare across different models for robustness

### Dashboard

1. **Start with Overview**: Get familiar with your data
2. **Check Statistics**: Verify patterns are significant
3. **Use Filters**: Focus on specific aspects
4. **Compare carefully**: Ensure fair comparisons (same prompts, etc.)

## Troubleshooting

### "Database file not found" or Path Errors

**Problem:** Command fails with "Path does not exist" or "Database file not found"

**Solution:** Ensure you're running commands from the `llm-bias-research` directory:

```bash
# Check your current directory
pwd

# If not in llm-bias-research, navigate there
cd path/to/llm-bias-research

# Then run your command
uv run llm-bias dashboard --database 0_out/my_study.db
```

The CLI resolves relative paths from your current working directory. All commands must be run from the project root (`llm-bias-research/`).

### "Model not found" Error

```bash
# List available models
ollama list

# Pull the model you need
ollama pull phi3
```

### "Connection refused" Error

```bash
# Make sure Ollama is running
# On macOS: Ollama runs automatically
# On Linux: Start with `ollama serve`
```

### Import Errors

```bash
# Reinstall in development mode
pip install -e ".[dev]"
```

### Dashboard Not Loading

```bash
# Check if port is in use
lsof -i :8501

# Use a different port
uv run llm-bias dashboard --database 0_out/my_study.db --port 8502
```

## Next Steps

- Read the [Methodology Documentation](methodology.md) to understand the bias detection algorithm
- Check the [API Reference](api_reference.md) for programmatic usage
- See [CONTRIBUTING.md](../CONTRIBUTING.md) to contribute to the project

## Getting Help

- 📖 Read the documentation in `docs/`
- 💬 Open an issue on GitHub
- 📧 Contact the maintainers

Happy researching! 🔍
