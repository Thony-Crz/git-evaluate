"""Core evaluation engine for git-evaluate."""

import git
from typing import Dict, List, Optional
from .analyzers.message import MessageAnalyzer
from .analyzers.diff import DiffAnalyzer
from .analyzers.risk import RiskAnalyzer
from .analyzers.test import TestAnalyzer


class GitEvaluator:
    """Main evaluator that orchestrates all analyzers."""

    def __init__(self, repo_path: str = '.'):
        """
        Initialize the evaluator.
        
        Args:
            repo_path: Path to the git repository
        """
        try:
            self.repo = git.Repo(repo_path, search_parent_directories=True)
        except git.InvalidGitRepositoryError:
            raise ValueError(f"Not a git repository: {repo_path}")

        self.message_analyzer = MessageAnalyzer()
        self.diff_analyzer = DiffAnalyzer()
        self.risk_analyzer = RiskAnalyzer()
        self.test_analyzer = TestAnalyzer()

    def evaluate(self, message: Optional[str] = None) -> Dict:
        """
        Evaluate the current staging area.
        
        Args:
            message: Optional commit message to evaluate. If None, uses a placeholder.
            
        Returns:
            Dictionary with evaluation results
        """
        # Get staged changes
        diff_text = self._get_staged_diff()
        file_stats = self._get_file_stats()

        # Use provided message or placeholder
        commit_message = message if message else ""

        # Run all analyzers
        message_result = self.message_analyzer.analyze(commit_message)
        diff_result = self.diff_analyzer.analyze(diff_text, file_stats)
        risk_result = self.risk_analyzer.analyze(diff_text, file_stats)
        test_result = self.test_analyzer.analyze(file_stats)

        # Calculate overall score (weighted average)
        weights = {
            'message': 0.25,
            'diff': 0.25,
            'risk': 0.30,
            'test': 0.20
        }

        overall_score = (
            message_result['score'] * weights['message'] +
            diff_result['score'] * weights['diff'] +
            risk_result['score'] * weights['risk'] +
            test_result['score'] * weights['test']
        )

        # Aggregate all issues, warnings, and suggestions
        all_issues = []
        all_warnings = []
        all_suggestions = []

        for name, result in [
            ('message', message_result),
            ('diff', diff_result),
            ('risk', risk_result),
            ('test', test_result)
        ]:
            all_issues.extend([f"[{name}] {issue}" for issue in result.get('issues', [])])
            all_warnings.extend([f"[{name}] {warning}" for warning in result.get('warnings', [])])
            all_suggestions.extend([f"[{name}] {suggestion}" for suggestion in result.get('suggestions', [])])

        # Determine status and exit code
        status, exit_code = self._determine_status(overall_score, all_issues)

        return {
            'overall_score': round(overall_score, 2),
            'max_score': 100,
            'status': status,
            'exit_code': exit_code,
            'details': {
                'message': message_result,
                'diff': diff_result,
                'risk': risk_result,
                'test': test_result
            },
            'summary': {
                'issues': all_issues,
                'warnings': all_warnings,
                'suggestions': all_suggestions
            }
        }

    def _get_staged_diff(self) -> str:
        """Get the diff of staged changes."""
        try:
            # Get diff of staged changes
            diff = self.repo.git.diff('--cached')
            return diff
        except Exception:
            return ""

    def _get_file_stats(self) -> List[Dict]:
        """Get statistics for each staged file."""
        try:
            diff_index = self.repo.index.diff('HEAD')
            stats = []
            
            for diff_item in diff_index:
                # Get the diff stats for this file
                try:
                    diff_text = self.repo.git.diff('--cached', '--', diff_item.a_path)
                    additions = diff_text.count('\n+') - diff_text.count('\n+++')
                    deletions = diff_text.count('\n-') - diff_text.count('\n---')
                    
                    stats.append({
                        'filename': diff_item.a_path,
                        'additions': additions,
                        'deletions': deletions
                    })
                except Exception:
                    # If we can't get stats, just include filename
                    stats.append({
                        'filename': diff_item.a_path,
                        'additions': 0,
                        'deletions': 0
                    })
            
            return stats
        except Exception:
            return []

    def _determine_status(self, score: float, issues: List[str]) -> tuple:
        """
        Determine overall status and exit code.
        
        Args:
            score: Overall score
            issues: List of all issues
            
        Returns:
            Tuple of (status string, exit code)
        """
        # Exit codes for CI/hooks integration
        # 0: excellent/good, 1: warning, 2: poor/critical
        
        if score >= 80:
            return "excellent", 0
        elif score >= 60:
            return "good", 0
        elif score >= 40:
            return "warning", 1
        elif score >= 20:
            return "poor", 1
        else:
            return "critical", 2
