# Git Evaluate Examples

This directory contains example integrations for git-evaluate.

## Pre-commit Hook

The `pre-commit-hook.sh` script shows how to integrate git-evaluate into your git pre-commit hook.

### Installation

```bash
# Copy the hook to your repository
cp examples/pre-commit-hook.sh .git/hooks/pre-commit

# Make it executable
chmod +x .git/hooks/pre-commit
```

### Usage

The hook will automatically run when you try to commit. It will:
- Evaluate your staged changes
- Display warnings and errors
- Block the commit if critical issues are found (exit code 2)

## GitHub Actions Workflow

The `github-workflow.yml` example shows how to integrate git-evaluate into your CI/CD pipeline.

### Installation

```bash
# Copy to your workflows directory
cp examples/github-workflow.yml .github/workflows/git-evaluate.yml
```

### Features

- Runs on every pull request
- Evaluates the PR changes
- Fails the CI if critical issues are found
- Can be extended to post comments on the PR

## Custom Integration

You can integrate git-evaluate into any workflow by:

1. Running `git-evaluate -m "message" --json`
2. Parsing the JSON output
3. Using the `exit_code` field to determine if the evaluation passed:
   - `0`: Excellent/Good - safe to proceed
   - `1`: Warning/Poor - review recommended
   - `2`: Critical - should not proceed

### Example Python Integration

```python
import subprocess
import json

result = subprocess.run(
    ['git-evaluate', '-m', 'feat: add feature', '--json'],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)
print(f"Score: {data['overall_score']}/100")
print(f"Status: {data['status']}")

if data['exit_code'] == 2:
    print("Critical issues found!")
    sys.exit(1)
```

### Example Bash Integration

```bash
#!/bin/bash

# Run evaluation
git-evaluate -m "feat: new feature" --json > result.json
EXIT_CODE=$?

# Parse score
SCORE=$(cat result.json | jq -r '.overall_score')

echo "Score: $SCORE/100"

# Check exit code
if [ $EXIT_CODE -eq 2 ]; then
    echo "Critical issues - aborting"
    exit 1
fi
```
