# LLM Bias Research Dashboard

**Comprehensive Streamlit Application for Gender Bias Analysis**

This directory contains the interactive dashboard for analyzing gender bias in LLM responses.

## Features

- **Multi-page application** with dedicated analysis modules
- **Interactive visualizations** using Plotly and Altair
- **Statistical analysis** with significance testing
- **Model comparison** tools
- **Time-series tracking**
- **ML-based predictions**
- **Export capabilities**

## Running the Dashboard

```bash
# From project root
llm-bias dashboard

# Or directly with streamlit
cd dashboard
streamlit run app.py

# With specific database (single model)
streamlit run app.py -- --database ../0_out/phi3_test.db
```

## Loading Data

### Option 1: Multiple Database Upload (Recommended for Model Comparison)

Upload multiple database files through the sidebar file uploader:
- Each database file typically contains data for **one model**
- Upload 2+ files to enable multi-model comparison
- Dashboard automatically merges data from all uploaded files
- Memory-efficient approach for comparing different models

**Example workflow:**
```bash
# Create separate databases for each model
llm-bias query --model phi3 --keywords "Nurse,Doctor,Engineer" \
  --prompt-file prompts/default_prompts.txt --output results/phi3_study

llm-bias query --model llama3.2 --keywords "Nurse,Doctor,Engineer" \
  --prompt-file prompts/default_prompts.txt --output results/llama_study

llm-bias query --model mistral --keywords "Nurse,Doctor,Engineer" \
  --prompt-file prompts/default_prompts.txt --output results/mistral_study
```

Then in the dashboard:
1. Click "Browse files" in the sidebar
2. Select `phi3_study.db`, `llama_study.db`, and `mistral_study.db`
3. Dashboard loads and merges all three for comparison

### Option 2: Single Database Upload

Upload one database file containing data from one or multiple models.

### Option 3: Command Line Argument

```bash
streamlit run app.py -- --database path/to/database.db
```

## Page Structure

1. **Overview** - Summary statistics and quick insights
2. **Statistical Analysis** - Chi-square tests, t-tests, effect sizes
3. **Heatmaps** - Profession × pronoun and model × pronoun grids
4. **Time Series** - Track bias changes over time/versions
5. **Sentiment Analysis** - Correlation between sentiment and bias
6. **Word Clouds** - Visualize common words by gender group
7. **ML Predictions** - Machine learning bias forecasting
8. **Model Comparison** - Cosine similarity and detailed comparisons
