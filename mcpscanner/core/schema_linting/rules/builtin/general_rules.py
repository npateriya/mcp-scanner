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

"""Built-in general linting rules for MCP definitions.

These rules apply across all MCP definition types:
- Empty array validation
- General structure checks
"""

import re
from ...rule_base import Rule, RuleConfig, Finding, Severity
from ...path_resolver import get_items, build_item_path


class NoEmptyArrays(Rule):
    """Validates that tools/prompts/resources arrays are not empty."""
    
    id = "no-empty-arrays"
    description = "MCP definitions should not have empty tools, prompts, or resources arrays"
    default_severity = Severity.WARN
    category = "general"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        
        if not isinstance(data, dict):
            return findings
        
        # Check for empty arrays
        for key in ["tools", "prompts", "resources"]:
            if key in data:
                value = data[key]
                if isinstance(value, list) and len(value) == 0:
                    findings.append(self.create_finding(
                        message=f"'{key}' array is empty - consider removing if unused",
                        path=key,
                        config=config,
                        source=source,
                        suggestion=f"Either add {key} or remove the empty array",
                    ))
        
        return findings


class PromptNameCasing(Rule):
    """Validates that prompt names follow a consistent naming convention.
    
    Note: Naming conventions vary across ecosystems. This rule is INFO severity -
    use it to enforce team-specific conventions via config.
    """
    
    id = "prompt-name-casing"
    description = "Prompt names should follow a consistent naming convention"
    default_severity = Severity.INFO  # INFO since conventions vary
    category = "prompt"
    
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
            return findings
        
        prompts, is_wrapped = get_items(data, "prompts")
        
        for i, prompt in enumerate(prompts):
            if not isinstance(prompt, dict):
                continue
            
            name = prompt.get("name", "")
            if name and not pattern.match(name):
                path = build_item_path("prompts", i, is_wrapped)
                findings.append(self.create_finding(
                    message=f"Prompt name '{name}' does not follow {convention} convention",
                    path=f"{path}.name",
                    config=config,
                    source=source,
                    suggestion=f"Rename to follow {convention}",
                ))
        
        return findings
