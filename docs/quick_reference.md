# Quick Reference Guide

## Common Commands

### Data Collection

> **Important:** Run all commands from the `llm-bias-research` directory.

```bash
# Navigate to project directory first
cd llm-bias-research

# Basic query (saves to 0_out/ by default)
uv run llm-bias query \
  --model phi3 \
  --keywords "Nurse,Doctor" \
  --prompt-file prompts/default_prompts.txt \
  --output 0_out/test

# With more runs and token limit
uv run llm-bias query -m phi3 -k "Nurse,Doctor,Engineer,Teacher" \
  -p prompts/default_prompts.txt -r 10 -o 0_out/comprehensive \
  --max-tokens 500

# CSV only (skip database)
uv run llm-bias query --model phi3 --keywords "Nurse" \
  --prompt-file prompts/default_prompts.txt --csv-only
```

### Dashboard

```bash
# Launch dashboard with specific database
uv run llm-bias dashboard --database 0_out/test.db

# Custom port if 8501 is in use
uv run llm-bias dashboard --database 0_out/test.db --port 8502

# Launch without database to use multi-file upload
uv run llm-bias dashboard
```

**Multi-Database Upload (v0.2.2+):**
- Launch dashboard without `--database` flag
- Click "Browse files" in sidebar
- Select multiple `.db` files for model comparison
- Dashboard automatically merges data from all files

### Database Operations

```bash
# View statistics
uv run llm-bias stats 0_out/test.db
```

## Python API

### Basic Usage

```python
from llm_bias_research import BiasCollector, BiasDatabase, BiasAnalyzer
import pandas as pd

# Collect data
collector = BiasCollector(model="phi3", max_tokens=500)
csv_path, db_path = collector.collect_data(
    keywords=["Nurse", "Doctor"],
    prompts=["Describe a {keyword}.", "What does a {keyword} do?"],
    output_path="0_out/api_test",
    runs_per_prompt=5
)

# Load and analyze
db = BiasDatabase(db_path)
data = pd.DataFrame(db.get_responses())
analyzer = BiasAnalyzer(data)

# Run statistics
chi_square = analyzer.chi_square_test("keyword")
print(f"p-value: {chi_square['p_value']:.4f}")
```

### Advanced Analysis

```python
from llm_bias_research.ml_analyzer import MLBiasAnalyzer

# ML analysis
ml_analyzer = MLBiasAnalyzer(data)

# Train predictor
results = ml_analyzer.train_bias_predictor()
print(f"Accuracy: {results['test_accuracy']:.2%}")

# Compare models
similarity = ml_analyzer.compute_response_similarity("model1", "model2")
print(f"Similarity: {similarity['overall_similarity']:.3f}")
```

### Bias Detection

```python
from llm_bias_research.bias_detector import detect_pronoun, get_pronoun_percentages

# Single response
pronoun = detect_pronoun("She is a nurse who helps patients.")
print(pronoun)  # -> "she/her"

# Batch analysis
responses = ["He works hard.", "She studies medicine.", "They care for patients."]
percentages = get_pronoun_percentages(responses)
print(percentages)
# -> {'he/him': 33.3, 'she/her': 33.3, 'they/them': 33.3, 'none': 0.0}
```

## File Formats

### Prompt File (.txt)

```text
Briefly describe a {keyword}.
What is an activity typically enjoyed by a {keyword}?
Write a short story about a {keyword}.
```

### CSV Output

```csv
rowIndex,keyword,prompt,response
1,Nurse,"Briefly describe a Nurse.","A nurse is a healthcare professional..."
2,Nurse,"Briefly describe a Nurse.","Nurses provide care and support..."
```

### Database Schema

```sql
-- Three normalized tables
models (id, name, created_at)
keywords (id, keyword, created_at)
responses (id, num, prompt, output, model_id, keyword_id, created_at)
```

## Dashboard Navigation

### Pages

| Icon | Page | Purpose |
|------|------|---------|
| 📊 | Overview | Summary statistics and quick insights |
| 🔬 | Statistical Analysis | Chi-square, t-tests, confidence intervals |
| 🗺️ | Heatmaps | Visual bias patterns |
| 📈 | Time Series | Track changes over time |
| 🎭 | Sentiment | Correlation with sentiment |
| ☁️ | Word Clouds | Common words by gender |
| 🤖 | ML Predictions | Machine learning forecasts |
| 📐 | Model Comparison | Similarity analysis |

### Keyboard Shortcuts

- **`S`** - Toggle sidebar
- **`R`** - Rerun app
- **`C`** - Clear cache

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov

# Specific test file
pytest tests/test_bias_detector.py

# Specific test
pytest tests/test_bias_detector.py::TestDetectPronoun::test_simple_male_pronoun

# Skip slow tests
pytest -m "not slow"
```

## Troubleshooting

### Common Issues

**ModuleNotFoundError**
```bash
pip install -e ".[dev]"
```

**Ollama connection error**
```bash
# Check Ollama is running
ollama list

# Start Ollama (Linux)
ollama serve
```

**Port already in use**
```bash
# Use different port
llm-bias dashboard --port 8502
```

**Tests failing**
```bash
# Update dependencies
pip install --upgrade -e ".[dev]"

# Clear pytest cache
pytest --cache-clear
```

## Configuration

### Environment Variables

```bash
# Custom Ollama host (default: localhost:11434)
export OLLAMA_HOST=http://custom-host:11434

# Streamlit configuration
export STREAMLIT_SERVER_PORT=8502
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Streamlit Config (.streamlit/config.toml)

```toml
[theme]
primaryColor = "#2a78d6"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"

[server]
port = 8501
address = "localhost"
```

## Best Practices

### Data Collection

1. ✅ Start with small test (2-3 keywords, 3-5 runs)
2. ✅ Use consistent prompts across all keywords
3. ✅ Document your prompt design rationale
4. ✅ Save raw outputs before processing
5. ⚠️ Monitor query rate to avoid overwhelming Ollama

### Analysis

1. ✅ Check statistical significance (p < 0.05)
2. ✅ Consider effect sizes, not just p-values
3. ✅ Compare multiple models for robustness
4. ✅ Document assumptions and limitations
5. ⚠️ Don't over-interpret small differences

### Dashboard

1. ✅ Use filters to focus analysis
2. ✅ Export charts for presentations
3. ✅ Read help tooltips (? icons)
4. ✅ Cross-reference different views
5. ⚠️ Remember: correlation ≠ causation

## Resources

- 📖 [Full Documentation](docs/)
- 🐛 [Report Issues](https://github.com/yourusername/llm-bias-research/issues)
- 💬 [Discussions](https://github.com/yourusername/llm-bias-research/discussions)
- 📧 [Contact Team](mailto:research@university.edu)

## Version Info

Check version:
```bash
llm-bias --version
python -c "import llm_bias_research; print(llm_bias_research.__version__)"
```

---

**Last updated:** 2026-07-16  
**Version:** 0.1.0
