#!/bin/bash

# Script to reorganize files in SynapseDTE project
# Run this from the project root directory

echo "Starting file reorganization..."

# Create directory structure if not exists
echo "Creating directory structure..."
mkdir -p scripts/utils scripts/debug scripts/setup scripts/migration
mkdir -p _reference/documents/analysis _reference/documents/implementation_plans 
mkdir -p _reference/documents/guides _reference/documents/summaries _reference/documents/temporal

# Move debug and test scripts to scripts/debug/
echo "Moving debug scripts..."
for file in check_*.py test_*.py debug_*.py verify_*.py list_*.py update_*.py complete_*.py; do
    if [ -f "$file" ]; then
        echo "  Moving $file to scripts/debug/"
        mv "$file" scripts/debug/
    fi
done

# Move setup scripts to scripts/setup/
echo "Moving setup scripts..."
if [ -f "scripts/create_test_users.py" ]; then mv "scripts/create_test_users.py" scripts/setup/; fi
if [ -f "scripts/init_database.py" ]; then mv "scripts/init_database.py" scripts/setup/; fi
if [ -f "scripts/setup_database.py" ]; then mv "scripts/setup_database.py" scripts/setup/; fi
for file in scripts/create_*.py scripts/init_*.py scripts/setup_*.py; do
    if [ -f "$file" ]; then
        echo "  Moving $file to scripts/setup/"
        mv "$file" scripts/setup/
    fi
done

# Move analysis documents
echo "Moving analysis documents..."
for file in *_ANALYSIS.md *ANALYSIS*.md; do
    if [ -f "$file" ]; then
        echo "  Moving $file to _reference/documents/analysis/"
        mv "$file" _reference/documents/analysis/
    fi
done

# Move implementation documents
echo "Moving implementation documents..."
for file in *_IMPLEMENTATION*.md IMPLEMENTATION_*.md *_PLAN.md; do
    if [ -f "$file" ]; then
        echo "  Moving $file to _reference/documents/implementation_plans/"
        mv "$file" _reference/documents/implementation_plans/
    fi
done

# Move guides
echo "Moving guide documents..."
for file in *_GUIDE.md *GUIDE*.md; do
    if [ -f "$file" ]; then
        echo "  Moving $file to _reference/documents/guides/"
        mv "$file" _reference/documents/guides/
    fi
done

# Move summaries and status reports
echo "Moving summary documents..."
for file in *_SUMMARY.md *_STATUS.md *_REPORT.md; do
    if [ -f "$file" ]; then
        echo "  Moving $file to _reference/documents/summaries/"
        mv "$file" _reference/documents/summaries/
    fi
done

# Move Temporal-related documents
echo "Moving Temporal documents..."
for file in TEMPORAL_*.md; do
    if [ -f "$file" ]; then
        echo "  Moving $file to _reference/documents/temporal/"
        mv "$file" _reference/documents/temporal/
    fi
done

# Move SQL files to scripts/migration/
echo "Moving SQL files..."
for file in *.sql; do
    if [ -f "$file" ]; then
        echo "  Moving $file to scripts/migration/"
        mv "$file" scripts/migration/
    fi
done

# Move test result JSON files
echo "Moving test result files..."
mkdir -p test_results
for file in test_*.json; do
    if [ -f "$file" ]; then
        echo "  Moving $file to test_results/"
        mv "$file" test_results/
    fi
done

echo "File reorganization complete!"
echo ""
echo "Summary of changes:"
echo "- Debug/test scripts moved to: scripts/debug/"
echo "- Setup scripts moved to: scripts/setup/" 
echo "- Analysis documents moved to: _reference/documents/analysis/"
echo "- Implementation plans moved to: _reference/documents/implementation_plans/"
echo "- Guides moved to: _reference/documents/guides/"
echo "- Summaries moved to: _reference/documents/summaries/"
echo "- Temporal docs moved to: _reference/documents/temporal/"
echo "- SQL files moved to: scripts/migration/"
echo "- Test results moved to: test_results/"
echo ""
echo "Note: Some important files like README.md and CLAUDE.md remain at root level"