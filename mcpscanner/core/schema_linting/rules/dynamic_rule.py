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

"""Dynamic rules defined via YAML configuration.

Dynamic rules allow users to create custom linting rules without writing Python code.

Example YAML:
    rules:
      acme-tool-prefix:
        target: "tools[].name"
        check: "pattern"
        options:
          match: "^acme_"
        severity: error
        message: "Tool name must start with 'acme_'"
"""

from typing import Any

from ..rule_base import Rule, Finding, RuleConfig, Severity
from ..path_resolver import query_path
from ..checks import get_check, CheckResult


class DynamicRule(Rule):
    """A rule defined dynamically via YAML configuration.
    
    Attributes:
        id: Unique rule identifier
        description: Human-readable description
        default_severity: Default severity level
        target: Path pattern to query (e.g., "tools[].name")
        check_name: Name of the check function to use
        check_options: Options to pass to the check function
        custom_message: Custom message template for failures
        recommendation: Recommended fix
    """
    
    category = "custom"
    
    def __init__(
        self,
        rule_id: str,
        target: str,
        check_name: str,
        options: dict[str, Any] | None = None,
        severity: str = "warn",
        message: str | None = None,
        description: str | None = None,
        recommendation: str | None = None,
    ):
        """Initialize a dynamic rule.
        
        Args:
            rule_id: Unique identifier for this rule
            target: Path pattern to query (e.g., "tools[].name")
            check_name: Name of the built-in check function
            options: Options to pass to the check function
            severity: Default severity level
            message: Custom message template (can use {value}, {path})
            description: Human-readable description
            recommendation: Recommended fix
        """
        self.id = rule_id
        self.target = target
        self.check_name = check_name
        self.check_options = options or {}
        self.default_severity = Severity.from_string(severity)
        self.custom_message = message
        self.description = description or f"Custom rule: {check_name} on {target}"
        self.recommendation = recommendation
    
    def check(
        self, 
        data: dict, 
        config: RuleConfig, 
        source: str = ""
    ) -> list[Finding]:
        """Execute the dynamic rule on the data.
        
        Args:
            data: MCP definition data to check
            config: Rule configuration
            source: Source file/URL
            
        Returns:
            List of findings for any violations
        """
        findings = []
        
        # Get the check function
        check_func = get_check(self.check_name)
        if check_func is None:
            # Unknown check function - skip with warning
            findings.append(self.create_finding(
                message=f"Unknown check function '{self.check_name}'",
                path="",
                config=config,
                source=source,
            ))
            return findings
        
        # Merge config options with rule options
        merged_options = {**self.check_options}
        if config.options:
            merged_options.update(config.options)
        
        # Query all values matching the target path
        for match in query_path(data, self.target):
            result: CheckResult = check_func(match.value, merged_options)
            
            if not result.passed:
                message = self._format_message(result.message, match.value, match.path)
                findings.append(self.create_finding(
                    message=message,
                    path=match.path,
                    config=config,
                    source=source,
                ))
        
        return findings
    
    def _format_message(self, default_message: str, value: Any, path: str) -> str:
        """Format the finding message.
        
        Supports placeholders:
        - {value}: The actual value that failed
        - {path}: The path to the value
        - {check}: The check function name
        """
        if self.custom_message:
            try:
                return self.custom_message.format(
                    value=value,
                    path=path,
                    check=self.check_name,
                )
            except (KeyError, ValueError):
                return self.custom_message
        return default_message


def create_dynamic_rule(rule_id: str, rule_def: dict[str, Any]) -> DynamicRule | None:
    """Create a DynamicRule from a YAML rule definition.
    
    Args:
        rule_id: The rule identifier
        rule_def: The rule definition dictionary from YAML
        
    Returns:
        DynamicRule instance, or None if the definition is not a dynamic rule
        
    Example rule_def:
        {
            "target": "tools[].name",
            "check": "pattern",
            "options": {"match": "^acme_"},
            "severity": "error",
            "message": "Tool name must start with 'acme_'"
        }
    """
    # Check if this is a dynamic rule (has 'target' and 'check')
    if "target" not in rule_def or "check" not in rule_def:
        return None
    
    return DynamicRule(
        rule_id=rule_id,
        target=rule_def["target"],
        check_name=rule_def["check"],
        options=rule_def.get("options"),
        severity=rule_def.get("severity", "warn"),
        message=rule_def.get("message"),
        description=rule_def.get("description"),
        recommendation=rule_def.get("recommendation"),
    )


def parse_dynamic_rules(rules_config: dict[str, Any]) -> list[DynamicRule]:
    """Parse all dynamic rules from a rules configuration.
    
    Args:
        rules_config: The 'rules' section of a YAML config
        
    Returns:
        List of DynamicRule instances
        
    Example:
        config = {
            "rules": {
                "my-rule": {
                    "target": "tools[].name",
                    "check": "pattern",
                    "options": {"match": "^my_"}
                },
                "tool-description-required": {"severity": "error"}  # Not dynamic
            }
        }
        rules = parse_dynamic_rules(config.get("rules", {}))
        # Returns [DynamicRule(id="my-rule", ...)]
    """
    dynamic_rules = []
    
    for rule_id, rule_def in rules_config.items():
        if isinstance(rule_def, dict):
            rule = create_dynamic_rule(rule_id, rule_def)
            if rule:
                dynamic_rules.append(rule)
    
    return dynamic_rules

