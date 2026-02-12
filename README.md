# git-evaluate

A CLI tool to analyze git staging changes before commit. Evaluates commit message quality, diff size and coherence, detects risks (sensitive files, secrets, binaries), and checks for test presence.

## Features

- **Message Quality Analysis**: Checks commit messages against conventional commit format, length guidelines, and clarity
- **Diff Analysis**: Evaluates the size and coherence of changes
- **Risk Detection**: Identifies sensitive files, potential secrets, and binary files
- **Test Presence**: Checks if tests are included with implementation changes
- **Scoring System**: Generates an overall score with detailed breakdown
- **JSON Output**: Structured output for CI/hooks integration
- **Exit Codes**: Returns appropriate exit codes for automated workflows
- **Modular Architecture**: Easily extensible for custom rules and future LLM integration

## Installation

```bash
# Clone the repository
git clone https://github.com/Thony-Crz/git-evaluate.git
cd git-evaluate

# Install dependencies
pip install -r requirements.txt

# Install the tool
pip install -e .
```

## Usage

### Basic Usage

```bash
# Evaluate staging area with a commit message
git-evaluate -m "feat: add new feature"

# Evaluate without message (message analysis will show lower score)
git-evaluate

# Output in JSON format for CI/hooks
git-evaluate -m "fix: bug fix" --json

# Specify repository path
git-evaluate --repo /path/to/repo -m "docs: update README"
```

### Example Output

```
======================================================================
GIT EVALUATE - Staging Area Analysis
======================================================================

Overall Score: 75.5/100 (GOOD)

Detailed Scores:
----------------------------------------------------------------------
  Message: 85/100
  Diff: 90/100
  Risk: 100/100
  Test: 60/100

WARNINGS (should fix):
----------------------------------------------------------------------
  ⚠ [message] Subject line is longer than recommended (55 chars, ideally ≤50)
  ⚠ [test] Low test-to-implementation ratio (1:3)

SUGGESTIONS:
----------------------------------------------------------------------
  → [message] Keep subject line under 50 characters
  → [test] Consider adding more test coverage

Change Statistics:
----------------------------------------------------------------------
  Files changed: 3
  Lines added: 45
  Lines deleted: 12
  Test files: 1
  Implementation files: 3

======================================================================
```

### JSON Output Example

```json
{
  "overall_score": 75.5,
  "max_score": 100,
  "status": "good",
  "exit_code": 0,
  "details": {
    "message": {
      "score": 85,
      "max_score": 100,
      "issues": [],
      "warnings": ["Subject line is longer than recommended"],
      "suggestions": ["Keep subject line under 50 characters"]
    },
    "diff": { ... },
    "risk": { ... },
    "test": { ... }
  },
  "summary": {
    "issues": [],
    "warnings": [...],
    "suggestions": [...]
  }
}
```

## Integration

### Git Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Get the commit message from the user
COMMIT_MSG=$(git log -1 --pretty=%B)

# Run git-evaluate
git-evaluate -m "$COMMIT_MSG" --json > /tmp/git-evaluate.json

EXIT_CODE=$?

if [ $EXIT_CODE -eq 2 ]; then
    echo "CRITICAL: Commit evaluation failed!"
    cat /tmp/git-evaluate.json
    exit 1
fi

exit 0
```

### CI Pipeline (GitHub Actions)

```yaml
- name: Evaluate Changes
  run: |
    git diff HEAD~1 --cached
    git-evaluate -m "${{ github.event.head_commit.message }}" --json
```

## Exit Codes

- `0`: Good/Excellent (score >= 60)
- `1`: Warning/Poor (40 <= score < 60)
- `2`: Critical (score < 40)
- `3`: Error (invalid repository, etc.)

## Scoring System

The tool evaluates four main aspects:

1. **Message Quality (25%)**: Conventional commit format, length, clarity
2. **Diff Analysis (25%)**: Size, number of files, coherence
3. **Risk Detection (30%)**: Sensitive files, secrets, binaries
4. **Test Presence (20%)**: Ratio of test files to implementation files

Overall scores:
- **90-100**: Excellent
- **60-89**: Good
- **40-59**: Warning
- **20-39**: Poor
- **0-19**: Critical

## Architecture

The tool follows a modular architecture:

```
src/git_evaluate/
├── __init__.py
├── cli.py              # CLI interface
├── evaluator.py        # Main evaluation orchestrator
└── analyzers/
    ├── __init__.py
    ├── message.py      # Commit message analyzer
    ├── diff.py         # Diff size and coherence analyzer
    ├── risk.py         # Risk detection analyzer
    └── test.py         # Test presence analyzer
```

Each analyzer is independent and can be extended or replaced. Future enhancements can include:
- Custom rule configurations
- LLM integration for advanced analysis
- Additional analyzers (documentation, code quality, etc.)

## Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests (when available)
pytest
```

### Adding Custom Analyzers

Create a new analyzer in `src/git_evaluate/analyzers/`:

```python
class CustomAnalyzer:
    def __init__(self):
        self.max_score = 100
        
    def analyze(self, *args) -> dict:
        return {
            'score': 100,
            'max_score': self.max_score,
            'issues': [],
            'warnings': [],
            'suggestions': []
        }
```

Add it to the evaluator in `evaluator.py`.

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.