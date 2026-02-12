"""Tests for message analyzer."""

import unittest
from git_evaluate.analyzers.message import MessageAnalyzer


class TestMessageAnalyzer(unittest.TestCase):
    """Test cases for MessageAnalyzer."""

    def setUp(self):
        self.analyzer = MessageAnalyzer()

    def test_empty_message(self):
        """Test empty message returns low score."""
        result = self.analyzer.analyze("")
        self.assertEqual(result['score'], 0)
        self.assertIn('Empty commit message', result['issues'])

    def test_conventional_commit_format(self):
        """Test conventional commit format is recognized."""
        result = self.analyzer.analyze("feat: add new feature")
        self.assertGreater(result['score'], 80)
        
    def test_subject_too_long(self):
        """Test subject line length check."""
        long_subject = "feat: " + "x" * 100
        result = self.analyzer.analyze(long_subject)
        self.assertLess(result['score'], 100)
        self.assertTrue(any('too long' in issue.lower() for issue in result['issues']))

    def test_subject_ideal_length(self):
        """Test ideal subject length."""
        result = self.analyzer.analyze("feat: add authentication")
        # Should have minimal penalties
        self.assertGreaterEqual(result['score'], 85)

    def test_unknown_conventional_type(self):
        """Test unknown conventional commit type."""
        result = self.analyzer.analyze("unknown: test message")
        self.assertTrue(any('unknown' in w.lower() for w in result['warnings']))

    def test_capitalization_check(self):
        """Test capitalization after colon."""
        result = self.analyzer.analyze("feat: add feature")
        # Should warn about lowercase after colon
        self.assertTrue(any('capital' in w.lower() for w in result['warnings']))

    def test_period_ending(self):
        """Test period at end of subject."""
        result = self.analyzer.analyze("feat: Add feature.")
        self.assertTrue(any('period' in w.lower() for w in result['warnings']))

    def test_blank_line_after_subject(self):
        """Test blank line between subject and body."""
        message_no_blank = "feat: Add feature\nThis is body"
        result = self.analyzer.analyze(message_no_blank)
        self.assertTrue(any('blank line' in w.lower() for w in result['warnings']))
        
        message_with_blank = "feat: Add feature\n\nThis is body"
        result = self.analyzer.analyze(message_with_blank)
        # Should not have blank line warning
        blank_warnings = [w for w in result['warnings'] if 'blank line' in w.lower()]
        self.assertEqual(len(blank_warnings), 0)

    def test_good_commit_message(self):
        """Test well-formatted commit message."""
        good_message = "feat: Add user authentication\n\nImplement JWT-based authentication with refresh tokens."
        result = self.analyzer.analyze(good_message)
        self.assertGreater(result['score'], 85)


if __name__ == '__main__':
    unittest.main()
