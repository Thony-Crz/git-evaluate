"""Risk analyzer for detecting sensitive files, secrets, and binaries."""

import re
from typing import Dict, List, Set
import os


class RiskAnalyzer:
    """Analyzes changes for potential risks."""

    # Patterns for detecting secrets
    SECRET_PATTERNS = [
        (r'["\']?api[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{20,}["\']?', 'API key'),
        (r'["\']?secret[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{20,}["\']?', 'Secret key'),
        (r'["\']?password["\']?\s*[:=]\s*["\'][^"\']{8,}["\']', 'Password'),
        (r'["\']?token["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{20,}["\']?', 'Token'),
        (r'-----BEGIN (RSA |DSA )?PRIVATE KEY-----', 'Private key'),
        (r'aws_access_key_id\s*=\s*[A-Z0-9]{20}', 'AWS access key'),
        (r'aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}', 'AWS secret key'),
        (r'Bearer [A-Za-z0-9\-._~+/]+', 'Bearer token'),
    ]

    # Sensitive file patterns
    SENSITIVE_FILES = {
        '.env', '.env.local', '.env.production', '.env.development',
        'credentials.json', 'secrets.json', 'secret.yaml', 'secrets.yaml',
        '.aws/credentials', '.ssh/id_rsa', '.ssh/id_dsa', '.ssh/id_ecdsa',
        'id_rsa', 'id_dsa', 'id_ecdsa',
        '.npmrc', '.pypirc', '.dockercfg', '.docker/config.json'
    }

    # Sensitive file extensions
    SENSITIVE_EXTENSIONS = {
        '.pem', '.key', '.p12', '.pfx', '.keystore', '.jks'
    }

    # Binary file extensions
    BINARY_EXTENSIONS = {
        '.exe', '.dll', '.so', '.dylib', '.bin', '.dat',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.zip', '.tar', '.gz', '.7z', '.rar',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
        '.mp3', '.mp4', '.avi', '.mov', '.wav',
        '.class', '.jar', '.war', '.ear',
        '.pyc', '.pyo', '.o', '.a'
    }

    def __init__(self):
        self.max_score = 100
        self.issues = []
        self.warnings = []
        self.suggestions = []

    def analyze(self, diff_text: str, file_stats: List[Dict]) -> Dict:
        """
        Analyze changes for potential risks.
        
        Args:
            diff_text: The git diff text
            file_stats: List of file statistics
            
        Returns:
            Dictionary with score, issues, warnings, and suggestions
        """
        score = self.max_score
        self.issues = []
        self.warnings = []
        self.suggestions = []

        if not diff_text or not file_stats:
            return {
                'score': 100,
                'max_score': self.max_score,
                'issues': [],
                'warnings': [],
                'suggestions': []
            }

        # Check for sensitive files
        score -= self._check_sensitive_files(file_stats)
        
        # Check for binary files
        score -= self._check_binary_files(file_stats)
        
        # Check for secrets in diff
        score -= self._check_secrets(diff_text)

        return {
            'score': max(0, score),
            'max_score': self.max_score,
            'issues': self.issues,
            'warnings': self.warnings,
            'suggestions': self.suggestions
        }

    def _check_sensitive_files(self, file_stats: List[Dict]) -> int:
        """Check for sensitive files in the changeset."""
        penalty = 0
        
        for file_stat in file_stats:
            filename = file_stat.get('filename', '')
            basename = os.path.basename(filename)
            
            # Check against sensitive filenames
            if basename in self.SENSITIVE_FILES or filename in self.SENSITIVE_FILES:
                self.issues.append(f"Sensitive file detected: {filename}")
                self.suggestions.append(f"Avoid committing sensitive files like {filename}. Add to .gitignore")
                penalty += 30
                continue
            
            # Check against sensitive extensions
            _, ext = os.path.splitext(filename)
            if ext in self.SENSITIVE_EXTENSIONS:
                self.warnings.append(f"Potentially sensitive file type: {filename}")
                self.suggestions.append(f"Review {filename} to ensure no secrets are included")
                penalty += 15

        return min(penalty, 50)  # Cap at 50 points

    def _check_binary_files(self, file_stats: List[Dict]) -> int:
        """Check for binary files in the changeset."""
        penalty = 0
        
        for file_stat in file_stats:
            filename = file_stat.get('filename', '')
            _, ext = os.path.splitext(filename)
            
            if ext.lower() in self.BINARY_EXTENSIONS:
                self.warnings.append(f"Binary file detected: {filename}")
                self.suggestions.append(f"Consider storing large binaries outside of git (use Git LFS if needed)")
                penalty += 5

        return min(penalty, 20)  # Cap at 20 points

    def _check_secrets(self, diff_text: str) -> int:
        """Check for potential secrets in the diff."""
        penalty = 0
        secrets_found = set()
        
        # Only check added lines (lines starting with +)
        for line in diff_text.split('\n'):
            if not line.startswith('+') or line.startswith('+++'):
                continue
                
            # Remove the + prefix
            content = line[1:]
            
            # Check each secret pattern
            for pattern, name in self.SECRET_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    if name not in secrets_found:
                        self.issues.append(f"Potential secret detected: {name}")
                        self.suggestions.append(f"Remove hardcoded {name} and use environment variables instead")
                        secrets_found.add(name)
                        penalty += 25

        return min(penalty, 75)  # Cap at 75 points

    def _check_diff_size_risk(self, file_stats: List[Dict]) -> int:
        """Large diffs increase risk due to harder review."""
        penalty = 0
        
        total_changes = sum(f.get('additions', 0) + f.get('deletions', 0) for f in file_stats)
        num_files = len(file_stats)
        
        # Large diffs are harder to review, increasing risk of missed issues
        if total_changes > 500:
            self.warnings.append(f"Large diff increases review risk ({total_changes} lines)")
            self.suggestions.append("Large changes are harder to audit for security issues")
            penalty = 15
        elif total_changes > 300:
            self.warnings.append(f"Moderately large diff affects review quality ({total_changes} lines)")
            penalty = 8
        
        # Many files also increase review complexity
        if num_files > 10:
            self.warnings.append(f"Many files increase risk of oversight ({num_files} files)")
            penalty += 10
        elif num_files > 5:
            penalty += 5
        
        return min(penalty, 20)  # Cap at 20 points

    def _check_diff_size_risk(self, file_stats: List[Dict]) -> int:
        """Large diffs increase risk due to harder review."""
        penalty = 0
        
        total_changes = sum(f.get('additions', 0) + f.get('deletions', 0) for f in file_stats)
        num_files = len(file_stats)
        
        # Large diffs are harder to review, increasing risk of missed issues
        if total_changes > 500:
            self.warnings.append(f"Large diff increases review risk ({total_changes} lines)")
            self.suggestions.append("Large changes are harder to audit for security issues")
            penalty = 15
        elif total_changes > 300:
            self.warnings.append(f"Moderately large diff affects review quality ({total_changes} lines)")
            penalty = 8
        
        # Many files also increase review complexity
        if num_files > 10:
            self.warnings.append(f"Many files increase risk of oversight ({num_files} files)")
            penalty += 10
        elif num_files > 5:
            penalty += 5
        
        return min(penalty, 20)  # Cap at 20 points
