"""Diff analyzer for staging changes."""

from typing import Dict, List
import re


class DiffAnalyzer:
    """Analyzes diff size and coherence."""

    def __init__(self):
        self.max_score = 100
        self.issues = []
        self.warnings = []
        self.suggestions = []

    def analyze(self, diff_text: str, file_stats: List[Dict]) -> Dict:
        """
        Analyze diff size and coherence.
        
        Args:
            diff_text: The git diff text
            file_stats: List of file statistics (additions, deletions, filename)
            
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
                'warnings': ['No changes in staging area'],
                'suggestions': ['Stage some changes before running evaluation']
            }

        # Calculate total changes
        total_additions = sum(f.get('additions', 0) for f in file_stats)
        total_deletions = sum(f.get('deletions', 0) for f in file_stats)
        total_changes = total_additions + total_deletions
        num_files = len(file_stats)

        # Check diff size
        score -= self._check_diff_size(total_changes, num_files)
        score -= self._check_file_count(num_files)
        score -= self._check_large_files(file_stats)
        score -= self._check_coherence(file_stats)

        return {
            'score': max(0, score),
            'max_score': self.max_score,
            'issues': self.issues,
            'warnings': self.warnings,
            'suggestions': self.suggestions,
            'stats': {
                'files_changed': num_files,
                'additions': total_additions,
                'deletions': total_deletions,
                'total_changes': total_changes
            }
        }

    def _check_diff_size(self, total_changes: int, num_files: int) -> int:
        """Check if diff size is reasonable (Clean Code: atomic commits)."""
        penalty = 0

        if total_changes == 0:
            self.warnings.append("No line changes detected")
            return 0

        # Clean Code recommends small, atomic commits
        if total_changes > 500:
            self.issues.append(f"Very large diff: {total_changes} lines changed")
            self.suggestions.append("Split into multiple atomic commits (recommended: <200 lines)")
            penalty = 30
        elif total_changes > 300:
            self.issues.append(f"Large diff: {total_changes} lines changed")
            self.suggestions.append("Large commits are hard to review. Consider splitting (recommended: <200 lines)")
            penalty = 20
        elif total_changes > 200:
            self.warnings.append(f"Moderately large diff: {total_changes} lines changed")
            self.suggestions.append("Consider smaller, focused commits for easier review")
            penalty = 12
        elif total_changes > 100:
            self.warnings.append(f"Significant diff: {total_changes} lines changed")
            penalty = 5

        return penalty

    def _check_file_count(self, num_files: int) -> int:
        """Check if number of files is reasonable (atomic commits)."""
        penalty = 0

        # Atomic commits should focus on one thing
        if num_files > 10:
            self.issues.append(f"Too many files changed: {num_files} files")
            self.suggestions.append("Split into atomic commits (recommended: 1-5 files per commit)")
            penalty = 25
        elif num_files > 5:
            self.warnings.append(f"Many files changed: {num_files} files")
            self.suggestions.append("Consider splitting into smaller, focused commits")
            penalty = 15
        elif num_files > 3:
            self.warnings.append(f"Several files changed: {num_files} files")
            penalty = 8

        return penalty

    def _check_large_files(self, file_stats: List[Dict]) -> int:
        """Check for individual files with large changes."""
        penalty = 0

        for file_stat in file_stats:
            filename = file_stat.get('filename', 'unknown')
            changes = file_stat.get('additions', 0) + file_stat.get('deletions', 0)
            
            if changes > 300:
                self.issues.append(f"Very large changes in single file: {filename} ({changes} lines)")
                self.suggestions.append(f"Refactor {filename} changes into smaller commits")
                penalty = min(penalty + 10, 25)
            elif changes > 150:
                self.warnings.append(f"Large changes in single file: {filename} ({changes} lines)")
                penalty = min(penalty + 5, 15)

        return penalty

    def _check_coherence(self, file_stats: List[Dict]) -> int:
        """Check if changes are coherent (related files)."""
        penalty = 0

        # Group files by directory and extension
        directories = set()
        extensions = set()
        
        for file_stat in file_stats:
            filename = file_stat.get('filename', '')
            if '/' in filename:
                directories.add(filename.rsplit('/', 1)[0])
            if '.' in filename:
                extensions.add(filename.rsplit('.', 1)[1])

        # If changes span too many directories or file types, it might lack coherence
        if len(directories) > 5:
            self.warnings.append(f"Changes span many directories ({len(directories)})")
            self.suggestions.append("Consider grouping related changes in separate commits")
            penalty = 10
        
        if len(extensions) > 5:
            self.warnings.append(f"Changes involve many file types ({len(extensions)})")
            penalty = 5

        return penalty
