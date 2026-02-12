"""Test presence analyzer for checking if tests are included."""

import re
from typing import Dict, List
import os


class TestAnalyzer:
    """Analyzes if tests are present in the changeset."""

    # Patterns to identify test files
    TEST_FILE_PATTERNS = [
        r'test_.*\.py$',
        r'.*_test\.py$',
        r'.*\.test\.js$',
        r'.*\.test\.ts$',
        r'.*\.test\.jsx$',
        r'.*\.test\.tsx$',
        r'.*\.spec\.js$',
        r'.*\.spec\.ts$',
        r'.*\.spec\.jsx$',
        r'.*\.spec\.tsx$',
        r'test/.*',
        r'tests/.*',
        r'__tests__/.*',
        r'.*Test\.java$',
        r'.*Tests\.java$',
        r'.*_test\.go$',
        r'.*_test\.rb$',
        r'test\..*',
    ]

    # Patterns to identify implementation files (non-test code)
    IMPL_FILE_PATTERNS = {
        '.py': [r'^(?!test_).*(?<!_test)\.py$'],
        '.js': [r'^(?!.*\.test\.js$)(?!.*\.spec\.js$).*\.js$'],
        '.ts': [r'^(?!.*\.test\.ts$)(?!.*\.spec\.ts$).*\.ts$'],
        '.jsx': [r'^(?!.*\.test\.jsx$)(?!.*\.spec\.jsx$).*\.jsx$'],
        '.tsx': [r'^(?!.*\.test\.tsx$)(?!.*\.spec\.tsx$).*\.tsx$'],
        '.java': [r'^(?!.*Test\.java$)(?!.*Tests\.java$).*\.java$'],
        '.go': [r'^(?!.*_test\.go$).*\.go$'],
        '.rb': [r'^(?!.*_test\.rb$).*\.rb$'],
    }

    # Directories typically containing implementation code
    IMPL_DIRECTORIES = {'src', 'lib', 'app', 'pkg', 'internal'}

    def __init__(self):
        self.max_score = 100
        self.issues = []
        self.warnings = []
        self.suggestions = []

    def analyze(self, file_stats: List[Dict]) -> Dict:
        """
        Analyze if tests are present in the changeset.
        
        Args:
            file_stats: List of file statistics
            
        Returns:
            Dictionary with score, issues, warnings, and suggestions
        """
        score = self.max_score
        self.issues = []
        self.warnings = []
        self.suggestions = []

        if not file_stats:
            return {
                'score': 100,
                'max_score': self.max_score,
                'issues': [],
                'warnings': [],
                'suggestions': []
            }

        # Categorize files
        test_files = []
        impl_files = []
        other_files = []

        for file_stat in file_stats:
            filename = file_stat.get('filename', '')
            
            if self._is_test_file(filename):
                test_files.append(filename)
            elif self._is_implementation_file(filename):
                impl_files.append(filename)
            else:
                other_files.append(filename)

        # Analyze test coverage
        score -= self._check_test_presence(test_files, impl_files, other_files)

        return {
            'score': max(0, score),
            'max_score': self.max_score,
            'issues': self.issues,
            'warnings': self.warnings,
            'suggestions': self.suggestions,
            'stats': {
                'test_files': len(test_files),
                'implementation_files': len(impl_files),
                'other_files': len(other_files)
            }
        }

    def _is_test_file(self, filename: str) -> bool:
        """Check if a file is a test file."""
        for pattern in self.TEST_FILE_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                return True
        return False

    def _is_implementation_file(self, filename: str) -> bool:
        """Check if a file is an implementation file."""
        # Skip config files and documentation
        basename = os.path.basename(filename)
        if basename in {'.gitignore', 'README.md', 'LICENSE', 'setup.py', 
                       'package.json', 'requirements.txt', 'Makefile'}:
            return False
        
        # Check by extension
        _, ext = os.path.splitext(filename)
        
        if ext in self.IMPL_FILE_PATTERNS:
            for pattern in self.IMPL_FILE_PATTERNS[ext]:
                if re.search(pattern, basename):
                    # Also check if in implementation directory
                    parts = filename.split('/')
                    if len(parts) > 1 and parts[0] in self.IMPL_DIRECTORIES:
                        return True
                    # Or if it has significant additions (likely code, not just config)
                    return True
        
        return False

    def _check_test_presence(self, test_files: List[str], 
                           impl_files: List[str], 
                           other_files: List[str]) -> int:
        """Check if tests are included when implementation code changes."""
        penalty = 0

        # If only documentation or config files changed, don't require tests
        if not impl_files and other_files:
            return 0

        # If no implementation files changed, no penalty
        if not impl_files:
            return 0

        # If implementation files changed but no tests
        if impl_files and not test_files:
            self.issues.append(f"No test files found ({len(impl_files)} implementation files changed)")
            self.suggestions.append("Add or update tests to cover your changes")
            penalty = 40
        elif impl_files and test_files:
            # Check ratio based on file count
            # Note: This uses file counts rather than line counts for simplicity.
            # Future enhancement: Consider line-based ratios for more accurate assessment.
            ratio = len(test_files) / len(impl_files)
            if ratio < 0.3:
                self.warnings.append(f"Few test files relative to implementation ({len(test_files)} test vs {len(impl_files)} impl)")
                self.suggestions.append("Consider adding more test coverage")
                penalty = 20
            elif ratio < 0.5:
                self.warnings.append(f"Low test-to-implementation ratio ({len(test_files)}:{len(impl_files)})")
                penalty = 10

        return penalty
