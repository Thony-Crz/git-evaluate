"""Tests for risk analyzer."""

import unittest
from git_evaluate.analyzers.risk import RiskAnalyzer


class TestRiskAnalyzer(unittest.TestCase):
    """Test cases for RiskAnalyzer."""

    def setUp(self):
        self.analyzer = RiskAnalyzer()

    def test_no_risks(self):
        """Test clean diff with no risks."""
        diff = "+# Just a comment\n+print('hello')"
        file_stats = [{'filename': 'main.py', 'additions': 2, 'deletions': 0}]
        result = self.analyzer.analyze(diff, file_stats)
        self.assertEqual(result['score'], 100)

    def test_sensitive_file_detection(self):
        """Test detection of sensitive files."""
        file_stats = [
            {'filename': '.env', 'additions': 5, 'deletions': 0}
        ]
        result = self.analyzer.analyze("some diff", file_stats)
        self.assertLess(result['score'], 100)
        self.assertTrue(any('sensitive file' in i.lower() for i in result['issues']))

    def test_sensitive_extension_detection(self):
        """Test detection of sensitive file extensions."""
        file_stats = [
            {'filename': 'private.key', 'additions': 10, 'deletions': 0}
        ]
        result = self.analyzer.analyze("some diff", file_stats)
        self.assertLess(result['score'], 100)

    def test_binary_file_detection(self):
        """Test detection of binary files."""
        file_stats = [
            {'filename': 'image.png', 'additions': 100, 'deletions': 0},
            {'filename': 'app.exe', 'additions': 200, 'deletions': 0}
        ]
        result = self.analyzer.analyze("some diff", file_stats)
        self.assertLess(result['score'], 100)
        self.assertTrue(any('binary' in w.lower() for w in result['warnings']))

    def test_api_key_detection(self):
        """Test detection of API keys."""
        diff = "+API_KEY = 'sk_test_abcdefghijklmnopqrstuvwxyz123456'"
        file_stats = [{'filename': 'config.py', 'additions': 1, 'deletions': 0}]
        result = self.analyzer.analyze(diff, file_stats)
        self.assertLess(result['score'], 100)
        self.assertTrue(any('api key' in i.lower() for i in result['issues']))

    def test_password_detection(self):
        """Test detection of passwords."""
        diff = '+password = "MySecretPass123"'
        file_stats = [{'filename': 'config.py', 'additions': 1, 'deletions': 0}]
        result = self.analyzer.analyze(diff, file_stats)
        self.assertLess(result['score'], 100)
        self.assertTrue(any('password' in i.lower() for i in result['issues']))

    def test_private_key_detection(self):
        """Test detection of private keys."""
        diff = "+-----BEGIN RSA PRIVATE KEY-----\n+MIIEpAIBAAKC"
        file_stats = [{'filename': 'key.pem', 'additions': 2, 'deletions': 0}]
        result = self.analyzer.analyze(diff, file_stats)
        self.assertLess(result['score'], 100)
        self.assertTrue(any('private key' in i.lower() for i in result['issues']))

    def test_aws_credentials_detection(self):
        """Test detection of AWS credentials."""
        diff = "+aws_access_key_id = AKIAIOSFODNN7EXAMPLE"
        file_stats = [{'filename': 'credentials', 'additions': 1, 'deletions': 0}]
        result = self.analyzer.analyze(diff, file_stats)
        self.assertLess(result['score'], 100)

    def test_only_checks_added_lines(self):
        """Test that only added lines are checked for secrets."""
        # Removed line with secret should not trigger
        diff = "-API_KEY = 'sk_test_abcdefghijklmnopqrstuvwxyz123456'\n+# removed the key"
        file_stats = [{'filename': 'config.py', 'additions': 1, 'deletions': 1}]
        result = self.analyzer.analyze(diff, file_stats)
        # Should have high score since we're removing the secret
        self.assertGreater(result['score'], 90)


if __name__ == '__main__':
    unittest.main()
