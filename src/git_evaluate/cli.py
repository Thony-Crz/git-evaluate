"""CLI interface for git-evaluate."""

import argparse
import json
import sys
from .evaluator import GitEvaluator


def format_text_output(result: dict) -> str:
    """Format evaluation result as human-readable text."""
    output = []
    
    # Header
    output.append("=" * 70)
    output.append("GIT EVALUATE - Staging Area Analysis")
    output.append("=" * 70)
    output.append("")
    
    # Overall score
    score = result['overall_score']
    status = result['status']
    output.append(f"Overall Score: {score}/100 ({status.upper()})")
    output.append("")
    
    # Details by analyzer
    output.append("Detailed Scores:")
    output.append("-" * 70)
    for name, details in result['details'].items():
        analyzer_score = details['score']
        max_score = details['max_score']
        output.append(f"  {name.capitalize()}: {analyzer_score}/{max_score}")
    output.append("")
    
    # Issues
    if result['summary']['issues']:
        output.append("ISSUES (must fix):")
        output.append("-" * 70)
        for issue in result['summary']['issues']:
            output.append(f"  ✗ {issue}")
        output.append("")
    
    # Warnings
    if result['summary']['warnings']:
        output.append("WARNINGS (should fix):")
        output.append("-" * 70)
        for warning in result['summary']['warnings']:
            output.append(f"  ⚠ {warning}")
        output.append("")
    
    # Suggestions
    if result['summary']['suggestions']:
        output.append("SUGGESTIONS:")
        output.append("-" * 70)
        for suggestion in result['summary']['suggestions']:
            output.append(f"  → {suggestion}")
        output.append("")
    
    # Statistics
    if 'stats' in result['details']['diff']:
        stats = result['details']['diff']['stats']
        output.append("Change Statistics:")
        output.append("-" * 70)
        output.append(f"  Files changed: {stats['files_changed']}")
        output.append(f"  Lines added: {stats['additions']}")
        output.append(f"  Lines deleted: {stats['deletions']}")
        output.append("")
    
    if 'stats' in result['details']['test']:
        stats = result['details']['test']['stats']
        output.append(f"  Test files: {stats['test_files']}")
        output.append(f"  Implementation files: {stats['implementation_files']}")
        if 'test_lines' in stats and 'implementation_lines' in stats:
            output.append(f"  Test lines: {stats['test_lines']}")
            output.append(f"  Implementation lines: {stats['implementation_lines']}")
            if 'test_to_code_ratio' in stats and stats['test_to_code_ratio'] > 0:
                output.append(f"  Test-to-code ratio: {stats['test_to_code_ratio']}:1")
        output.append("")
    
    output.append("=" * 70)
    
    return '\n'.join(output)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Evaluate git staging changes before commit',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate staging area with a commit message
  git-evaluate -m "feat: add new feature"
  
  # Evaluate a specific commit from history
  git-evaluate --commit abc123
  git-evaluate -c HEAD~1
  
  # Evaluate with JSON output for CI/hooks
  git-evaluate -m "fix: bug fix" --json
  
  # Evaluate without message (message analysis will be skipped)
  git-evaluate
  
Exit codes:
  0 - Good/Excellent (score >= 60)
  1 - Warning/Poor (40 <= score < 60)
  2 - Critical (score < 40)
        """
    )
    
    parser.add_argument(
        '-m', '--message',
        type=str,
        help='Commit message to evaluate'
    )
    
    parser.add_argument(
        '-c', '--commit',
        type=str,
        help='Evaluate a specific commit from history (e.g., HEAD~1, abc123)'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    
    parser.add_argument(
        '--repo',
        type=str,
        default='.',
        help='Path to git repository (default: current directory)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='git-evaluate 0.1.0'
    )
    
    args = parser.parse_args()
    
    try:
        # Create evaluator and run evaluation
        evaluator = GitEvaluator(args.repo)
        
        # Evaluate commit from history or staging area
        if args.commit:
            result = evaluator.evaluate_commit(args.commit)
        else:
            result = evaluator.evaluate(message=args.message)
        
        # Output results
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(format_text_output(result))
        
        # Exit with appropriate code
        sys.exit(result['exit_code'])
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == '__main__':
    main()
