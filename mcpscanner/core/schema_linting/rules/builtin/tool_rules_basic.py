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

"""Basic linting rules for MCP Tool definitions.

These rules validate fundamental tool properties:
- Required fields (name, description)
- Description length requirements
- Naming conventions and validation
"""

import re
from ...rule_base import Rule, RuleConfig, Finding, Severity
from ...path_resolver import get_items, build_item_path


class ToolDescriptionRequired(Rule):
    """Validates that all tools have a non-empty description."""
    
    id = "tool-description-required"
    description = "Tools must have a non-empty description field"
    default_severity = Severity.ERROR
    category = "tool"
    docs_url = "https://github.com/cisco-ai-defense/mcp-scanner/blob/main/docs/design/mcp-schema-linter-design.md#built-in-rules"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
                
            desc = tool.get("description", "")
            if not desc or (isinstance(desc, str) and not desc.strip()):
                path = build_item_path("tools", i, is_wrapped)
                findings.append(self.create_finding(
                    message=f"Tool '{tool.get('name', 'unnamed')}' is missing a description",
                    path=f"{path}.description",
                    config=config,
                    source=source,
                    suggestion="Add a meaningful description that explains what the tool does and how to use it",
                ))
        
        return findings


class ToolDescriptionMinLength(Rule):
    """Validates that tool descriptions meet a minimum length requirement."""
    
    id = "tool-description-min-length"
    description = "Tool descriptions should be at least N characters long"
    default_severity = Severity.WARN
    category = "tool"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        min_length = config.options.get("min", 20)
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
                
            desc = tool.get("description", "")
            if isinstance(desc, str) and desc.strip() and len(desc.strip()) < min_length:
                path = build_item_path("tools", i, is_wrapped)
                findings.append(self.create_finding(
                    message=f"Tool '{tool.get('name', 'unnamed')}' description is too short ({len(desc.strip())} chars, minimum {min_length})",
                    path=f"{path}.description",
                    config=config,
                    source=source,
                    suggestion=f"Expand the description to at least {min_length} characters with meaningful details",
                ))
        
        return findings


class ToolNameCasing(Rule):
    """Validates that tool names follow a consistent naming convention.
    
    Note: Official MCP servers use mixed conventions (camelCase in JS, snake_case in Python).
    This rule is intentionally INFO severity - use it to enforce team conventions.
    """
    
    id = "tool-name-casing"
    description = "Tool names should follow a consistent naming convention"
    default_severity = Severity.INFO  # INFO since conventions vary across ecosystems
    category = "tool"
    
    # Patterns for different naming conventions
    PATTERNS = {
        "snake_case": re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$"),
        "camelCase": re.compile(r"^[a-z][a-zA-Z0-9]*$"),
        "PascalCase": re.compile(r"^[A-Z][a-zA-Z0-9]*$"),
        "kebab-case": re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$"),
    }
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        convention = config.options.get("convention", "snake_case")
        pattern = self.PATTERNS.get(convention)
        
        if not pattern:
            return findings  # Unknown convention, skip
        
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
                
            name = tool.get("name", "")
            if name and not pattern.match(name):
                path = build_item_path("tools", i, is_wrapped)
                findings.append(self.create_finding(
                    message=f"Tool name '{name}' does not follow {convention} convention",
                    path=f"{path}.name",
                    config=config,
                    source=source,
                    suggestion=f"Rename to follow {convention} (e.g., {self._suggest_name(name, convention)})",
                ))
        
        return findings
    
    def _suggest_name(self, name: str, convention: str) -> str:
        """Suggest a corrected name based on convention."""
        # Simple conversion suggestions
        words = re.split(r"[-_\s]+|(?<=[a-z])(?=[A-Z])", name)
        words = [w.lower() for w in words if w]
        
        if convention == "snake_case":
            return "_".join(words)
        elif convention == "camelCase":
            return words[0] + "".join(w.capitalize() for w in words[1:])
        elif convention == "PascalCase":
            return "".join(w.capitalize() for w in words)
        elif convention == "kebab-case":
            return "-".join(words)
        return name


class ToolNoDuplicateNames(Rule):
    """Validates that tool names are unique within a definition."""
    
    id = "tool-no-duplicate-names"
    description = "Tool names must be unique within a definition"
    default_severity = Severity.ERROR
    category = "tool"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        tools, is_wrapped = get_items(data, "tools")
        
        # Track seen names and their first occurrence index
        seen_names: dict[str, int] = {}
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
            
            name = tool.get("name", "")
            if not name:
                continue
            
            if name in seen_names:
                path = build_item_path("tools", i, is_wrapped)
                findings.append(self.create_finding(
                    message=f"Duplicate tool name '{name}' (first defined at index {seen_names[name]})",
                    path=f"{path}.name",
                    config=config,
                    source=source,
                    suggestion=f"Rename one of the '{name}' tools to be unique",
                ))
            else:
                seen_names[name] = i
        
        return findings


class ToolNameNoReserved(Rule):
    """Validates that tool names don't use reserved words."""
    
    id = "tool-name-no-reserved"
    description = "Tool names should not use reserved or problematic words"
    default_severity = Severity.ERROR
    category = "tool"
    
    # Reserved words that could cause issues
    RESERVED_WORDS = {
        # MCP protocol reserved
        "tools", "prompts", "resources", "initialize", "shutdown",
        "ping", "cancel", "progress", "roots", "sampling",
        # Common programming reserved
        "undefined", "null", "none", "true", "false",
        "class", "function", "return", "import", "export",
        # Potentially confusing
        "test", "debug", "internal", "private", "system",
    }
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        
        # Get custom reserved words from options
        custom_reserved = set(config.options.get("reserved_words", []))
        reserved = self.RESERVED_WORDS | custom_reserved
        
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
            
            name = tool.get("name", "").lower()
            if name in reserved:
                path = build_item_path("tools", i, is_wrapped)
                findings.append(self.create_finding(
                    message=f"Tool name '{tool.get('name')}' uses a reserved word",
                    path=f"{path}.name",
                    config=config,
                    source=source,
                    suggestion="Choose a more descriptive name that isn't a reserved word",
                ))
        
        return findings


class ToolNameMinLength(Rule):
    """Validates that tool names meet minimum length."""
    
    id = "tool-name-min-length"
    description = "Tool names should be at least N characters"
    default_severity = Severity.WARN
    category = "tool"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        min_length = config.options.get("min", 3)
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
            
            name = tool.get("name", "")
            if name and len(name) < min_length:
                path = build_item_path("tools", i, is_wrapped)
                findings.append(self.create_finding(
                    message=f"Tool name '{name}' is too short ({len(name)} chars, min {min_length})",
                    path=f"{path}.name",
                    config=config,
                    source=source,
                    suggestion="Use a more descriptive name",
                ))
        
        return findings


class ToolNameMaxLength(Rule):
    """Validates that tool names don't exceed maximum length."""
    
    id = "tool-name-max-length"
    description = "Tool names should not exceed N characters"
    default_severity = Severity.WARN
    category = "tool"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        max_length = config.options.get("max", 64)
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
            
            name = tool.get("name", "")
            if name and len(name) > max_length:
                path = build_item_path("tools", i, is_wrapped)
                findings.append(self.create_finding(
                    message=f"Tool name '{name[:20]}...' is too long ({len(name)} chars, max {max_length})",
                    path=f"{path}.name",
                    config=config,
                    source=source,
                    suggestion="Consider a shorter, more concise name",
                ))
        
        return findings


class ToolNameActionVerb(Rule):
    """Validates that tool names start with an action verb."""
    
    id = "tool-name-action-verb"
    description = "Tool names should start with an action verb"
    default_severity = Severity.INFO
    category = "tool"
    
    # Common action verb prefixes (expanded based on real MCP server analysis)
    ACTION_VERBS = {
        # CRUD operations
        "get", "fetch", "retrieve", "read", "load", "find", "search", "list", "query",
        "create", "add", "insert", "generate", "build", "make", "new", "write",
        "update", "modify", "change", "set", "edit", "patch", "put", "merge",
        "delete", "remove", "destroy", "clear", "reset", "drop",
        # Communication
        "send", "post", "submit", "publish", "notify", "trigger",
        # Validation
        "check", "validate", "verify", "test", "ping", "health",
        # Execution
        "start", "stop", "run", "execute", "invoke", "call",
        "enable", "disable", "toggle", "switch",
        # Data transfer
        "upload", "download", "export", "import", "sync", "push", "pull",
        # Transformation
        "convert", "transform", "parse", "format", "zip", "unzip", "compress",
        # Connection
        "connect", "disconnect", "login", "logout", "authenticate", "open", "close",
        # Events
        "subscribe", "unsubscribe", "watch", "listen",
        # Computation
        "count", "sum", "calculate", "compute", "analyze",
        # Common utilities (from real MCP servers)
        "echo", "print", "log", "sample", "fork", "move", "copy",
        "ask", "annotate", "describe",
        # Git/VCS operations
        "commit", "branch", "checkout", "clone", "rebase", "revert",
        # Directory/tree operations
        "directory", "tree", "walk", "traverse",
    }
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
            
            name = tool.get("name", "")
            if not name:
                continue
            
            # Extract first word (handle snake_case, camelCase, etc.)
            first_word = re.split(r'[-_]|(?<=[a-z])(?=[A-Z])', name)[0].lower()
            
            if first_word not in self.ACTION_VERBS:
                path = build_item_path("tools", i, is_wrapped)
                findings.append(self.create_finding(
                    message=f"Tool name '{name}' should start with an action verb",
                    path=f"{path}.name",
                    config=config,
                    source=source,
                    suggestion="Consider prefixing with: get_, create_, update_, delete_, etc.",
                ))
        
        return findings


class ToolNameNoGeneric(Rule):
    """Validates that tool names aren't too generic."""
    
    id = "tool-name-no-generic"
    description = "Tool names should be specific, not generic"
    default_severity = Severity.WARN
    category = "tool"
    
    GENERIC_NAMES = {
        "run", "do", "execute", "process", "handle",
        "action", "task", "operation", "command", "cmd",
        "data", "item", "thing", "stuff", "misc",
        "main", "default", "generic", "common", "base",
        "helper", "util", "utility", "tool", "func", "function",
    }
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
            
            name = tool.get("name", "").lower()
            
            # Check if name is exactly one of the generic names
            if name in self.GENERIC_NAMES:
                path = build_item_path("tools", i, is_wrapped)
                findings.append(self.create_finding(
                    message=f"Tool name '{tool.get('name')}' is too generic",
                    path=f"{path}.name",
                    config=config,
                    source=source,
                    suggestion="Use a more descriptive name that explains what the tool does",
                ))
        
        return findings

