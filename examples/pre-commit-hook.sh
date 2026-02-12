#!/bin/bash
#
# Example pre-commit hook for git-evaluate
# Install by copying to .git/hooks/pre-commit and making it executable
#

# Get the commit message from git
# Note: For pre-commit hooks, we need to read the message from the commit-msg file
# This example shows how to integrate git-evaluate into your workflow

# Check if git-evaluate is installed
if ! command -v git-evaluate &> /dev/null; then
    echo "Warning: git-evaluate not found. Skipping evaluation."
    exit 0
fi

# Run evaluation on staged changes
# Using a placeholder message since we don't have the actual message yet in pre-commit
git-evaluate --json > /tmp/git-evaluate-result.json
EXIT_CODE=$?

# Display results
echo "Git Evaluate Results:"
cat /tmp/git-evaluate-result.json | python3 -m json.tool

# Exit based on severity
if [ $EXIT_CODE -eq 2 ]; then
    echo ""
    echo "ERROR: Commit evaluation failed with critical issues!"
    echo "Please fix the issues above before committing."
    exit 1
elif [ $EXIT_CODE -eq 1 ]; then
    echo ""
    echo "WARNING: Commit has some issues. Consider fixing them."
    # Allow commit but warn user
    exit 0
fi

echo ""
echo "✓ Commit evaluation passed!"
exit 0
