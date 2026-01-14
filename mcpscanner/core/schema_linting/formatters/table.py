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

"""Table formatter for MCP Schema Linting results.

Inspired by Cisco api-insights-cli output format. Groups findings by rule
and shows affected items count, with optional verbose mode showing each
occurrence with line numbers.
"""

import textwrap
from collections import defaultdict
from dataclasses import dataclass
from ..linter import LintResult
from ..rule_base import Finding, Severity


@dataclass
class GroupedFinding:
    """A group of findings for the same rule."""
    rule_id: str
    severity: Severity
    message: str
    suggestion: str | None
    occurrences: list[Finding]
    
    @property
    def count(self) -> int:
        return len(self.occurrences)


class TableFormatter:
    """Formats linting results as grouped tables, similar to api-insights-cli.
    
    Default mode shows one row per rule with affected items count.
    Verbose mode expands to show each occurrence with line:col and path.
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
    
    # Column widths for the table
    COL_NUM = 3
    COL_SEVERITY = 8
    COL_CODE = 35
    COL_FINDINGS = 30
    COL_RECOMMENDATION = 45
    COL_AFFECTED = 8
    
    # Categories for grouping
    CATEGORIES = {
        "tool": "Tool Quality",
        "prompt": "Prompt Quality",
        "resource": "Resource Quality",
        "general": "General Quality",
    }
    
    def __init__(self, use_color: bool = True):
        """Initialize formatter.
        
        Args:
            use_color: Whether to use ANSI color codes in output
        """
        self.use_color = use_color
    
    def format(self, result: LintResult, verbose: bool = False) -> str:
        """Format a single LintResult as a grouped table.
        
        Args:
            result: The linting result to format
            verbose: Whether to show each occurrence with line numbers
            
        Returns:
            Formatted table string
        """
        lines = []
        
        # Show config warnings first (P0: Spectral-like behavior)
        if result.config_warnings:
            lines.append(self._bold("\n⚠️  Configuration Warnings"))
            for warning in result.config_warnings:
                lines.append(f"  {self._colorize(warning, Severity.WARN)}")
            lines.append("")
        
        # Show infrastructure errors (P1: Separate from findings)
        if result.errors:
            lines.append(self._bold("\n❌ Errors"))
            for error in result.errors:
                lines.append(f"  {self._colorize(error, Severity.ERROR)}")
            lines.append("")
            # If only errors and no findings, return early
            if not result.findings:
                return "\n".join(lines)
        
        if not result.findings:
            return "\n".join(lines) + self._format_empty(result)
        
        # Group findings by category, then by rule
        by_category = self._group_by_category(result.findings)
        
        # Format each category (append to existing lines for warnings/errors)
        for category, category_name in self.CATEGORIES.items():
            if category not in by_category:
                continue
            
            grouped = by_category[category]
            lines.append(self._format_category(category_name, grouped, verbose))
        
        return "\n".join(lines)
    
    def format_multiple(self, results: list[LintResult], verbose: bool = False) -> str:
        """Format multiple LintResults.
        
        Args:
            results: List of linting results
            verbose: Whether to show detailed information
            
        Returns:
            Formatted table string
        """
        # Combine all findings, errors, and config warnings
        all_findings = []
        all_errors = []
        all_config_warnings = []
        sources = []
        
        for r in results:
            all_findings.extend(r.findings)
            all_errors.extend(r.errors)
            all_config_warnings.extend(r.config_warnings)
            if r.source:
                sources.append(r.source)
        
        # Create combined result
        combined = LintResult(
            source=", ".join(sources) if sources else "",
            findings=all_findings,
            errors=all_errors,
            config_warnings=all_config_warnings,
        )
        
        output = self.format(combined, verbose)
        
        # Add summary table
        output += self._format_summary_table(results)
        
        return output
    
    def _group_by_category(self, findings: list[Finding]) -> dict[str, list[GroupedFinding]]:
        """Group findings by category and then by rule_id."""
        # First, group by rule_id
        by_rule: dict[str, list[Finding]] = defaultdict(list)
        for f in findings:
            by_rule[f.rule_id].append(f)
        
        # Then organize by category
        by_category: dict[str, list[GroupedFinding]] = defaultdict(list)
        
        for rule_id, occurrences in by_rule.items():
            first = occurrences[0]
            
            # Determine category from rule_id prefix
            category = "general"
            for cat in ["tool", "prompt", "resource"]:
                if rule_id.startswith(cat):
                    category = cat
                    break
            
            grouped = GroupedFinding(
                rule_id=rule_id,
                severity=first.severity,
                message=first.message,
                suggestion=first.suggestion,
                occurrences=occurrences,
            )
            by_category[category].append(grouped)
        
        # Sort each category by severity (errors first)
        for cat in by_category:
            by_category[cat].sort(key=lambda g: self._severity_order(g.severity))
        
        return by_category
    
    def _format_category(self, name: str, grouped: list[GroupedFinding], verbose: bool) -> str:
        """Format a single category section."""
        lines = []
        
        # Category header
        lines.append(f"\n{self._bold(name)}")
        
        # Table header
        header = self._format_header()
        lines.append(header)
        
        # Count findings by severity
        error_count = sum(1 for g in grouped if g.severity == Severity.ERROR)
        warn_count = sum(1 for g in grouped if g.severity == Severity.WARN)
        info_count = sum(1 for g in grouped if g.severity == Severity.INFO)
        hint_count = sum(1 for g in grouped if g.severity == Severity.HINT)
        
        # Format each grouped finding
        for i, g in enumerate(grouped, 1):
            lines.append(self._format_grouped_finding(i, g, verbose))
        
        # Category summary
        summary_parts = []
        total = len(grouped)
        summary_parts.append(f"{total} Finding{'s' if total != 1 else ''}")
        summary_parts.append(f"({error_count} Error, {warn_count} Warning, {info_count} Info, {hint_count} Hint)")
        lines.append(" ".join(summary_parts))
        
        return "\n".join(lines)
    
    def _format_header(self) -> str:
        """Format the table header row."""
        parts = [
            "#".rjust(self.COL_NUM),
            "SEVERITY".ljust(self.COL_SEVERITY),
            "CODE".ljust(self.COL_CODE),
            "FINDINGS".ljust(self.COL_FINDINGS),
            "RECOMMENDATION".ljust(self.COL_RECOMMENDATION),
            "AFFECTED ITEMS".rjust(self.COL_AFFECTED),
        ]
        return "  " + "  ".join(parts)
    
    def _format_grouped_finding(self, num: int, g: GroupedFinding, verbose: bool) -> str:
        """Format a single grouped finding row."""
        lines = []
        
        # Severity with color
        severity_str = self._colorize(g.severity.value, g.severity)
        
        # Wrap long text
        message_lines = textwrap.wrap(g.message, width=self.COL_FINDINGS)
        suggestion_lines = textwrap.wrap(g.suggestion or "", width=self.COL_RECOMMENDATION) if g.suggestion else [""]
        
        # First row
        first_msg = message_lines[0] if message_lines else ""
        first_sug = suggestion_lines[0] if suggestion_lines else ""
        
        row = "  " + "  ".join([
            str(num).rjust(self.COL_NUM),
            severity_str.ljust(self.COL_SEVERITY + (len(severity_str) - len(g.severity.value))),  # Adjust for color codes
            g.rule_id.ljust(self.COL_CODE),
            first_msg.ljust(self.COL_FINDINGS),
            first_sug.ljust(self.COL_RECOMMENDATION),
            str(g.count).rjust(self.COL_AFFECTED),
        ])
        lines.append(row)
        
        # Additional message/suggestion lines
        max_extra_lines = max(len(message_lines) - 1, len(suggestion_lines) - 1)
        for i in range(max_extra_lines):
            msg = message_lines[i + 1] if i + 1 < len(message_lines) else ""
            sug = suggestion_lines[i + 1] if i + 1 < len(suggestion_lines) else ""
            
            continuation = "  " + "  ".join([
                " " * self.COL_NUM,
                " " * self.COL_SEVERITY,
                " " * self.COL_CODE,
                msg.ljust(self.COL_FINDINGS),
                sug.ljust(self.COL_RECOMMENDATION),
                " " * self.COL_AFFECTED,
            ])
            lines.append(continuation)
        
        # Verbose mode: show each occurrence with line:col and path
        if verbose:
            for occ in g.occurrences:
                line_col = f"{occ.line or ''}:{occ.column or ''}" if occ.line else ""
                path_str = occ.path or ""
                
                # Format: indented line:col followed by path
                occurrence_line = "  " + "  ".join([
                    " " * self.COL_NUM,
                    " " * self.COL_SEVERITY,
                    line_col.ljust(self.COL_CODE) if line_col else " " * self.COL_CODE,
                    path_str[:self.COL_FINDINGS + self.COL_RECOMMENDATION],
                ])
                lines.append(occurrence_line.rstrip())
        
        return "\n".join(lines)
    
    def _format_empty(self, result: LintResult) -> str:
        """Format output when no issues found."""
        source = result.source or "input"
        return f"\n{self._colorize('✅', Severity.INFO)} {source}: No issues found!\n"
    
    def _format_summary_table(self, results: list[LintResult]) -> str:
        """Format the final summary table."""
        lines = []
        lines.append("")
        lines.append("  # |   CATEGORY   | ERROR | WARNING | INFO | HINT")
        lines.append("----+--------------+-------+---------+------+------")
        
        # Aggregate by category
        cat_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"error": 0, "warn": 0, "info": 0, "hint": 0})
        
        # Track unique rules that triggered findings
        rules_with_findings: set[str] = set()
        total_findings = 0
        
        for r in results:
            for f in r.findings:
                total_findings += 1
                rules_with_findings.add(f.rule_id)
                
                # Determine category
                category = "General"
                for cat_prefix, cat_name in [("tool", "Tool"), ("prompt", "Prompt"), ("resource", "Resource")]:
                    if f.rule_id.startswith(cat_prefix):
                        category = cat_name
                        break
                
                if f.severity == Severity.ERROR:
                    cat_stats[category]["error"] += 1
                elif f.severity == Severity.WARN:
                    cat_stats[category]["warn"] += 1
                elif f.severity == Severity.INFO:
                    cat_stats[category]["info"] += 1
                elif f.severity == Severity.HINT:
                    cat_stats[category]["hint"] += 1
        
        for i, (cat, stats) in enumerate(sorted(cat_stats.items()), 1):
            lines.append(
                f"  {i} | {cat.ljust(12)} | {str(stats['error']).rjust(5)} | "
                f"{str(stats['warn']).rjust(7)} | {str(stats['info']).rjust(4)} | {str(stats['hint']).rjust(4)}"
            )
        
        # Overall summary
        lines.append("")
        lines.append("=" * 60)
        
        # Aggregate scan stats
        total_tools = sum(r.stats.tools for r in results)
        total_prompts = sum(r.stats.prompts for r in results)
        total_resources = sum(r.stats.resources for r in results)
        
        # Get total rules from registry
        try:
            from ..rules.registry import get_default_registry
            registry = get_default_registry()
            total_rules = len(registry)
        except Exception:
            total_rules = 37  # Fallback
        
        rules_passed = total_rules - len(rules_with_findings)
        
        lines.append(self._bold("📊 Summary"))
        
        # Show scan stats if any items were found
        scanned_parts = []
        if total_tools:
            scanned_parts.append(f"{total_tools} tool{'s' if total_tools != 1 else ''}")
        if total_prompts:
            scanned_parts.append(f"{total_prompts} prompt{'s' if total_prompts != 1 else ''}")
        if total_resources:
            scanned_parts.append(f"{total_resources} resource{'s' if total_resources != 1 else ''}")
        
        if scanned_parts:
            lines.append(f"  Scanned:       {', '.join(scanned_parts)}")
        
        lines.append(f"  Rules checked: {total_rules}")
        lines.append(f"  Rules passed:  {self._colorize(str(rules_passed), Severity.INFO)} ({rules_passed * 100 // total_rules}%)")
        lines.append(f"  Rules failed:  {len(rules_with_findings)}")
        lines.append(f"  Total issues:  {total_findings}")
        
        # Totals row
        total_errors = sum(s["error"] for s in cat_stats.values())
        total_warns = sum(s["warn"] for s in cat_stats.values())
        total_info = sum(s["info"] for s in cat_stats.values())
        total_hints = sum(s["hint"] for s in cat_stats.values())
        
        if total_errors:
            lines.append(f"    • {self._colorize(f'{total_errors} errors', Severity.ERROR)}")
        if total_warns:
            lines.append(f"    • {self._colorize(f'{total_warns} warnings', Severity.WARN)}")
        if total_info:
            lines.append(f"    • {self._colorize(f'{total_info} info', Severity.INFO)}")
        if total_hints:
            lines.append(f"    • {total_hints} hints")
        
        lines.append("")
        return "\n".join(lines)
    
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

