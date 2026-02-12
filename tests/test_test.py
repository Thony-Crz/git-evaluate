"""Tests for test analyzer."""

import unittest
from git_evaluate.analyzers.test import TestAnalyzer


class TestTestAnalyzer(unittest.TestCase):
    """Test cases for TestAnalyzer."""

    def setUp(self):
        self.analyzer = TestAnalyzer()

    def test_no_files(self):
        """Test with no files."""
        result = self.analyzer.analyze([])
        self.assertEqual(result['score'], 100)

    def test_test_file_detection_python(self):
        """Test detection of Python test files."""
        file_stats = [
            {'filename': 'test_main.py', 'additions': 50, 'deletions': 0},
            {'filename': 'main_test.py', 'additions': 30, 'deletions': 0}
        ]
        result = self.analyzer.analyze(file_stats)
        self.assertEqual(result['stats']['test_files'], 2)

    def test_test_file_detection_javascript(self):
        """Test detection of JavaScript test files."""
        file_stats = [
            {'filename': 'component.test.js', 'additions': 50, 'deletions': 0},
            {'filename': 'util.spec.ts', 'additions': 30, 'deletions': 0}
        ]
        result = self.analyzer.analyze(file_stats)
        self.assertEqual(result['stats']['test_files'], 2)

    def test_implementation_file_detection(self):
        """Test detection of implementation files."""
        file_stats = [
            {'filename': 'src/main.py', 'additions': 50, 'deletions': 0},
            {'filename': 'src/utils.py', 'additions': 30, 'deletions': 0}
        ]
        result = self.analyzer.analyze(file_stats)
        self.assertEqual(result['stats']['implementation_files'], 2)

    def test_config_files_ignored(self):
        """Test that config files are not counted as implementation."""
        file_stats = [
            {'filename': 'README.md', 'additions': 50, 'deletions': 0},
            {'filename': 'setup.py', 'additions': 30, 'deletions': 0},
            {'filename': '.gitignore', 'additions': 10, 'deletions': 0}
        ]
        result = self.analyzer.analyze(file_stats)
        self.assertEqual(result['stats']['implementation_files'], 0)

    def test_implementation_without_tests(self):
        """Test implementation changes without tests get penalty."""
        file_stats = [
            {'filename': 'src/main.py', 'additions': 100, 'deletions': 10},
            {'filename': 'src/utils.py', 'additions': 50, 'deletions': 5}
        ]
        result = self.analyzer.analyze(file_stats)
        self.assertLess(result['score'], 100)
        self.assertTrue(any('no test' in i.lower() for i in result['issues']))

    def test_implementation_with_tests(self):
        """Test implementation with adequate tests."""
        file_stats = [
            {'filename': 'src/main.py', 'additions': 50, 'deletions': 0},
            {'filename': 'tests/test_main.py', 'additions': 50, 'deletions': 0}
        ]
        result = self.analyzer.analyze(file_stats)
        # Should have high score with 1:1 ratio
        self.assertGreater(result['score'], 85)

    def test_low_test_ratio(self):
        """Test low test-to-implementation ratio."""
        file_stats = [
            {'filename': 'src/file1.py', 'additions': 50, 'deletions': 0},
            {'filename': 'src/file2.py', 'additions': 50, 'deletions': 0},
            {'filename': 'src/file3.py', 'additions': 50, 'deletions': 0},
            {'filename': 'tests/test_file1.py', 'additions': 20, 'deletions': 0}
        ]
        result = self.analyzer.analyze(file_stats)
        self.assertLess(result['score'], 100)
        self.assertTrue(any('test' in w.lower() and 'ratio' in w.lower() 
                          for w in result['warnings']))

    def test_only_documentation_changes(self):
        """Test that only documentation changes don't require tests."""
        file_stats = [
            {'filename': 'README.md', 'additions': 100, 'deletions': 20},
            {'filename': 'docs/guide.md', 'additions': 50, 'deletions': 10}
        ]
        result = self.analyzer.analyze(file_stats)
        # Should have perfect score
        self.assertEqual(result['score'], 100)


if __name__ == '__main__':
    unittest.main()
