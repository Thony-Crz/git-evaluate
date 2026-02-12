"""Message quality analyzer for commit messages."""

import re
from typing import Dict, List, Tuple


class MessageAnalyzer:
    """Analyzes commit message quality based on conventions and clarity."""

    # Conventional commit types
    CONVENTIONAL_TYPES = {
        'feat', 'fix', 'docs', 'style', 'refactor', 
        'perf', 'test', 'build', 'ci', 'chore', 'revert'
    }

    def __init__(self):
        self.max_score = 100
        self.issues = []
        self.warnings = []
        self.suggestions = []

    def analyze(self, message: str) -> Dict:
        """
        Analyze commit message quality.
        
        Args:
            message: The commit message to analyze
            
        Returns:
            Dictionary with score, issues, warnings, and suggestions
        """
        if not message or not message.strip():
            return {
                'score': 0,
                'max_score': self.max_score,
                'issues': ['Empty commit message'],
                'warnings': [],
                'suggestions': ['Provide a meaningful commit message']
            }

        score = self.max_score
        self.issues = []
        self.warnings = []
        self.suggestions = []

        lines = message.strip().split('\n')
        subject = lines[0] if lines else ""
        body = '\n'.join(lines[2:]) if len(lines) > 2 else ""

        # Check subject line
        score -= self._check_subject_length(subject)
        score -= self._check_subject_format(subject)
        score -= self._check_conventional_format(subject)
        score -= self._check_capitalization(subject)
        score -= self._check_period_ending(subject)
        
        # Check body
        if len(lines) > 1:
            score -= self._check_blank_line_after_subject(lines)
            score -= self._check_body_line_length(body)

        return {
            'score': max(0, score),
            'max_score': self.max_score,
            'issues': self.issues,
            'warnings': self.warnings,
            'suggestions': self.suggestions
        }

    def _check_subject_length(self, subject: str) -> int:
        """Check if subject line length is appropriate."""
        length = len(subject)
        penalty = 0
        
        if length == 0:
            self.issues.append("Subject line is empty")
            penalty = 20
        elif length < 10:
            self.warnings.append(f"Subject line is very short ({length} chars)")
            self.suggestions.append("Consider providing more context in the subject")
            penalty = 10
        elif length > 72:
            self.issues.append(f"Subject line is too long ({length} chars, max 72)")
            self.suggestions.append("Keep subject line under 72 characters")
            penalty = 15
        elif length > 50:
            self.warnings.append(f"Subject line is longer than recommended ({length} chars, ideally ≤50)")
            penalty = 5
            
        return penalty

    def _check_subject_format(self, subject: str) -> int:
        """Check basic subject format."""
        penalty = 0
        
        if subject.startswith(' ') or subject.endswith(' '):
            self.warnings.append("Subject has leading or trailing whitespace")
            penalty = 5
            
        return penalty

    def _check_conventional_format(self, subject: str) -> int:
        """Check if message follows conventional commit format."""
        penalty = 0
        
        # Pattern: type(scope): description or type: description
        pattern = r'^([a-z]+)(\([a-z0-9-]+\))?: .+'
        match = re.match(pattern, subject.lower())
        
        if match:
            commit_type = match.group(1)
            if commit_type not in self.CONVENTIONAL_TYPES:
                self.warnings.append(f"Unknown conventional commit type: '{commit_type}'")
                self.suggestions.append(f"Use one of: {', '.join(sorted(self.CONVENTIONAL_TYPES))}")
                penalty = 5
        else:
            self.warnings.append("Message doesn't follow conventional commit format")
            self.suggestions.append("Consider using format: type(scope): description (e.g., 'feat: add new feature')")
            penalty = 10
            
        return penalty

    def _check_capitalization(self, subject: str) -> int:
        """Check if subject starts with capital letter (after type:)."""
        penalty = 0
        
        # Skip conventional commit prefix
        desc_start = subject.find(': ')
        if desc_start != -1:
            desc = subject[desc_start + 2:]
        else:
            desc = subject
            
        if desc and desc[0].islower():
            self.warnings.append("Subject description should start with capital letter")
            penalty = 5
            
        return penalty

    def _check_period_ending(self, subject: str) -> int:
        """Check if subject ends with a period."""
        penalty = 0
        
        if subject.endswith('.'):
            self.warnings.append("Subject should not end with a period")
            penalty = 5
            
        return penalty

    def _check_blank_line_after_subject(self, lines: List[str]) -> int:
        """Check if there's a blank line after subject."""
        penalty = 0
        
        if len(lines) > 1 and lines[1].strip() != "":
            self.warnings.append("Missing blank line after subject")
            self.suggestions.append("Add a blank line between subject and body")
            penalty = 5
            
        return penalty

    def _check_body_line_length(self, body: str) -> int:
        """Check body line length."""
        penalty = 0
        
        if body:
            for i, line in enumerate(body.split('\n'), start=3):
                if len(line) > 72:
                    self.warnings.append(f"Line {i} in body exceeds 72 characters")
                    penalty = min(penalty + 2, 10)  # Cap at 10 points
                    break
                    
        return penalty
