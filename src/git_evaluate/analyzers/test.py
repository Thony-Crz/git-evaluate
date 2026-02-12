"""Test presence analyzer for checking if tests are included."""

import re
from typing import Dict, List
import os


class TestAnalyzer:
    """Analyzes if tests are present in the changeset."""

    # Patterns to identify test files
    TEST_FILE_PATTERNS = [
        # Python
        r'test_.*\.py$',
        r'.*_test\.py$',
        # JavaScript/TypeScript
        r'.*\.test\.js$',
        r'.*\.test\.ts$',
        r'.*\.test\.jsx$',
        r'.*\.test\.tsx$',
        r'.*\.spec\.js$',
        r'.*\.spec\.ts$',
        r'.*\.spec\.jsx$',
        r'.*\.spec\.tsx$',
        # .NET (C#, F#)
        r'.*Tests?\.cs$',
        r'.*Tests?\.fs$',
        r'.*\.Tests?\.cs$',
        r'.*\.Tests?\.fs$',
        r'.*UnitTests?\.cs$',
        r'.*IntegrationTests?\.cs$',
        # Java
        r'.*Test\.java$',
        r'.*Tests\.java$',
        # Go
        r'.*_test\.go$',
        # Ruby
        r'.*_test\.rb$',
        # Test directories
        r'[Tt]est/.*',
        r'[Tt]ests/.*',
        r'__tests__/.*',
        r'.*\.Tests/.*',
        r'.*\.UnitTests/.*',
        r'.*\.IntegrationTests/.*',
    ]
    
    # .NET test framework using statements
    DOTNET_TEST_USINGS = [
        r'using\s+NUnit\.Framework',
        r'using\s+Xunit',
        r'using\s+Microsoft\.VisualStudio\.TestTools\.UnitTesting',
        r'using\s+FluentAssertions',
        r'using\s+Moq',
    ]
    
    # .NET test attributes
    DOTNET_TEST_ATTRIBUTES = [
        r'\[Test\]',
        r'\[TestMethod\]',
        r'\[Fact\]',
        r'\[Theory\]',
        r'\[TestFixture\]',
        r'\[TestClass\]',
    ]

    # Patterns to identify implementation files (non-test code)
    IMPL_FILE_PATTERNS = {
        '.py': [r'^(?!test_).*(?<!_test)\.py$'],
        '.js': [r'^(?!.*\.test\.js$)(?!.*\.spec\.js$).*\.js$'],
        '.ts': [r'^(?!.*\.test\.ts$)(?!.*\.spec\.ts$).*\.ts$'],
        '.jsx': [r'^(?!.*\.test\.jsx$)(?!.*\.spec\.jsx$).*\.jsx$'],
        '.tsx': [r'^(?!.*\.test\.tsx$)(?!.*\.spec\.tsx$).*\.tsx$'],
        '.cs': [r'^(?!.*Tests?\.cs$)(?!.*\.Tests?\.cs$)(?!.*UnitTests?\.cs$)(?!.*IntegrationTests?\.cs$).*\.cs$'],
        '.fs': [r'^(?!.*Tests?\.fs$)(?!.*\.Tests?\.fs$).*\.fs$'],
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

    def analyze(self, file_stats: List[Dict], diff_text: str = '') -> Dict:
        """
        Analyze if tests are present in the changeset.
        
        Args:
            file_stats: List of file statistics
            diff_text: Optional git diff text for content analysis
            
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
        
        # For .NET files, also check content for test indicators
        if diff_text:
            test_files.extend(self._detect_dotnet_tests_from_content(diff_text, file_stats, test_files))
            test_files = list(set(test_files))  # Remove duplicates

        # Calculate lines of code for stats
        test_lines = sum(f.get('additions', 0) for f in file_stats if f.get('filename') in test_files)
        impl_lines = sum(f.get('additions', 0) for f in file_stats if f.get('filename') in impl_files)

        # Analyze test coverage
        score -= self._check_test_presence(test_files, impl_files, other_files, file_stats)

        return {
            'score': max(0, score),
            'max_score': self.max_score,
            'issues': self.issues,
            'warnings': self.warnings,
            'suggestions': self.suggestions,
            'stats': {
                'test_files': len(test_files),
                'implementation_files': len(impl_files),
                'other_files': len(other_files),
                'test_lines': test_lines,
                'implementation_lines': impl_lines,
                'test_to_code_ratio': round(test_lines / impl_lines, 2) if impl_lines > 0 else 0
            }
        }

    def _is_test_file(self, filename: str) -> bool:
        """Check if a file is a test file."""
        for pattern in self.TEST_FILE_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                return True
        return False
    
    def _detect_dotnet_tests_from_content(self, diff_text: str, file_stats: List[Dict], 
                                          already_detected: List[str]) -> List[str]:
        """Detect .NET test files by analyzing diff content for test framework usings."""
        test_files = []
        
        # Parse diff to find .cs/.fs files with test indicators
        current_file = None
        file_content = []
        
        for line in diff_text.split('\n'):
            # Detect file header in diff
            if line.startswith('diff --git'):
                # Process previous file if any
                if current_file and current_file not in already_detected:
                    if self._content_has_test_indicators(file_content):
                        test_files.append(current_file)
                
                # Extract new filename
                parts = line.split(' b/')
                if len(parts) == 2:
                    current_file = parts[1]
                    file_content = []
            elif line.startswith('+') and not line.startswith('+++'):
                # Collect added lines
                file_content.append(line[1:])
        
        # Process last file
        if current_file and current_file not in already_detected:
            if self._content_has_test_indicators(file_content):
                test_files.append(current_file)
        
        return test_files
    
    def _content_has_test_indicators(self, lines: List[str]) -> bool:
        """Check if code content has .NET test framework indicators."""
        content = '\n'.join(lines)
        
        # Check for test framework using statements
        for pattern in self.DOTNET_TEST_USINGS:
            if re.search(pattern, content):
                return True
        
        # Check for test attributes
        for pattern in self.DOTNET_TEST_ATTRIBUTES:
            if re.search(pattern, content):
                return True
        
        return False
    
    def _detect_dotnet_tests_from_content(self, diff_text: str, file_stats: List[Dict], 
                                          already_detected: List[str]) -> List[str]:
        """Detect .NET test files by analyzing diff content for test framework usings."""
        test_files = []
        
        # Parse diff to find .cs/.fs files with test indicators
        current_file = None
        file_content = []
        
        for line in diff_text.split('\n'):
            # Detect file header in diff
            if line.startswith('diff --git'):
                # Process previous file if any
                if current_file and current_file not in already_detected:
                    if self._content_has_test_indicators(file_content):
                        test_files.append(current_file)
                
                # Extract new filename
                parts = line.split(' b/')
                if len(parts) == 2:
                    current_file = parts[1]
                    file_content = []
            elif line.startswith('+') and not line.startswith('+++'):
                # Collect added lines
                file_content.append(line[1:])
        
        # Process last file
        if current_file and current_file not in already_detected:
            if self._content_has_test_indicators(file_content):
                test_files.append(current_file)
        
        return test_files
    
    def _content_has_test_indicators(self, lines: List[str]) -> bool:
        """Check if code content has .NET test framework indicators."""
        content = '\n'.join(lines)
        
        # Check for test framework using statements
        for pattern in self.DOTNET_TEST_USINGS:
            if re.search(pattern, content):
                return True
        
        # Check for test attributes
        for pattern in self.DOTNET_TEST_ATTRIBUTES:
            if re.search(pattern, content):
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
                           other_files: List[str],
                           file_stats: List[Dict]) -> int:
        """Check if tests are included when implementation code changes (TDD approach)."""
        penalty = 0

        # If only documentation or config files changed, don't require tests
        if not impl_files and other_files:
            return 0

        # If no implementation files changed, no penalty
        if not impl_files:
            return 0

        # Calculate lines of code for test vs implementation files
        test_lines = 0
        impl_lines = 0
        
        for file_stat in file_stats:
            filename = file_stat.get('filename', '')
            additions = file_stat.get('additions', 0)
            
            if filename in test_files:
                test_lines += additions
            elif filename in impl_files:
                impl_lines += additions
        
        # If implementation code changed but no tests
        if impl_files and not test_files:
            self.issues.append(f"No test files found ({impl_lines} lines of implementation code added)")
            self.suggestions.append("Add or update tests to cover your changes (TDD: aim for 1:1 ratio)")
            penalty = 40
        elif impl_files and test_files:
            # TDD best practice: test lines >= implementation lines
            # Calculate ratio: test_lines / impl_lines
            if impl_lines > 0:
                ratio = test_lines / impl_lines
                
                if ratio < 0.3:
                    self.issues.append(f"Very low test coverage: {test_lines} test lines vs {impl_lines} impl lines (ratio: {ratio:.2f})")
                    self.suggestions.append("TDD best practice: aim for at least 1:1 test-to-code ratio")
                    penalty = 30
                elif ratio < 0.5:
                    self.warnings.append(f"Low test coverage: {test_lines} test lines vs {impl_lines} impl lines (ratio: {ratio:.2f})")
                    self.suggestions.append("Consider increasing test coverage (TDD target: >= 1:1)")
                    penalty = 20
                elif ratio < 1.0:
                    self.warnings.append(f"Moderate test coverage: {test_lines} test lines vs {impl_lines} impl lines (ratio: {ratio:.2f})")
                    self.suggestions.append("Good progress! TDD target is >= 1:1 ratio")
                    penalty = 10
                # ratio >= 1.0: Excellent! No penalty
            else:
                # Only test lines added (e.g., fixing tests), no penalty
                pass

        return penalty
