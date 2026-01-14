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

"""Main linter orchestrator for MCP Schema validation.

This module provides the SchemaLinter class which:
- Loads and parses MCP definitions from various sources
- Applies configured rules to validate the definitions
- Aggregates and returns findings
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .rule_base import Finding, RuleConfig, Severity
from .rules.registry import get_default_registry, RuleRegistry
from .rules.dynamic_rule import parse_dynamic_rules, DynamicRule


@dataclass
class LintConfig:
    """Configuration for the schema linter.
    
    Attributes:
        rules: Per-rule configuration overrides
        extends: List of rulesets to extend (e.g., ["mcp:recommended"])
        ignore_patterns: Glob patterns for paths to ignore
        fail_on_error: Whether to treat errors as failures (for exit codes)
        fail_on_warn: Whether to treat warnings as failures
        raw_rules: Raw rule definitions from YAML (for dynamic rules)
        dynamic_rules: Parsed dynamic rules from config
    """
    rules: dict[str, RuleConfig | str | None] = field(default_factory=dict)
    extends: list[str] = field(default_factory=lambda: ["mcp:recommended"])
    ignore_patterns: list[str] = field(default_factory=list)
    fail_on_error: bool = True
    fail_on_warn: bool = False
    raw_rules: dict[str, Any] = field(default_factory=dict)  # For dynamic rule parsing
    dynamic_rules: list = field(default_factory=list)  # Parsed DynamicRule instances
    
    @classmethod
    def from_dict(cls, data: dict) -> "LintConfig":
        """Create config from dictionary (e.g., parsed YAML)."""
        raw_rules = data.get("rules", {})
        rules = {}
        
        for rule_id, rule_config in raw_rules.items():
            if isinstance(rule_config, (str, type(None))):
                rules[rule_id] = RuleConfig.from_dict(rule_config)
            elif isinstance(rule_config, dict):
                rules[rule_id] = RuleConfig.from_dict(rule_config)
            else:
                rules[rule_id] = RuleConfig()
        
        # Parse dynamic rules from config
        dynamic_rules = parse_dynamic_rules(raw_rules)
        
        return cls(
            rules=rules,
            extends=data.get("extends", ["mcp:recommended"]),
            ignore_patterns=data.get("ignore", []),
            fail_on_error=data.get("fail_on_error", True),
            fail_on_warn=data.get("fail_on_warn", False),
            raw_rules=raw_rules,
            dynamic_rules=dynamic_rules,
        )
    
    @classmethod
    def default(cls) -> "LintConfig":
        """Create default configuration with recommended rules."""
        return cls()


@dataclass
class LintResult:
    """Result of a linting operation.
    
    Attributes:
        findings: List of linting findings (rule violations)
        errors: List of infrastructure errors (connection, parse failures)
        source: Source identifier (file path, URL, etc.)
        config_warnings: Warnings about configuration issues
    """
    findings: list[Finding] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)  # P1: Separate infrastructure errors
    config_warnings: list[str] = field(default_factory=list)  # P0: Config validation warnings
    source: str = ""
    
    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.ERROR)
    
    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.WARN)
    
    @property
    def info_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.INFO)
    
    @property
    def hint_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.HINT)
    
    @property
    def has_errors(self) -> bool:
        return self.error_count > 0 or len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        return self.warning_count > 0
    
    def should_fail(self, config: "LintConfig") -> bool:
        """Determine if this result should cause a failure based on config."""
        if self.errors:  # Infrastructure errors always fail
            return True
        if config.fail_on_error and self.error_count > 0:
            return True
        if config.fail_on_warn and self.has_warnings:
            return True
        return False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        result = {
            "source": self.source,
            "findings": [f.to_dict() for f in self.findings],
            "summary": {
                "errors": self.error_count,
                "warnings": self.warning_count,
                "info": self.info_count,
                "hints": self.hint_count,
                "total": len(self.findings),
            },
        }
        if self.errors:
            result["infrastructure_errors"] = self.errors
        if self.config_warnings:
            result["config_warnings"] = self.config_warnings
        return result
    
    # P1: Factory methods for common error cases
    @classmethod
    def connection_error(cls, source: str, message: str) -> "LintResult":
        """Create a result for connection/network errors."""
        return cls(source=source, errors=[f"Connection error: {message}"])
    
    @classmethod
    def parse_error(cls, source: str, message: str, line: int | None = None) -> "LintResult":
        """Create a result for JSON/YAML parse errors."""
        error_msg = f"Parse error: {message}"
        if line:
            error_msg += f" (line {line})"
        return cls(source=source, errors=[error_msg])
    
    @classmethod
    def file_error(cls, source: str, message: str) -> "LintResult":
        """Create a result for file read errors."""
        return cls(source=source, errors=[f"File error: {message}"])


class SchemaLinter:
    """Main linter class for validating MCP schema definitions.
    
    Example usage:
        linter = SchemaLinter()
        
        # Lint a file
        result = linter.lint_file("tools.json")
        
        # Lint data directly
        result = linter.lint({"tools": [...]})
        
        # With custom config
        config = LintConfig(rules={"tool-name-casing": "error"})
        result = linter.lint_file("tools.json", config=config)
    """
    
    def __init__(self, registry: RuleRegistry | None = None):
        """Initialize the linter.
        
        Args:
            registry: Rule registry to use. Defaults to built-in registry.
        """
        self.registry = registry or get_default_registry()
    
    def lint(
        self,
        data: dict | list,
        config: LintConfig | None = None,
        source: str = "",
    ) -> LintResult:
        """Lint MCP definition data.
        
        Args:
            data: MCP definition data (dict with tools/prompts/resources or list of items)
            config: Linting configuration. Uses defaults if not provided.
            source: Source identifier for findings (e.g., filename)
            
        Returns:
            LintResult with all findings
        """
        config = config or LintConfig.default()
        result = LintResult(source=source)
        
        # P0: Validate config - warn about unknown rule IDs (Spectral-like behavior)
        result.config_warnings = self._validate_config(config)
        
        # Normalize data - handle both object and list formats
        if isinstance(data, list):
            # Try to detect item type from content
            normalized = self._normalize_list_data(data)
        else:
            normalized = data
        
        # Run all enabled built-in rules
        for rule in self.registry.get_all():
            rule_config = self._get_rule_config(rule.id, config)
            
            if not rule_config.enabled:
                continue
            
            try:
                findings = rule.check(normalized, rule_config, source)
                result.findings.extend(findings)
            except Exception as e:
                # Add an error for rule execution failures
                result.errors.append(f"Rule '{rule.id}' failed: {e}")
        
        # Run dynamic rules from config
        for dynamic_rule in config.dynamic_rules:
            rule_config = self._get_rule_config(dynamic_rule.id, config)
            
            if not rule_config.enabled:
                continue
            
            try:
                findings = dynamic_rule.check(normalized, rule_config, source)
                result.findings.extend(findings)
            except Exception as e:
                result.errors.append(f"Dynamic rule '{dynamic_rule.id}' failed: {e}")
        
        return result
    
    def _validate_config(self, config: LintConfig) -> list[str]:
        """Validate configuration and return warnings for issues.
        
        Checks for:
        - Unknown rule IDs in config (typos, deprecated rules)
        - Invalid severity values
        
        Returns:
            List of warning messages
        """
        warnings = []
        known_rule_ids = {rule.id for rule in self.registry.get_all()}
        
        # Dynamic rules are also known (they define themselves)
        dynamic_rule_ids = {rule.id for rule in config.dynamic_rules}
        all_known_ids = known_rule_ids | dynamic_rule_ids
        
        for rule_id in config.rules.keys():
            if rule_id not in all_known_ids:
                # Find similar rule IDs for suggestion
                similar = self._find_similar_rule_id(rule_id, known_rule_ids)
                if similar:
                    warnings.append(
                        f"Unknown rule '{rule_id}' in config. Did you mean '{similar}'?"
                    )
                else:
                    warnings.append(
                        f"Unknown rule '{rule_id}' in config. "
                        f"Use --list-rules to see available rules."
                    )
        
        return warnings
    
    def _find_similar_rule_id(self, rule_id: str, known_ids: set[str]) -> str | None:
        """Find a similar rule ID for typo suggestions."""
        # Simple similarity: check if any known ID contains the unknown one or vice versa
        rule_parts = rule_id.lower().replace("-", " ").replace("_", " ").split()
        
        best_match = None
        best_score = 0
        
        for known in known_ids:
            known_parts = known.lower().replace("-", " ").replace("_", " ").split()
            # Count matching parts
            score = sum(1 for p in rule_parts if p in known_parts)
            if score > best_score:
                best_score = score
                best_match = known
        
        # Only suggest if at least 2 parts match
        return best_match if best_score >= 2 else None
    
    def lint_file(
        self,
        file_path: str | Path,
        config: LintConfig | None = None,
    ) -> LintResult:
        """Lint an MCP definition file.
        
        Args:
            file_path: Path to JSON file containing MCP definitions
            config: Linting configuration
            
        Returns:
            LintResult with all findings
        """
        path = Path(file_path)
        
        if not path.exists():
            return LintResult.file_error(str(path), f"File not found: {path}")
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return LintResult.parse_error(str(path), str(e), line=e.lineno)
        except Exception as e:
            return LintResult.file_error(str(path), str(e))
        
        return self.lint(data, config, source=str(path))
    
    def lint_files(
        self,
        file_paths: list[str | Path],
        config: LintConfig | None = None,
    ) -> list[LintResult]:
        """Lint multiple MCP definition files.
        
        Args:
            file_paths: List of paths to JSON files
            config: Linting configuration (shared across all files)
            
        Returns:
            List of LintResult, one per file
        """
        return [self.lint_file(path, config) for path in file_paths]
    
    def _get_rule_config(self, rule_id: str, config: LintConfig) -> RuleConfig:
        """Get effective configuration for a rule."""
        # Check for explicit config
        if rule_id in config.rules:
            rule_config = config.rules[rule_id]
            if isinstance(rule_config, RuleConfig):
                return rule_config
            return RuleConfig.from_dict(rule_config)
        
        # Use rule's default
        rule = self.registry.get(rule_id)
        if rule:
            return RuleConfig(severity=rule.default_severity)
        
        return RuleConfig()
    
    def _normalize_list_data(self, data: list) -> dict:
        """Normalize a list of items to a categorized dict.
        
        Attempts to detect the item type from the content.
        """
        if not data:
            return {"tools": [], "prompts": [], "resources": []}
        
        # Check first item to guess type
        first = data[0] if data else {}
        if not isinstance(first, dict):
            return {"tools": data}  # Default to tools
        
        # Heuristics for type detection
        if "inputSchema" in first:
            return {"tools": data}
        elif "arguments" in first and "messages" not in first:
            return {"prompts": data}
        elif "uri" in first or "mimeType" in first:
            return {"resources": data}
        else:
            # Default to tools
            return {"tools": data}
    
    def list_rules(self) -> list[dict[str, str]]:
        """List all available rules with their metadata."""
        rules = []
        for rule in self.registry.get_all():
            rules.append({
                "id": rule.id,
                "description": rule.description,
                "category": rule.category,
                "default_severity": str(rule.default_severity),
            })
        return rules

