#!/bin/bash

echo "🧹 Cleaning up temporary test files"
echo "===================================="

# Remove temporary test scripts
echo "🗑️  Removing temporary test runners..."
rm -f test_basic.py
rm -f test_simple.py  
rm -f test_step_by_step.sh
rm -f test_clean.sh
rm -f test_final.sh
rm -f test_comprehensive.sh
rm -f run_tests.sh
rm -f run_working_tests.py
rm -f test_final_summary.sh
rm -f quick_fix_tests.sh
rm -f final_fix.sh

# Remove duplicate/backup SPM files
echo "🗑️  Removing duplicate SPM files..."
rm -f src/core/smp_complete.py
rm -f src/core/spm_complete.py
rm -f src/core/spm_fixed.py

# Remove minimal pytest config (keep main one)
echo "🗑️  Removing redundant config files..."
rm -f pytest_minimal.ini

# Remove any temporary storage directories that might have been created during tests
echo "🗑️  Cleaning up test storage..."
rm -rf storage/

# Remove Python cache files
echo "🗑️  Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "*.pyo" -delete 2>/dev/null

# Remove pytest cache
echo "🗑️  Removing pytest cache..."
rm -rf .pytest_cache/

# Keep these essential files:
echo ""
echo "✅ Keeping essential files:"
echo "   📁 src/ - Core application code"
echo "   📁 tests/ - Test suite"
echo "   📄 pytest.ini - Test configuration"
echo "   📄 requirements-test.txt - Test dependencies"
echo "   📄 README.md - Documentation"
echo "   📄 requirements.txt - Main dependencies"

echo ""
echo "🎯 Files cleaned up:"
echo "   ❌ Temporary test runners (test_*.py, test_*.sh)"
echo "   ❌ Duplicate SPM implementations"
echo "   ❌ Redundant config files"
echo "   ❌ Python cache files"
echo "   ❌ Pytest cache"
echo "   ❌ Test storage directories"

echo ""
echo "✨ Cleanup completed! Project is now clean and organized."
echo ""
echo "📊 Final project structure:"
tree -I '__pycache__|*.pyc|.pytest_cache' --dirsfirst 2>/dev/null || ls -la