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

"""Base classes and interfaces for MCP Schema Linting rules.

This module defines the core abstractions for the linting system:
- Finding: Represents a single linting issue
- RuleConfig: Configuration options for a rule
- Rule: Abstract base class for all linting rules
- Severity: Enum for finding severity levels
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """Severity levels for linting findings.
    
    Levels from most to least severe:
    - error: Critical issue that should fail CI/CD
    - warn: Issue that should be addressed
    - info: Informational finding
    - hint: Suggestion for improvement
    - off: Rule is disabled
    """
    ERROR = "error"
    WARN = "warn"
    INFO = "info"
    HINT = "hint"
    OFF = "off"
    
    def __str__(self) -> str:
        return self.value
    
    @classmethod
    def from_string(cls, value: str) -> "Severity":
        """Parse severity from string, case-insensitive."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.WARN  # Default to warn for unknown values


@dataclass
class Finding:
    """Represents a single linting finding/issue.
    
    Attributes:
        rule_id: Unique identifier for the rule that generated this finding
        message: Human-readable description of the issue
        severity: Severity level of the finding
        path: JSONPath-like path to the problematic element (e.g., "tools[0].description")
        source: Source file or identifier where the issue was found
        line: Line number in source file (if available)
        column: Column number in source file (if available)
        suggestion: Optional suggestion for fixing the issue
        docs_url: Optional URL to documentation about this rule
    """
    rule_id: str
    message: str
    severity: Severity
    path: str
    source: str = ""
    line: int | None = None
    column: int | None = None
    suggestion: str | None = None
    docs_url: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert finding to dictionary for JSON serialization."""
        return {
            "rule_id": self.rule_id,
            "message": self.message,
            "severity": str(self.severity),
            "path": self.path,
            "source": self.source,
            "line": self.line,
            "column": self.column,
            "suggestion": self.suggestion,
            "docs_url": self.docs_url,
        }
    
    def format_location(self) -> str:
        """Format location for display."""
        parts = []
        if self.source:
            parts.append(self.source)
        if self.line is not None:
            parts.append(f"line {self.line}")
        if self.column is not None:
            parts.append(f"col {self.column}")
        if self.path:
            parts.append(f"at {self.path}")
        return " ".join(parts) if parts else "unknown location"


@dataclass
class RuleConfig:
    """Configuration for a linting rule.
    
    Attributes:
        severity: Override severity level for this rule
        enabled: Whether the rule is enabled
        options: Rule-specific configuration options
    """
    severity: Severity = Severity.WARN
    enabled: bool = True
    options: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: dict | str | None) -> "RuleConfig":
        """Parse rule config from various formats.
        
        Supports:
        - None or "off" -> disabled
        - "error"/"warn"/"info"/"hint" -> just severity
        - {"severity": "error", "options": {...}} -> full config
        """
        if data is None or data == "off":
            return cls(enabled=False, severity=Severity.OFF)
        
        if isinstance(data, str):
            return cls(severity=Severity.from_string(data))
        
        if isinstance(data, dict):
            severity = Severity.from_string(data.get("severity", "warn"))
            options = data.get("options", {})
            enabled = severity != Severity.OFF
            return cls(severity=severity, enabled=enabled, options=options)
        
        return cls()  # Default config


class Rule(ABC):
    """Abstract base class for all linting rules.
    
    To create a custom rule, subclass this and implement:
    - id: Unique rule identifier (e.g., "tool-description-required")
    - description: Human-readable description of what the rule checks
    - default_severity: Default severity when not configured
    - check(): The actual validation logic
    
    Example:
        class ToolDescriptionRequired(Rule):
            id = "tool-description-required"
            description = "Tools must have a non-empty description"
            default_severity = Severity.ERROR
            
            def check(self, data: dict, config: RuleConfig) -> list[Finding]:
                findings = []
                for i, tool in enumerate(data.get("tools", [])):
                    if not tool.get("description"):
                        findings.append(Finding(
                            rule_id=self.id,
                            message="Tool is missing description",
                            severity=config.severity,
                            path=f"tools[{i}].description"
                        ))
                return findings
    """
    
    # Class attributes that subclasses must define
    id: str = ""
    description: str = ""
    default_severity: Severity = Severity.WARN
    docs_url: str | None = None
    category: str = "general"  # tool, prompt, resource, general
    
    @abstractmethod
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        """Execute the rule and return findings.
        
        Args:
            data: The MCP definition data to validate
            config: Configuration for this rule (severity, options)
            source: Source identifier (filename, URL, etc.)
            
        Returns:
            List of Finding objects for any issues found
        """
        pass
    
    def get_config(self, config: RuleConfig | None = None) -> RuleConfig:
        """Get effective config, using defaults if not provided."""
        if config is None:
            return RuleConfig(severity=self.default_severity)
        return config
    
    def create_finding(
        self,
        message: str,
        path: str,
        config: RuleConfig,
        source: str = "",
        suggestion: str | None = None,
    ) -> Finding:
        """Helper to create a finding with this rule's metadata."""
        return Finding(
            rule_id=self.id,
            message=message,
            severity=config.severity,
            path=path,
            source=source,
            suggestion=suggestion,
            docs_url=self.docs_url,
        )

