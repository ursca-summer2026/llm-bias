# UV Quick Reference

This project now supports **UV**, a blazingly fast Python package manager (10-100x faster than pip).

## What is UV?

UV is a next-generation Python package manager written in Rust that:
- ⚡ Installs packages 10-100x faster than pip
- 🔒 Creates reproducible environments with `uv.lock`
- 📦 Manages Python versions, virtual environments, and packages
- 💾 Shares cache across projects to save disk space
- 🎯 Drop-in replacement for pip with minimal changes

## Installation

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip (though this defeats the speed purpose!)
pip install uv
```

## Quick Start

### Install Project Dependencies

```bash
# Install everything (creates .venv automatically)
uv sync --all-extras

# Install core dependencies only
uv sync

# Install specific extras
uv sync --extra dev
uv sync --extra export
```

### Running Commands

> **Important:** All commands must be run from the `llm-bias-research` project directory.

```bash
# Ensure you're in the correct directory
cd llm-bias-research

# Run CLI commands directly (no activation needed)
uv run llm-bias --help
uv run llm-bias query --model phi3 --keywords "Nurse,Doctor" \
  --prompt-file prompts/default_prompts.txt \
  --output 0_out/test --max-tokens 500

# Run tests
uv run pytest

# Run linters/formatters
uv run black src/
uv run ruff check src/
uv run mypy src/

# Launch dashboard
uv run llm-bias dashboard --database 0_out/test.db
```

### Managing Dependencies

```bash
# Add a new dependency
uv add requests

# Add a dev dependency
uv add --dev pytest-asyncio

# Remove a dependency
uv remove requests

# Update all dependencies
uv sync --upgrade

# Update uv.lock without installing
uv lock --upgrade
```

### Virtual Environment

```bash
# UV creates .venv automatically on first sync
# You can still activate it manually if needed:

# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# Or let UV handle it:
uv run python  # Uses .venv automatically
```

## Performance Comparison

Real-world timings from this project:

| Operation | pip | UV | Speedup |
|-----------|-----|-----|---------|
| Fresh install (174 packages) | ~2 minutes | **888ms** | ~135x |
| Reinstall (cached) | ~30 seconds | **<100ms** | ~300x |
| Lock file generation | N/A | ~5 seconds | - |

## UV vs pip Commands

| pip | UV | Notes |
|-----|-----|-------|
| `pip install -e .` | `uv sync` | Install project |
| `pip install -e ".[dev]"` | `uv sync --all-extras` | Install with extras |
| `pip install package` | `uv add package` | Add dependency |
| `pip install -r requirements.txt` | `uv pip install -r requirements.txt` | Requirements file |
| `python -m venv venv` | Automatic | UV creates .venv |
| `source venv/bin/activate` | Not needed | Use `uv run` |
| `python script.py` | `uv run python script.py` | Run scripts |
| `pytest` | `uv run pytest` | Run commands |

## Project Files

- **`.python-version`** - Specifies Python 3.9 for UV
- **`uv.lock`** - Lock file with exact versions (like package-lock.json)
- **`.venv/`** - Virtual environment (UV default, gitignored)
- **`pyproject.toml`** - Project config (unchanged, works with UV)

## Common Tasks

### Daily Development

```bash
# Update dependencies
uv sync --upgrade

# Run tests after changes
uv run pytest

# Format code
uv run black src/ tests/

# Type check
uv run mypy src/

# Launch dashboard for testing
uv run llm-bias dashboard --database 0_out/test.db
```

### Clean Install

```bash
# Remove old environments
rm -rf .venv venv

# Fresh install
uv sync --all-extras

# Verify
uv run llm-bias --version
uv run pytest
```

### CI/CD Pipeline

```bash
# Install UV in CI
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest --cov

# Run linters
uv run ruff check src/
```

## Troubleshooting

### "VIRTUAL_ENV warning"
If you see `warning: VIRTUAL_ENV=venv does not match the project environment path .venv`, either:
- Deactivate the old venv: `deactivate`
- Or ignore it - UV will use `.venv` correctly

### UV not found
```bash
# Ensure UV is in PATH
export PATH="$HOME/.local/bin:$PATH"

# Or reinstall
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Switching back to pip
```bash
# UV doesn't break pip - you can still use it
source .venv/bin/activate
pip list  # Works fine
```

## Benefits for This Project

1. **Faster CI/CD** - Tests run faster with quick dependency installs
2. **Reproducible Builds** - `uv.lock` ensures everyone has exact same versions
3. **Better Developer Experience** - No waiting for pip to resolve dependencies
4. **Disk Space Savings** - Shared cache means less duplication
5. **Easier Onboarding** - New contributors get up and running in seconds

## Backward Compatibility

UV is **fully backward compatible**:
- Existing `pip` workflows still work
- `pyproject.toml` unchanged
- Users can choose pip or UV
- Both `venv/` and `.venv/` supported

## Learn More

- [UV Documentation](https://docs.astral.sh/uv/)
- [UV GitHub](https://github.com/astral-sh/uv)
- [Astral Blog](https://astral.sh/blog)

---

**TL;DR:** Use `uv sync --all-extras` to install, then `uv run <command>` to run anything. It's 100x faster than pip and just works.
