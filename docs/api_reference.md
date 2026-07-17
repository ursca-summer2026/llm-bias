# API Reference

Complete API documentation for the LLM Bias Research toolkit.

## Module Overview

- [bias_detector](#bias_detector) - Core pronoun detection algorithm
- [collector](#collector) - Data collection from Ollama
- [database](#database) - SQLite database operations  
- [analyzer](#analyzer) - Statistical analysis
- [ml_analyzer](#ml_analyzer) - Machine learning analysis
- [utils](#utils) - Utility functions
- [cli](#cli) - Command-line interface

---

## bias_detector

Core module for detecting pronoun groups in text responses.

### Functions

#### `detect_pronoun(text: str) -> PronounGroup`

Detect the primary pronoun group used in a text response.

**Parameters:**
- `text` (str): The text to analyze

**Returns:**
- `PronounGroup`: One of "he/him", "she/her", "they/them", or "none"

**Algorithm:**
1. Count frequencies of all pronouns
2. If tie, first appearance wins
3. Gendered pronouns take precedence over neutral
4. Robust to punctuation and case

**Example:**
```python
from llm_bias_research import detect_pronoun

text = "She is a nurse. She helps patients."
pronoun = detect_pronoun(text)  # Returns "she/her"
```

---

#### `analyze_response_batch(responses: List[str]) -> List[PronounGroup]`

Analyze multiple responses in batch.

**Parameters:**
- `responses` (List[str]): List of text responses to analyze

**Returns:**
- `List[PronounGroup]`: List of detected pronoun groups

**Example:**
```python
responses = [
    "He works as a doctor.",
    "She is an engineer.",
    "They are a teacher."
]
results = analyze_response_batch(responses)
# Returns ["he/him", "she/her", "they/them"]
```

---

#### `get_pronoun_percentages(responses: List[str]) -> Dict[PronounGroup, float]`

Calculate percentage distribution of pronoun groups.

**Parameters:**
- `responses` (List[str]): List of text responses

**Returns:**
- `Dict[PronounGroup, float]`: Percentage for each pronoun group

**Example:**
```python
responses = ["He works." * 60 + "She works." * 40]
percentages = get_pronoun_percentages(responses)
# Returns {"he/him": 60.0, "she/her": 40.0, "they/them": 0.0, "none": 0.0}
```

---

### Constants

#### `PRONOUN_GROUPS`

Dictionary mapping pronoun groups to their pronoun lists:

```python
PRONOUN_GROUPS = {
    "he/him": ["he", "him", "his", "himself"],
    "she/her": ["she", "her", "hers", "herself"],
    "they/them": ["they", "them", "their", "theirs", "themselves"]
}
```

---

## collector

Module for collecting data from Ollama LLMs.

### Class: `BiasCollector`

Main class for collecting bias data.

#### `__init__(model: str, rate_limit_delay: float = 0.05, max_retries: int = 3)`

Initialize the bias collector.

**Parameters:**
- `model` (str): Ollama model name (e.g., "phi3", "llama3.2")
- `rate_limit_delay` (float, optional): Delay between queries in seconds. Default: 0.05
- `max_retries` (int, optional): Maximum retry attempts for failed queries. Default: 3

**Example:**
```python
from llm_bias_research import BiasCollector

collector = BiasCollector(
    model="phi3",
    rate_limit_delay=0.1,
    max_retries=5
)
```

---

#### `query_model(prompt: str) -> str`

Query the Ollama model with a prompt.

**Parameters:**
- `prompt` (str): The prompt to send to the model

**Returns:**
- `str`: First two sentences of model response

**Raises:**
- `Exception`: If all retry attempts fail

**Example:**
```python
response = collector.query_model("Describe a nurse.")
print(response)  # "A nurse is a healthcare professional. They provide patient care."
```

---

#### `collect_data(keywords: List[str], prompts: List[str], output_path: str, runs_per_prompt: int = 5, create_database: bool = True) -> Tuple[str, str]`

Collect bias data for multiple keywords and prompts.

**Parameters:**
- `keywords` (List[str]): List of professions/keywords to test
- `prompts` (List[str]): List of prompt templates with `{keyword}` placeholder
- `output_path` (str): Base path for output files (without extension)
- `runs_per_prompt` (int, optional): Number of times to run each prompt. Default: 5
- `create_database` (bool, optional): Whether to create SQLite database. Default: True

**Returns:**
- `Tuple[str, str]`: (csv_path, database_path)

**Example:**
```python
csv_path, db_path = collector.collect_data(
    keywords=["Nurse", "Doctor", "Engineer"],
    prompts=["Describe a {keyword}.", "What does a {keyword} do?"],
    output_path="0_out/my_test",
    runs_per_prompt=10
)

print(f"CSV saved to: {csv_path}")
print(f"Database saved to: {db_path}")
```

---

## database

Module for SQLite database operations.

### Class: `BiasDatabase`

Interface for bias response database.

#### `__init__(db_path: str)`

Initialize database connection.

**Parameters:**
- `db_path` (str): Path to SQLite database file

**Example:**
```python
from llm_bias_research import BiasDatabase

db = BiasDatabase("0_out/my_data.db")
```

---

#### `create_schema()`

Create database schema with three tables: models, keywords, responses.

**Schema:**
```sql
CREATE TABLE models (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE keywords (
    id INTEGER PRIMARY KEY,
    keyword TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE responses (
    id INTEGER PRIMARY KEY,
    num INTEGER NOT NULL,
    prompt TEXT NOT NULL,
    output TEXT NOT NULL,
    model_id INTEGER,
    keyword_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES models(id),
    FOREIGN KEY (keyword_id) REFERENCES keywords(id)
);
```

---

#### `insert_model_data(model_name: str, rows: List[Dict]) -> int`

Insert data for a specific model.

**Parameters:**
- `model_name` (str): Name of the model
- `rows` (List[Dict]): List of dictionaries with keys: num, keyword, prompt, output

**Returns:**
- `int`: Number of rows inserted

**Example:**
```python
rows = [
    {
        "num": 1,
        "keyword": "Nurse",
        "prompt": "Describe a Nurse.",
        "output": "A nurse is a healthcare professional."
    },
    {
        "num": 2,
        "keyword": "Doctor",
        "prompt": "Describe a Doctor.",
        "output": "A doctor diagnoses and treats patients."
    }
]

count = db.insert_model_data("phi3", rows)
print(f"Inserted {count} rows")
```

---

#### `get_responses(model: Optional[str] = None, keyword: Optional[str] = None) -> List[Dict]`

Retrieve responses with optional filtering.

**Parameters:**
- `model` (str, optional): Filter by model name
- `keyword` (str, optional): Filter by keyword

**Returns:**
- `List[Dict]`: List of response dictionaries

**Example:**
```python
# Get all responses
all_responses = db.get_responses()

# Get responses for specific model
phi3_responses = db.get_responses(model="phi3")

# Get responses for specific keyword
nurse_responses = db.get_responses(keyword="Nurse")

# Combined filter
specific_responses = db.get_responses(model="phi3", keyword="Nurse")
```

---

#### `get_statistics() -> Dict`

Get comprehensive database statistics.

**Returns:**
- `Dict`: Statistics including total_responses, models, keywords, by_model, by_keyword

**Example:**
```python
stats = db.get_statistics()

print(f"Total responses: {stats['total_responses']}")
print(f"Models: {stats['models']}")
print(f"Keywords: {stats['keywords']}")

for keyword, count in stats['by_keyword'].items():
    print(f"{keyword}: {count} responses")
```

---

## analyzer

Module for statistical analysis of bias data.

### Class: `BiasAnalyzer`

Statistical analysis interface.

#### `__init__(data: pd.DataFrame)`

Initialize analyzer with data.

**Parameters:**
- `data` (pd.DataFrame): DataFrame with columns: keyword, pronoun_group, and optional: model, prompt

**Example:**
```python
from llm_bias_research import BiasAnalyzer
import pandas as pd

# Load data
db = BiasDatabase("0_out/my_data.db")
data = pd.DataFrame(db.get_responses())

# Add pronoun detection
data["pronoun_group"] = data["output"].apply(detect_pronoun)

# Create analyzer
analyzer = BiasAnalyzer(data)
```

---

#### `chi_square_test(variable: str) -> Dict`

Perform chi-square test of independence.

**Parameters:**
- `variable` (str): Column name to test (e.g., "keyword", "model")

**Returns:**
- `Dict`: Contains chi2, p_value, dof, cramers_v, interpretation

**Example:**
```python
result = analyzer.chi_square_test("keyword")

print(f"Chi-square: {result['chi2']:.2f}")
print(f"P-value: {result['p_value']:.4f}")
print(f"Cramér's V: {result['cramers_v']:.3f}")
print(f"Interpretation: {result['interpretation']}")

if result['p_value'] < 0.05:
    print("Significant association detected!")
```

---

#### `t_test_pronouns(group1_filter: Dict, group2_filter: Dict, pronoun: str) -> Dict`

Perform independent samples t-test.

**Parameters:**
- `group1_filter` (Dict): Filter for first group (e.g., {"keyword": "Nurse"})
- `group2_filter` (Dict): Filter for second group (e.g., {"keyword": "Doctor"})
- `pronoun` (str): Pronoun group to test ("he/him", "she/her", etc.)

**Returns:**
- `Dict`: Contains t_statistic, p_value, cohens_d, interpretation, group1_mean, group2_mean

**Example:**
```python
result = analyzer.t_test_pronouns(
    group1_filter={"keyword": "Nurse"},
    group2_filter={"keyword": "Doctor"},
    pronoun="he/him"
)

print(f"Nurse he/him rate: {result['group1_mean']:.1%}")
print(f"Doctor he/him rate: {result['group2_mean']:.1%}")
print(f"Difference is {'significant' if result['p_value'] < 0.05 else 'not significant'}")
print(f"Effect size (Cohen's d): {result['cohens_d']:.2f}")
```

---

#### `confidence_interval(group_filter: Dict, pronoun: str, confidence: float = 0.95) -> Dict`

Calculate confidence interval for pronoun proportion.

**Parameters:**
- `group_filter` (Dict): Filter for group (e.g., {"keyword": "Nurse"})
- `pronoun` (str): Pronoun group
- `confidence` (float, optional): Confidence level (0.0-1.0). Default: 0.95

**Returns:**
- `Dict`: Contains lower, upper, mean, n

**Example:**
```python
ci = analyzer.confidence_interval(
    group_filter={"keyword": "Nurse"},
    pronoun="she/her",
    confidence=0.95
)

print(f"Mean: {ci['mean']:.1%}")
print(f"95% CI: [{ci['lower']:.1%}, {ci['upper']:.1%}]")
print(f"Sample size: {ci['n']}")
```

---

## ml_analyzer

Module for machine learning analysis.

### Class: `MLBiasAnalyzer`

Machine learning analysis interface.

#### `__init__(data: pd.DataFrame)`

Initialize ML analyzer.

**Parameters:**
- `data` (pd.DataFrame): DataFrame with columns: keyword, pronoun_group, output

**Example:**
```python
from llm_bias_research.ml_analyzer import MLBiasAnalyzer

ml_analyzer = MLBiasAnalyzer(data)
```

---

#### `train_bias_predictor(test_size: float = 0.2, cv_folds: int = 5) -> Dict`

Train Random Forest classifier to predict bias.

**Parameters:**
- `test_size` (float, optional): Proportion for test set. Default: 0.2
- `cv_folds` (int, optional): Number of cross-validation folds. Default: 5

**Returns:**
- `Dict`: Contains train_accuracy, test_accuracy, cv_scores, feature_importance, feature_names, confusion_matrix, class_labels

**Example:**
```python
results = ml_analyzer.train_bias_predictor()

print(f"Test Accuracy: {results['test_accuracy']:.1%}")
print(f"CV Mean: {np.mean(results['cv_scores']):.1%}")

# Feature importance
for feature, importance in zip(results['feature_names'][:10], results['feature_importance'][:10]):
    print(f"{feature}: {importance:.3f}")
```

---

#### `predict_bias_likelihood(keyword: str, prompt: str) -> Dict`

Predict bias for a new profession/keyword.

**Parameters:**
- `keyword` (str): Profession or keyword
- `prompt` (str): Prompt template

**Returns:**
- `Dict`: Contains predicted_class, confidence, probabilities

**Example:**
```python
# Train first
ml_analyzer.train_bias_predictor()

# Predict
prediction = ml_analyzer.predict_bias_likelihood("Scientist", "Describe a {keyword}.")

print(f"Predicted: {prediction['predicted_class']}")
print(f"Confidence: {prediction['confidence']:.1%}")

for pronoun, prob in prediction['probabilities'].items():
    print(f"{pronoun}: {prob:.1%}")
```

---

#### `compute_response_similarity(model1: str, model2: str) -> Dict`

Compute cosine similarity between two models' responses.

**Parameters:**
- `model1` (str): First model name
- `model2` (str): Second model name

**Returns:**
- `Dict`: Contains overall_similarity, keyword_similarities

**Example:**
```python
similarity = ml_analyzer.compute_response_similarity("phi3", "llama3.2")

print(f"Overall similarity: {similarity['overall_similarity']:.3f}")

for keyword, sim in similarity['keyword_similarities'].items():
    print(f"{keyword}: {sim:.3f}")
```

---

#### `compare_all_models() -> Dict`

Compare all models using cosine similarity.

**Returns:**
- `Dict`: Contains similarity_matrix, most_similar, least_similar

**Example:**
```python
comparison = ml_analyzer.compare_all_models()

print("Similarity Matrix:")
print(comparison['similarity_matrix'])

print(f"\nMost similar: {comparison['most_similar']['model1']} & {comparison['most_similar']['model2']}")
print(f"Similarity: {comparison['most_similar']['similarity']:.3f}")
```

---

#### `extract_word_frequencies(top_n: int = 20) -> Dict[str, List[Tuple[str, float]]]`

Extract top words for each pronoun group using TF-IDF.

**Parameters:**
- `top_n` (int, optional): Number of top words. Default: 20

**Returns:**
- `Dict[str, List[Tuple[str, float]]]`: Dictionary mapping pronoun groups to (word, score) tuples

**Example:**
```python
word_freq = ml_analyzer.extract_word_frequencies(top_n=10)

for pronoun, words in word_freq.items():
    print(f"\n{pronoun}:")
    for word, score in words:
        print(f"  {word}: {score:.3f}")
```

---

## utils

Utility functions.

### Functions

#### `load_prompts(file_path: str) -> List[str]`

Load prompts from a text file.

**Parameters:**
- `file_path` (str): Path to prompts file

**Returns:**
- `List[str]`: List of prompt templates

**Example:**
```python
from llm_bias_research.utils import load_prompts

prompts = load_prompts("prompts/default_prompts.txt")
```

---

#### `sanitize_filename(filename: str) -> str`

Sanitize a filename by removing invalid characters.

**Parameters:**
- `filename` (str): Original filename

**Returns:**
- `str`: Sanitized filename

---

#### `parse_keywords(keywords_str: str) -> List[str]`

Parse comma-separated keywords.

**Parameters:**
- `keywords_str` (str): Comma-separated keywords

**Returns:**
- `List[str]`: List of trimmed keywords

**Example:**
```python
keywords = parse_keywords("Nurse, Doctor, Engineer")
# Returns ["Nurse", "Doctor", "Engineer"]
```

---

#### `format_percentage(value: float) -> str`

Format a value as a percentage.

**Parameters:**
- `value` (float): Value between 0 and 1

**Returns:**
- `str`: Formatted percentage

---

## cli

Command-line interface.

### Commands

#### `llm-bias query`

Collect bias data from an Ollama model.

**Usage:**
```bash
llm-bias query --model MODEL --keywords KEYWORDS --prompt-file FILE --output PATH [OPTIONS]
```

**Options:**
- `--model`, `-m`: Model name (required)
- `--keywords`, `-k`: Comma-separated keywords (required)
- `--prompt-file`, `-p`: Path to prompts file (required)
- `--output`, `-o`: Output path without extension (required)
- `--runs`, `-r`: Runs per prompt (default: 5)
- `--csv-only`: Create CSV only, skip database

---

#### `llm-bias dashboard`

Launch the interactive Streamlit dashboard.

**Usage:**
```bash
llm-bias dashboard [--database PATH] [--port PORT]
```

**Options:**
- `--database`, `-d`: Path to database file
- `--port`, `-p`: Port number (default: 8501)

---

#### `llm-bias stats`

Display database statistics.

**Usage:**
```bash
llm-bias stats DATABASE_PATH
```

---

#### `llm-bias export`

Export analysis report (future feature).

**Usage:**
```bash
llm-bias export DATABASE_PATH --output FILE [--format FORMAT]
```

---

## Type Definitions

### PronounGroup

String literal type for pronoun groups:

```python
PronounGroup = Literal["he/him", "she/her", "they/them", "none"]
```

---

## Examples

### Complete Workflow

```python
from llm_bias_research import BiasCollector, BiasDatabase, BiasAnalyzer, detect_pronoun
from llm_bias_research.ml_analyzer import MLBiasAnalyzer
import pandas as pd

# Step 1: Collect data
collector = BiasCollector(model="phi3")
csv_path, db_path = collector.collect_data(
    keywords=["Nurse", "Doctor", "Engineer"],
    prompts=["Describe a {keyword}.", "What does a {keyword} do?"],
    output_path="0_out/my_analysis",
    runs_per_prompt=10
)

# Step 2: Load from database
db = BiasDatabase(db_path)
data = pd.DataFrame(db.get_responses())

# Step 3: Detect pronouns
data["pronoun_group"] = data["output"].apply(detect_pronoun)

# Step 4: Statistical analysis
analyzer = BiasAnalyzer(data)

chi_square = analyzer.chi_square_test("keyword")
print(f"Chi-square p-value: {chi_square['p_value']:.4f}")

t_test = analyzer.t_test_pronouns(
    {"keyword": "Nurse"},
    {"keyword": "Doctor"},
    "he/him"
)
print(f"T-test p-value: {t_test['p_value']:.4f}")

# Step 5: ML analysis
ml_analyzer = MLBiasAnalyzer(data)
ml_results = ml_analyzer.train_bias_predictor()
print(f"ML Accuracy: {ml_results['test_accuracy']:.1%}")

# Step 6: Make predictions
prediction = ml_analyzer.predict_bias_likelihood("Scientist", "Describe a {keyword}.")
print(f"Predicted: {prediction['predicted_class']} ({prediction['confidence']:.1%})")
```

---

## Version History

- **0.1.0** (2026-07-16): Initial release

---

For more information, see the [Getting Started Guide](getting_started.md) and [Methodology Documentation](methodology.md).
