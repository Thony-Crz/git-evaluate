"""Tests for diff analyzer."""

import unittest
from git_evaluate.analyzers.diff import DiffAnalyzer


class TestDiffAnalyzer(unittest.TestCase):
    """Test cases for DiffAnalyzer."""

    def setUp(self):
        self.analyzer = DiffAnalyzer()

    def test_no_changes(self):
        """Test empty diff."""
        result = self.analyzer.analyze("", [])
        self.assertEqual(result['score'], 100)
        self.assertTrue(any('no changes' in w.lower() for w in result['warnings']))

    def test_small_diff(self):
        """Test small diff gets high score."""
        file_stats = [
            {'filename': 'file1.py', 'additions': 10, 'deletions': 5}
        ]
        result = self.analyzer.analyze("some diff", file_stats)
        self.assertGreater(result['score'], 90)

    def test_large_diff(self):
        """Test large diff gets penalty."""
        file_stats = [
            {'filename': 'file1.py', 'additions': 600, 'deletions': 500}
        ]
        result = self.analyzer.analyze("large diff", file_stats)
        self.assertLess(result['score'], 100)
        self.assertTrue(any('large diff' in i.lower() or 'large diff' in w.lower() 
                          for i in result['issues'] for w in result['warnings']))

    def test_many_files(self):
        """Test many files changed gets penalty."""
        file_stats = [
            {'filename': f'file{i}.py', 'additions': 10, 'deletions': 5}
            for i in range(25)
        ]
        result = self.analyzer.analyze("many files", file_stats)
        self.assertLess(result['score'], 100)
        self.assertTrue(any('files' in i.lower() or 'files' in w.lower() 
                          for i in result['issues'] for w in result['warnings']))

    def test_stats_calculation(self):
        """Test statistics are calculated correctly."""
        file_stats = [
            {'filename': 'file1.py', 'additions': 10, 'deletions': 5},
            {'filename': 'file2.py', 'additions': 15, 'deletions': 3}
        ]
        result = self.analyzer.analyze("diff", file_stats)
        
        self.assertEqual(result['stats']['files_changed'], 2)
        self.assertEqual(result['stats']['additions'], 25)
        self.assertEqual(result['stats']['deletions'], 8)
        self.assertEqual(result['stats']['total_changes'], 33)

    def test_coherence_many_directories(self):
        """Test coherence check for many directories."""
        file_stats = [
            {'filename': f'dir{i}/file.py', 'additions': 10, 'deletions': 5}
            for i in range(10)
        ]
        result = self.analyzer.analyze("spread out", file_stats)
        self.assertTrue(any('directories' in w.lower() for w in result['warnings']))


if __name__ == '__main__':
    unittest.main()
