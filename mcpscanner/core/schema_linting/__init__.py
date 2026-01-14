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

"""MCP Schema Linting - Spectral-like validation for MCP definitions.

This module provides quality and best-practice validation for MCP tool,
prompt, and resource definitions. It complements the security scanning
capabilities with schema completeness and documentation quality checks.

Example usage:
    from mcpscanner.core.schema_linting import SchemaLinter, LintConfig
    
    linter = SchemaLinter()
    findings = linter.lint_file("tools.json")
    
    for finding in findings:
        print(f"{finding.severity}: {finding.message}")

CLI usage:
    from mcpscanner.core.schema_linting import (
        SchemaLinter, LintConfig, load_lint_config,
        TextFormatter, JsonFormatter, TableFormatter,
    )
"""

from .rule_base import Finding, RuleConfig, Rule, Severity
from .linter import SchemaLinter, LintConfig
from .rule_loader import load_config as load_lint_config
from .formatters import TextFormatter, JsonFormatter, TableFormatter
from .orchestrator import LintOrchestrator, LintOptions

__all__ = [
    # Core classes
    "Finding",
    "RuleConfig", 
    "Rule",
    "Severity",
    "SchemaLinter",
    "LintConfig",
    # Orchestrator (main entry point)
    "LintOrchestrator",
    "LintOptions",
    # Config loader
    "load_lint_config",
    # Formatters
    "TextFormatter",
    "JsonFormatter",
    "TableFormatter",
]

