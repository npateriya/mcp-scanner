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

"""Documentation quality rules for MCP Tool definitions.

These rules validate documentation aspects:
- Example values in schemas
- Placeholder text detection
- Description formatting (length, HTML)
"""

import re
from ...rule_base import Rule, RuleConfig, Finding, Severity
from ...path_resolver import get_items, build_item_path


class ToolSchemaHasExamples(Rule):
    """Validates that schema properties have examples."""
    
    id = "tool-schema-has-examples"
    description = "Schema properties should have example values for documentation"
    default_severity = Severity.INFO
    category = "tool"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        min_properties = config.options.get("min_properties", 1)  # Only warn if >= N properties
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
            
            schema = tool.get("inputSchema", {})
            if not isinstance(schema, dict):
                continue
            
            properties = schema.get("properties", {})
            if len(properties) < min_properties:
                continue
            
            path = build_item_path("tools", i, is_wrapped)
            tool_name = tool.get("name", "unnamed")
            
            missing_examples = []
            for prop_name, prop_schema in properties.items():
                if isinstance(prop_schema, dict):
                    if "example" not in prop_schema and "examples" not in prop_schema:
                        if "default" not in prop_schema:  # default can serve as example
                            missing_examples.append(prop_name)
            
            if missing_examples:
                findings.append(self.create_finding(
                    message=f"Tool '{tool_name}' properties missing examples: {', '.join(missing_examples[:3])}{'...' if len(missing_examples) > 3 else ''}",
                    path=f"{path}.inputSchema.properties",
                    config=config,
                    source=source,
                    suggestion="Add 'example' field to properties for better documentation",
                ))
        
        return findings


class ToolDescriptionNoPlaceholder(Rule):
    """Validates that descriptions don't contain placeholder text."""
    
    id = "tool-description-no-placeholder"
    description = "Descriptions should not contain placeholder text like TODO or TBD"
    default_severity = Severity.ERROR
    category = "tool"
    
    PLACEHOLDER_PATTERNS = [
        r'\bTODO\b',
        r'\bTBD\b',
        r'\bFIXME\b',
        r'\bXXX\b',
        r'\bHACK\b',
        r'^\.{3,}$',  # Just "..."
        r'^\s*$',      # Empty or whitespace
        r'^placeholder',
        r'^description\s*(here)?$',
        r'^add\s+description',
    ]
    
    def __init__(self):
        self._patterns = [re.compile(p, re.IGNORECASE) for p in self.PLACEHOLDER_PATTERNS]
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
            
            desc = tool.get("description", "")
            if not isinstance(desc, str):
                continue
            
            path = build_item_path("tools", i, is_wrapped)
            tool_name = tool.get("name", "unnamed")
            
            for pattern in self._patterns:
                if pattern.search(desc):
                    findings.append(self.create_finding(
                        message=f"Tool '{tool_name}' description contains placeholder text",
                        path=f"{path}.description",
                        config=config,
                        source=source,
                        suggestion="Replace placeholder with a meaningful description",
                    ))
                    break
        
        return findings


class ToolDescriptionMaxLength(Rule):
    """Validates that descriptions aren't excessively long."""
    
    id = "tool-description-max-length"
    description = "Tool descriptions should not be excessively long"
    default_severity = Severity.INFO
    category = "tool"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        max_length = config.options.get("max", 500)
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
            
            desc = tool.get("description", "")
            if isinstance(desc, str) and len(desc) > max_length:
                path = build_item_path("tools", i, is_wrapped)
                findings.append(self.create_finding(
                    message=f"Tool '{tool.get('name', 'unnamed')}' description is too long ({len(desc)} chars, max {max_length})",
                    path=f"{path}.description",
                    config=config,
                    source=source,
                    suggestion="Consider shortening the description; details can go in property descriptions",
                ))
        
        return findings


class DescriptionNoHtml(Rule):
    """Validates that descriptions don't contain HTML tags."""
    
    id = "description-no-html"
    description = "Descriptions should not contain HTML markup"
    default_severity = Severity.WARN
    category = "tool"
    
    HTML_PATTERN = re.compile(r'<[a-zA-Z][^>]*>')
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
            
            desc = tool.get("description", "")
            if isinstance(desc, str) and self.HTML_PATTERN.search(desc):
                path = build_item_path("tools", i, is_wrapped)
                findings.append(self.create_finding(
                    message=f"Tool '{tool.get('name', 'unnamed')}' description contains HTML",
                    path=f"{path}.description",
                    config=config,
                    source=source,
                    suggestion="Use plain text or markdown instead of HTML",
                ))
        
        return findings

