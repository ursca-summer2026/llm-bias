# Contributing to LLM Bias Research

Thank you for your interest in contributing to the LLM Bias Research project! This document provides guidelines and instructions for contributing.

## 🤝 Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and professional in all interactions.

## 🚀 Getting Started

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/llm-bias-research.git
   cd llm-bias-research
   ```

2. **Choose your package manager**

   **Option A: Using UV (Recommended - faster)**
   ```bash
   # Install UV if needed
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install all dependencies including dev tools
   uv sync --all-extras
   
   # Install pre-commit hooks
   uv run pre-commit install
   
   # Run tests
   uv run pytest
   ```

   **Option B: Using pip (Traditional)**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies
   pip install -e ".[dev]"
   
   # Install pre-commit hooks
   pre-commit install
   
   # Run tests
   pytest
   ```

## 🏗️ Development Workflow

### Branching Strategy

- `main` - stable, production-ready code
- `develop` - integration branch for features
- `feature/your-feature-name` - feature branches
- `fix/bug-description` - bug fix branches

### Making Changes

   **Using UV:**
   ```bash
   # Run all tests
   uv run pytest

   # Run with coverage
   uv run pytest --cov

   # Format code
   uv run black src/ tests/

   # Lint code
   uv run ruff check src/ tests/

   # Type checking
   uv run mypy src/
   ```
   
   **Using pip:**
   
1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clear, documented code
   - Follow the coding standards (see below)
   - Add tests for new functionality

3. **Run tests and linters**
   ```bash
   # Run all tests
   pytest

   # Run with coverage
   pytest --cov

   # Format code
   black src/ tests/

   # Lint code
   ruff check src/ tests/

   # Type checking
   mypy src/
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - new feature
   - `fix:` - bug fix
   - `docs:` - documentation changes
   - `test:` - adding/updating tests
   - `refactor:` - code refactoring
   - `style:` - formatting changes
   - `chore:` - maintenance tasks

5. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📝 Coding Standards

### Python Style Guide

- **PEP 8** compliance (enforced by Black and Ruff)
- **Line length**: 100 characters
- **Type hints**: Required for all public functions
- **Docstrings**: Google style for all public modules, classes, and functions

### Example Function

```python
def analyze_bias(
    responses: list[str],
    keyword: str,
    threshold: float = 0.5
) -> dict[str, float]:
    """Analyze gender bias in LLM responses.

    Args:
        responses: List of model response strings to analyze.
        keyword: The profession or keyword being tested.
        threshold: Minimum confidence threshold for classification.

    Returns:
        Dictionary mapping pronoun groups to their proportions.

    Raises:
        ValueError: If responses list is empty.

    Example:
        >>> analyze_bias(["She is a nurse."], "nurse")
        {'she/her': 1.0, 'he/him': 0.0, 'they/them': 0.0, 'none': 0.0}
    """
    if not responses:
        raise ValueError("Responses list cannot be empty")
    
    # Implementation here
    ...
```

### Testing Requirements

- **Unit tests** for all new functions
- **Integration tests** for workflows
- **Minimum 80% code coverage**
- Tests should be fast and independent

Example test:

```python
import pytest
from llm_bias_research.bias_detector import detect_pronoun


class TestBiasDetector:
    """Tests for pronoun detection functionality."""

    def test_detect_male_pronoun(self):
        """Should detect he/him pronouns correctly."""
        result = detect_pronoun("He is a doctor.")
        assert result == "he/him"

    def test_detect_female_pronoun(self):
        """Should detect she/her pronouns correctly."""
        result = detect_pronoun("She is a nurse.")
        assert result == "she/her"

    @pytest.mark.parametrize("text,expected", [
        ("He met her.", "he/him"),
        ("She met him.", "she/her"),
    ])
    def test_pronoun_frequency(self, text, expected):
        """Should handle multiple pronouns based on frequency."""
        assert detect_pronoun(text) == expected
```

## 📚 Documentation

### When to Document

- All public APIs
- Complex algorithms
- Non-obvious design decisions
- Configuration options
- Usage examples

### Documentation Format

- **Code**: Google-style docstrings
- **Markdown**: For guides and READMEs
- **Type hints**: Serve as inline documentation

### Updating Documentation

If you change functionality, update:
- Function/class docstrings
- README.md (if user-facing)
- docs/ directory (if architectural)
- CHANGELOG.md

## 🧪 Testing Guidelines

### Test Organization

```
tests/
├── unit/              # Fast, isolated unit tests
├── integration/       # Multi-component tests
└── fixtures/          # Shared test data
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_collector.py

# Specific test
pytest tests/test_collector.py::test_query_model

# With coverage
pytest --cov --cov-report=html

# Skip slow tests
pytest -m "not slow"

# Integration tests only
pytest -m integration
```

### Test Markers

- `@pytest.mark.slow` - Tests taking >1 second
- `@pytest.mark.integration` - Multi-component tests
- `@pytest.mark.requires_ollama` - Needs Ollama running

## 🐛 Reporting Bugs

### Before Submitting

1. Check existing issues
2. Verify it's reproducible
3. Test with the latest version

### Bug Report Template

```markdown
**Describe the bug**
Clear description of what's wrong.

**To Reproduce**
Steps to reproduce:
1. Run command '...'
2. See error

**Expected behavior**
What should have happened.

**Environment**
- OS: [e.g., macOS 13.5]
- Python: [e.g., 3.11.5]
- Package version: [e.g., 0.1.0]
- Ollama version: [e.g., 0.1.27]

**Additional context**
Logs, screenshots, etc.
```

## 💡 Feature Requests

We welcome feature suggestions! Please:

1. Check if it's already requested
2. Describe the use case
3. Explain why it's valuable
4. Propose an implementation (optional)

## 📋 Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Branch is up to date with main

### PR Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?

## Checklist
- [ ] Tests pass
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] Self-review completed
```

### Review Process

1. Automated checks must pass
2. At least one maintainer approval required
3. All review comments addressed
4. CI/CD pipeline passes

## 🔄 Release Process

Releases are managed by maintainers:

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release tag
4. Build and publish to PyPI

## 💬 Communication

- **Issues**: Bug reports and feature requests
- **Discussions**: Questions and general discussion
- **Pull Requests**: Code contributions

## 🙏 Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- CONTRIBUTORS.md file

Thank you for contributing to LLM Bias Research! 🎉
