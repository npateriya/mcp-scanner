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

"""Built-in check functions for dynamic YAML rules.

These functions can be used with the `check` field in custom YAML rules:

    rules:
      my-custom-rule:
        target: "tools[].name"
        check: "pattern"
        options:
          match: "^mycompany_"
        severity: error
        message: "Tool name must start with 'mycompany_'"
"""

import re
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class CheckResult:
    """Result of a check function.
    
    Attributes:
        passed: Whether the check passed
        message: Error message if check failed
    """
    passed: bool
    message: str = ""


# Type alias for check functions
CheckFunction = Callable[[Any, dict[str, Any]], CheckResult]


# Registry of built-in check functions
_CHECKS: dict[str, CheckFunction] = {}


def register_check(name: str):
    """Decorator to register a check function."""
    def decorator(func: CheckFunction) -> CheckFunction:
        _CHECKS[name] = func
        return func
    return decorator


def get_check(name: str) -> CheckFunction | None:
    """Get a check function by name."""
    return _CHECKS.get(name)


def list_checks() -> list[str]:
    """List all available check function names."""
    return list(_CHECKS.keys())


# =============================================================================
# Built-in Check Functions
# =============================================================================


@register_check("pattern")
def check_pattern(value: Any, options: dict[str, Any]) -> CheckResult:
    """Check if value matches a regex pattern.
    
    Options:
        match: Regex pattern that value must match
        notMatch: Regex pattern that value must NOT match
        
    Example:
        check: "pattern"
        options:
          match: "^[a-z_]+$"
    """
    if not isinstance(value, str):
        return CheckResult(passed=True)  # Skip non-strings
    
    match_pattern = options.get("match")
    not_match_pattern = options.get("notMatch")
    
    if match_pattern:
        if not re.search(match_pattern, value):
            return CheckResult(
                passed=False,
                message=f"Value '{value}' does not match pattern '{match_pattern}'"
            )
    
    if not_match_pattern:
        if re.search(not_match_pattern, value):
            return CheckResult(
                passed=False,
                message=f"Value '{value}' matches forbidden pattern '{not_match_pattern}'"
            )
    
    return CheckResult(passed=True)


@register_check("minLength")
def check_min_length(value: Any, options: dict[str, Any]) -> CheckResult:
    """Check if string value meets minimum length.
    
    Options:
        min: Minimum length required
        
    Example:
        check: "minLength"
        options:
          min: 20
    """
    min_length = options.get("min", 0)
    
    if not isinstance(value, str):
        return CheckResult(passed=True)  # Skip non-strings
    
    if len(value) < min_length:
        return CheckResult(
            passed=False,
            message=f"Value is too short ({len(value)} chars, minimum {min_length})"
        )
    
    return CheckResult(passed=True)


@register_check("maxLength")
def check_max_length(value: Any, options: dict[str, Any]) -> CheckResult:
    """Check if string value doesn't exceed maximum length.
    
    Options:
        max: Maximum length allowed
        
    Example:
        check: "maxLength"
        options:
          max: 100
    """
    max_length = options.get("max", float("inf"))
    
    if not isinstance(value, str):
        return CheckResult(passed=True)  # Skip non-strings
    
    if len(value) > max_length:
        return CheckResult(
            passed=False,
            message=f"Value is too long ({len(value)} chars, maximum {max_length})"
        )
    
    return CheckResult(passed=True)


@register_check("required")
def check_required(value: Any, options: dict[str, Any]) -> CheckResult:
    """Check if value exists and is not empty.
    
    Options:
        allowEmpty: If true, empty strings/lists are allowed (default: false)
        
    Example:
        check: "required"
    """
    allow_empty = options.get("allowEmpty", False)
    
    if value is None:
        return CheckResult(
            passed=False,
            message="Required field is missing"
        )
    
    if not allow_empty:
        if isinstance(value, str) and not value.strip():
            return CheckResult(
                passed=False,
                message="Required field is empty"
            )
        if isinstance(value, (list, dict)) and len(value) == 0:
            return CheckResult(
                passed=False,
                message="Required field is empty"
            )
    
    return CheckResult(passed=True)


@register_check("enum")
def check_enum(value: Any, options: dict[str, Any]) -> CheckResult:
    """Check if value is one of allowed values.
    
    Options:
        values: List of allowed values
        
    Example:
        check: "enum"
        options:
          values: ["high", "medium", "low"]
    """
    allowed_values = options.get("values", [])
    
    if not allowed_values:
        return CheckResult(passed=True)  # No values specified
    
    if value not in allowed_values:
        values_str = ", ".join(repr(v) for v in allowed_values)
        return CheckResult(
            passed=False,
            message=f"Value '{value}' is not one of: {values_str}"
        )
    
    return CheckResult(passed=True)


@register_check("type")
def check_type(value: Any, options: dict[str, Any]) -> CheckResult:
    """Check if value is of expected type.
    
    Options:
        type: Expected type (string, number, boolean, object, array, null)
        
    Example:
        check: "type"
        options:
          type: "string"
    """
    expected_type = options.get("type")
    
    if not expected_type:
        return CheckResult(passed=True)
    
    type_map = {
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "object": dict,
        "array": list,
        "null": type(None),
    }
    
    expected_python_type = type_map.get(expected_type)
    
    if expected_python_type is None:
        return CheckResult(passed=True)  # Unknown type, skip
    
    # Special case: bool is subclass of int in Python
    if expected_type == "boolean" and isinstance(value, bool):
        return CheckResult(passed=True)
    if expected_type in ("number", "integer") and isinstance(value, bool):
        return CheckResult(
            passed=False,
            message=f"Expected type '{expected_type}', got 'boolean'"
        )
    
    if not isinstance(value, expected_python_type):
        actual_type = type(value).__name__
        return CheckResult(
            passed=False,
            message=f"Expected type '{expected_type}', got '{actual_type}'"
        )
    
    return CheckResult(passed=True)


@register_check("notEmpty")
def check_not_empty(value: Any, options: dict[str, Any]) -> CheckResult:
    """Check if value is not empty (non-empty string, list, or dict).
    
    Example:
        check: "notEmpty"
    """
    if value is None:
        return CheckResult(
            passed=False,
            message="Value is null/None"
        )
    
    if isinstance(value, str) and not value.strip():
        return CheckResult(
            passed=False,
            message="Value is an empty string"
        )
    
    if isinstance(value, (list, dict)) and len(value) == 0:
        return CheckResult(
            passed=False,
            message=f"Value is an empty {type(value).__name__}"
        )
    
    return CheckResult(passed=True)


@register_check("startsWith")
def check_starts_with(value: Any, options: dict[str, Any]) -> CheckResult:
    """Check if string starts with a prefix.
    
    Options:
        prefix: Required prefix (or list of prefixes)
        
    Example:
        check: "startsWith"
        options:
          prefix: "get_"
    """
    prefixes = options.get("prefix", [])
    if isinstance(prefixes, str):
        prefixes = [prefixes]
    
    if not prefixes:
        return CheckResult(passed=True)
    
    if not isinstance(value, str):
        return CheckResult(passed=True)  # Skip non-strings
    
    for prefix in prefixes:
        if value.startswith(prefix):
            return CheckResult(passed=True)
    
    prefixes_str = ", ".join(repr(p) for p in prefixes)
    return CheckResult(
        passed=False,
        message=f"Value '{value}' must start with one of: {prefixes_str}"
    )


@register_check("endsWith")
def check_ends_with(value: Any, options: dict[str, Any]) -> CheckResult:
    """Check if string ends with a suffix.
    
    Options:
        suffix: Required suffix (or list of suffixes)
        
    Example:
        check: "endsWith"
        options:
          suffix: "_id"
    """
    suffixes = options.get("suffix", [])
    if isinstance(suffixes, str):
        suffixes = [suffixes]
    
    if not suffixes:
        return CheckResult(passed=True)
    
    if not isinstance(value, str):
        return CheckResult(passed=True)  # Skip non-strings
    
    for suffix in suffixes:
        if value.endswith(suffix):
            return CheckResult(passed=True)
    
    suffixes_str = ", ".join(repr(s) for s in suffixes)
    return CheckResult(
        passed=False,
        message=f"Value '{value}' must end with one of: {suffixes_str}"
    )


@register_check("casing")
def check_casing(value: Any, options: dict[str, Any]) -> CheckResult:
    """Check if string follows a casing convention.
    
    Options:
        convention: One of 'snake_case', 'camelCase', 'kebab-case', 'PascalCase'
        
    Example:
        check: "casing"
        options:
          convention: "snake_case"
    """
    convention = options.get("convention", "snake_case")
    
    if not isinstance(value, str):
        return CheckResult(passed=True)
    
    patterns = {
        "snake_case": r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$",
        "camelCase": r"^[a-z][a-zA-Z0-9]*$",
        "kebab-case": r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$",
        "PascalCase": r"^[A-Z][a-zA-Z0-9]*$",
    }
    
    pattern = patterns.get(convention)
    if not pattern:
        return CheckResult(passed=True)  # Unknown convention
    
    if not re.match(pattern, value):
        return CheckResult(
            passed=False,
            message=f"Value '{value}' does not follow {convention} convention"
        )
    
    return CheckResult(passed=True)


@register_check("range")
def check_range(value: Any, options: dict[str, Any]) -> CheckResult:
    """Check if numeric value is within a range.
    
    Options:
        min: Minimum value (inclusive)
        max: Maximum value (inclusive)
        
    Example:
        check: "range"
        options:
          min: 1
          max: 100
    """
    if not isinstance(value, (int, float)):
        return CheckResult(passed=True)  # Skip non-numbers
    
    min_val = options.get("min")
    max_val = options.get("max")
    
    if min_val is not None and value < min_val:
        return CheckResult(
            passed=False,
            message=f"Value {value} is below minimum {min_val}"
        )
    
    if max_val is not None and value > max_val:
        return CheckResult(
            passed=False,
            message=f"Value {value} is above maximum {max_val}"
        )
    
    return CheckResult(passed=True)

