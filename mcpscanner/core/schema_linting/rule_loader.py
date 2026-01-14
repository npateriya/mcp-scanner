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

"""Configuration and ruleset loader for MCP Schema Linting.

This module handles:
- Loading .mcp-lint.yaml configuration files
- Resolving ruleset extensions (e.g., "mcp:recommended")
- Loading custom rule plugins
"""

from pathlib import Path
from typing import Any

from .linter import LintConfig
from .rule_base import RuleConfig, Severity


# Try to import yaml, with fallback
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def load_config(config_path: str | Path | None = None) -> LintConfig:
    """Load linting configuration from file or discover it.
    
    Args:
        config_path: Explicit path to config file. If None, searches for
                    .mcp-lint.yaml, .mcp-lint.yml, or mcp-lint.yaml
                    
    Returns:
        LintConfig instance
        
    Raises:
        ValueError: If config file is specified but not found
        ImportError: If YAML config is used but PyYAML is not installed
    """
    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise ValueError(f"Configuration file not found: {config_path}")
        return _load_yaml_config(path)
    
    # Search for config file in current directory
    search_paths = [
        ".mcp-lint.yaml",
        ".mcp-lint.yml",
        "mcp-lint.yaml",
        "mcp-lint.yml",
    ]
    
    for name in search_paths:
        path = Path(name)
        if path.exists():
            return _load_yaml_config(path)
    
    # No config found, return defaults
    return LintConfig.default()


def _load_yaml_config(path: Path) -> LintConfig:
    """Load configuration from a YAML file."""
    if not HAS_YAML:
        raise ImportError(
            "PyYAML is required for YAML configuration files. "
            "Install it with: pip install pyyaml"
        )
    
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    
    return _parse_config(data)


def _parse_config(data: dict) -> LintConfig:
    """Parse configuration dictionary into LintConfig."""
    # Use LintConfig.from_dict which handles dynamic rules
    config = LintConfig.from_dict(data)
    
    # Handle extends
    extends = data.get("extends", [])
    if isinstance(extends, str):
        extends = [extends]
    
    # Resolve extended rulesets and merge
    for ruleset in extends:
        resolved = resolve_ruleset(ruleset)
        # Merge with lower priority (explicit rules override)
        for rule_id, rule_config in resolved.items():
            if rule_id not in config.rules:
                config.rules[rule_id] = rule_config
    
    config.extends = extends
    return config


def resolve_ruleset(ruleset_name: str) -> dict[str, RuleConfig]:
    """Resolve a ruleset name to rule configurations.
    
    Built-in rulesets:
    - mcp:recommended - Recommended rules for MCP validation
    - mcp:strict - Stricter settings with more rules enabled
    - mcp:quality - Focus on documentation quality
    
    Args:
        ruleset_name: Name of the ruleset (e.g., "mcp:recommended")
        
    Returns:
        Dictionary mapping rule IDs to their configurations
    """
    rulesets = {
        "mcp:recommended": _get_recommended_ruleset(),
        "mcp:strict": _get_strict_ruleset(),
        "mcp:quality": _get_quality_ruleset(),
    }
    
    if ruleset_name in rulesets:
        return rulesets[ruleset_name]
    
    # Try to load from file
    if ruleset_name.endswith((".yaml", ".yml")):
        path = Path(ruleset_name)
        if path.exists():
            config = _load_yaml_config(path)
            return config.rules
    
    # Unknown ruleset - return empty
    return {}


def _get_recommended_ruleset() -> dict[str, RuleConfig]:
    """Get the recommended ruleset configuration."""
    return {
        # Tool rules
        "tool-description-required": RuleConfig(severity=Severity.ERROR),
        "tool-description-min-length": RuleConfig(
            severity=Severity.WARN,
            options={"min": 20}
        ),
        "tool-name-casing": RuleConfig(
            severity=Severity.WARN,
            options={"convention": "snake_case"}
        ),
        "tool-input-schema-required": RuleConfig(severity=Severity.WARN),
        "tool-input-schema-properties": RuleConfig(severity=Severity.INFO),
        
        # Prompt rules
        "prompt-description-required": RuleConfig(severity=Severity.ERROR),
        "prompt-arguments-description": RuleConfig(severity=Severity.WARN),
        
        # Resource rules
        "resource-description-required": RuleConfig(severity=Severity.WARN),
        "resource-mime-type": RuleConfig(severity=Severity.INFO),
    }


def _get_strict_ruleset() -> dict[str, RuleConfig]:
    """Get the strict ruleset configuration."""
    return {
        # Tool rules - all errors
        "tool-description-required": RuleConfig(severity=Severity.ERROR),
        "tool-description-min-length": RuleConfig(
            severity=Severity.ERROR,
            options={"min": 30}
        ),
        "tool-name-casing": RuleConfig(
            severity=Severity.ERROR,
            options={"convention": "snake_case"}
        ),
        "tool-input-schema-required": RuleConfig(severity=Severity.ERROR),
        "tool-input-schema-properties": RuleConfig(
            severity=Severity.ERROR,
            options={"require_property_descriptions": True}
        ),
        
        # Prompt rules - all errors
        "prompt-description-required": RuleConfig(severity=Severity.ERROR),
        "prompt-arguments-description": RuleConfig(severity=Severity.ERROR),
        
        # Resource rules
        "resource-description-required": RuleConfig(severity=Severity.ERROR),
        "resource-mime-type": RuleConfig(severity=Severity.WARN),
    }


def _get_quality_ruleset() -> dict[str, RuleConfig]:
    """Get the quality-focused ruleset configuration."""
    return {
        # Focus on documentation quality
        "tool-description-required": RuleConfig(severity=Severity.ERROR),
        "tool-description-min-length": RuleConfig(
            severity=Severity.WARN,
            options={"min": 50}  # Longer descriptions required
        ),
        "tool-name-casing": RuleConfig(severity=Severity.INFO),
        "tool-input-schema-required": RuleConfig(severity=Severity.WARN),
        "tool-input-schema-properties": RuleConfig(
            severity=Severity.WARN,
            options={"require_property_descriptions": True}
        ),
        
        "prompt-description-required": RuleConfig(severity=Severity.ERROR),
        "prompt-arguments-description": RuleConfig(severity=Severity.ERROR),
        
        "resource-description-required": RuleConfig(severity=Severity.ERROR),
        "resource-mime-type": RuleConfig(severity=Severity.INFO),
    }


def discover_config_file(start_dir: str | Path | None = None) -> Path | None:
    """Search for a configuration file starting from a directory.
    
    Searches upward through parent directories for config files.
    
    Args:
        start_dir: Starting directory for search. Defaults to current directory.
        
    Returns:
        Path to config file if found, None otherwise
    """
    config_names = [
        ".mcp-lint.yaml",
        ".mcp-lint.yml",
        "mcp-lint.yaml",
        "mcp-lint.yml",
    ]
    
    current = Path(start_dir) if start_dir else Path.cwd()
    
    # Search up to root
    while current != current.parent:
        for name in config_names:
            config_path = current / name
            if config_path.exists():
                return config_path
        current = current.parent
    
    return None

