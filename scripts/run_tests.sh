#!/bin/bash

echo "🚀 Running Su6i Yar Diagnostic Tests..."
echo "======================================="

# Ensure we are in the root directory
# Ensure we are in the root directory
cd "$(dirname "$0")/.."

# Activate Venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️  Virtual environment not found! Running with system python..."
fi

# Run Tests
echo "⚠️ No local tests confgured (Sherpa removed)."
# python3 tests/test_tts_local.py

EXIT_CODE=0
