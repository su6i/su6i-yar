#!/bin/bash

echo "🚀 Running Su6i Yar Diagnostic Tests..."
echo "======================================="

# Ensure we are in the root directory
cd "$(dirname "$0")"

# Activate Venv
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️  Virtual environment not found! Running with system python..."
fi

# Run TTS Test
python3 tests/test_tts_local.py

# Capture Exit Code
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ ALL SYSTEMS GO! You can restart the service."
else
    echo "❌ TESTS FAILED. Please check the logs above."
fi

exit $EXIT_CODE
