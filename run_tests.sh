#!/bin/bash

echo "🧪 RAC-NAS Test Runner"
echo "====================="

# Set up environment
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Ensure SPM file is the working version
if [ ! -f "src/core/spm.py" ]; then
    echo "❌ Missing src/core/spm.py file"
    exit 1
fi

# Run tests with proper configuration
echo "🚀 Running test suite..."
python -m pytest tests/ -v --tb=short --disable-warnings

echo ""
echo "📊 Test run completed!"