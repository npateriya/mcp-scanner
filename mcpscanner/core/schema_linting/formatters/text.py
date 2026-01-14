# Copyright 2025 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Text formatter for MCP Schema Linting results."""

from ..linter import LintResult
from ..rule_base import Severity


class TextFormatter:
    """Formats linting results as human-readable text output.
    
    Supports both summary and detailed output modes, with colored
    output for terminals that support it.
    """
    
    # ANSI color codes
    COLORS = {
        Severity.ERROR: "\033[91m",   # Red
        Severity.WARN: "\033[93m",    # Yellow
        Severity.INFO: "\033[94m",    # Blue
        Severity.HINT: "\033[90m",    # Gray
        "reset": "\033[0m",
        "bold": "\033[1m",
    }
    
    def __init__(self, use_color: bool = True):
        """Initialize formatter.
        
        Args:
            use_color: Whether to use ANSI color codes in output
        """
        self.use_color = use_color
    
    def format(self, result: LintResult, verbose: bool = False) -> str:
        """Format a single LintResult as text.
        
        Args:
            result: The linting result to format
            verbose: Whether to include detailed information
            
        Returns:
            Formatted text string
        """
        lines = []
        
        # Header
        if result.source:
            lines.append(f"\n{self._bold('📋 Linting:')} {result.source}")
        else:
            lines.append(f"\n{self._bold('📋 Linting Results')}")
        
        lines.append("-" * 50)
        
        # Show config warnings first (P0: Spectral-like behavior)
        if result.config_warnings:
            for warning in result.config_warnings:
                lines.append(f"  {self._colorize('[CONFIG WARNING]', Severity.WARN)} {warning}")
            lines.append("")
        
        # Show infrastructure errors (P1: Separate from findings)
        if result.errors:
            for error in result.errors:
                lines.append(f"  {self._colorize('[ERROR]', Severity.ERROR)} {error}")
            lines.append("")
        
        # Show findings grouped by severity
        if result.findings:
            for finding in sorted(result.findings, key=lambda f: self._severity_order(f.severity)):
                severity_str = self._colorize(f"[{finding.severity.value.upper()}]", finding.severity)
                lines.append(f"  {severity_str} {finding.rule_id}")
                lines.append(f"      {finding.message}")
                if finding.path:
                    lines.append(f"      at: {finding.path}")
                if verbose and finding.suggestion:
                    lines.append(f"      💡 {finding.suggestion}")
                lines.append("")
        elif not result.errors:
            lines.append(f"  {self._colorize('✅ No issues found!', Severity.INFO)}")
        
        # Summary
        lines.append("-" * 50)
        summary_parts = []
        if result.errors:
            summary_parts.append(self._colorize(f"{len(result.errors)} errors", Severity.ERROR))
        if result.error_count:
            summary_parts.append(self._colorize(f"{result.error_count} errors", Severity.ERROR))
        if result.warning_count:
            summary_parts.append(self._colorize(f"{result.warning_count} warnings", Severity.WARN))
        if result.info_count:
            summary_parts.append(self._colorize(f"{result.info_count} info", Severity.INFO))
        if result.hint_count:
            summary_parts.append(f"{result.hint_count} hints")
        
        if summary_parts:
            lines.append(f"  Summary: {', '.join(summary_parts)}")
        else:
            lines.append(f"  Summary: {self._colorize('All checks passed!', Severity.INFO)}")
        
        lines.append("")
        
        return "\n".join(lines)
    
    def format_multiple(self, results: list[LintResult], verbose: bool = False) -> str:
        """Format multiple LintResults.
        
        Args:
            results: List of linting results
            verbose: Whether to include detailed information
            
        Returns:
            Formatted text string
        """
        parts = [self.format(r, verbose) for r in results]
        
        # Add overall summary
        total_errors = sum(r.error_count for r in results)
        total_warnings = sum(r.warning_count for r in results)
        total_info = sum(r.info_count for r in results)
        
        summary = [
            "",
            "=" * 50,
            self._bold("📊 Overall Summary"),
            f"  Files checked: {len(results)}",
        ]
        
        if total_errors or total_warnings or total_info:
            summary.append(f"  Total issues: {total_errors + total_warnings + total_info}")
            if total_errors:
                summary.append(f"    • {self._colorize(f'{total_errors} errors', Severity.ERROR)}")
            if total_warnings:
                summary.append(f"    • {self._colorize(f'{total_warnings} warnings', Severity.WARN)}")
            if total_info:
                summary.append(f"    • {self._colorize(f'{total_info} info', Severity.INFO)}")
        else:
            summary.append(f"  {self._colorize('✅ All files passed!', Severity.INFO)}")
        
        summary.append("")
        
        parts.append("\n".join(summary))
        
        return "\n".join(parts)
    
    def _colorize(self, text: str, severity: Severity) -> str:
        """Apply color to text based on severity."""
        if not self.use_color:
            return text
        color = self.COLORS.get(severity, "")
        reset = self.COLORS["reset"]
        return f"{color}{text}{reset}"
    
    def _bold(self, text: str) -> str:
        """Apply bold formatting to text."""
        if not self.use_color:
            return text
        return f"{self.COLORS['bold']}{text}{self.COLORS['reset']}"
    
    def _severity_order(self, severity: Severity) -> int:
        """Get sort order for severity (errors first)."""
        order = {
            Severity.ERROR: 0,
            Severity.WARN: 1,
            Severity.INFO: 2,
            Severity.HINT: 3,
            Severity.OFF: 4,
        }
        return order.get(severity, 5)

