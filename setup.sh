#!/bin/bash
# Setup script for LLM Bias Research project

set -e  # Exit on error

echo "🔍 LLM Bias Research - Setup Script"
echo "===================================="
echo ""

# Detect package manager
USE_UV=false
if command -v uv &> /dev/null; then
    USE_UV=true
    echo "✨ Detected UV - using fast package manager"
    echo ""
fi

# Check Python version
echo "1️⃣ Checking Python version..."
if [ "$USE_UV" = true ]; then
    python_version=$(uv python list | grep "3\." | head -1 | awk '{print $1}' | sed 's/cpython-//')
    if [ -z "$python_version" ]; then
        python_version=$(python3 --version 2>&1 | awk '{print $2}')
    fi
else
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
fi
required_version="3.9"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "   ✓ Python $python_version detected"
else
    echo "   ✗ Error: Python 3.9+ required (found $python_version)"
    exit 1
fi

# Check Ollama
echo ""
echo "2️⃣ Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    echo "   ✓ Ollama is installed"
    
    # List available models
    echo "   📦 Available models:"
    ollama list | tail -n +2 | awk '{print "      - " $1}' || echo "      (none)"
else
    echo "   ⚠️  Ollama not found"
    echo "   Please install from: https://ollama.ai/"
    read -p "   Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment and install
echo ""
if [ "$USE_UV" = true ]; then
    echo "3️⃣ Setting up with UV..."
    
    # UV automatically creates venv if needed
    if [ -d ".venv" ]; then
        echo "   ⚠️  .venv already exists, syncing..."
        uv sync --all-extras > /dev/null 2>&1
    else
        echo "   📦 Creating virtual environment and installing dependencies..."
        uv sync --all-extras > /dev/null 2>&1
        echo "   ✓ Virtual environment created at .venv"
    fi
    
    echo "   ✓ Package and dependencies installed"
    VENV_PATH=".venv"
    ACTIVATE_CMD="source .venv/bin/activate"
else
    echo "3️⃣ Creating virtual environment..."
    if [ -d "venv" ]; then
        echo "   ⚠️  venv already exists, skipping..."
    else
        python3 -m venv venv
        echo "   ✓ Virtual environment created"
    fi
    
    echo ""
    echo "4️⃣ Activating virtual environment..."
    source venv/bin/activate
    echo "   ✓ Virtual environment activated"
    
    echo ""
    echo "5️⃣ Installing package and dependencies..."
    pip install --upgrade pip > /dev/null 2>&1
    pip install -e ".[dev]" > /dev/null 2>&1
    echo "   ✓ Package installed"
    
    VENV_PATH="venv"
    ACTIVATE_CMD="source venv/bin/activate"
fi

# Run tests
echo ""
if [ "$USE_UV" = true ]; then
    echo "4️⃣ Running tests..."
    if uv run pytest -q; then
        echo "   ✓ All tests passed"
    else
        echo "   ⚠️  Some tests failed (this might be okay)"
    fi
else
    echo "6️⃣ Running tests..."
    if pytest -q; then
        echo "   ✓ All tests passed"
    else
        echo "   ⚠️  Some tests failed (this might be okay)"
    fi
fi

# Create directories
echo ""
if [ "$USE_UV" = true ]; then
    echo "5️⃣ Creating data directories..."
else
    echo "7️⃣ Creating data directories..."
fi
mkdir -p results reports data
echo "   ✓ Directories created"

# Summary
echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
if [ "$USE_UV" = true ]; then
    echo "  1. Run commands with: uv run llm-bias --help"
    echo "  2. Or activate venv: $ACTIVATE_CMD"
    echo "  3. Install a model: ollama pull phi3"
    echo "  4. Run first query: uv run llm-bias query --model phi3 --keywords \"Nurse,Doctor\" --prompt-file prompts/default_prompts.txt --output results/test"
    echo "  5. Launch dashboard: uv run llm-bias dashboard --database results/test.db"
else
    echo "  1. Activate virtual environment: $ACTIVATE_CMD"
    echo "  2. Install a model: ollama pull phi3"
    echo "  3. Run first query: llm-bias query --model phi3 --keywords \"Nurse,Doctor\" --prompt-file prompts/default_prompts.txt --output results/test"
    echo "  4. Launch dashboard: llm-bias dashboard --database results/test.db"
fi
else
    echo "   ⚠️  Some tests failed (this might be okay)"
fi

# Create directories
echo ""
echo "7️⃣ Creating data directories..."
mkdir -p results reports data
echo "   ✓ Directories created"

# Summary
echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Install a model: ollama pull phi3"
echo "  3. Run first query: llm-bias query --model phi3 --keywords \"Nurse,Doctor\" --prompt-file prompts/default_prompts.txt --output results/test"
echo "  4. Launch dashboard: llm-bias dashboard --database results/test.db"
echo ""
echo "📖 See docs/getting_started.md for detailed instructions"
