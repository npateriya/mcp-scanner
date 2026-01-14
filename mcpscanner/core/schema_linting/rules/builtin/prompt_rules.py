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

"""Built-in linting rules for MCP Prompt definitions.

These rules validate prompt definitions for:
- Required fields (name, description)
- Argument documentation
"""

from ...rule_base import Rule, RuleConfig, Finding, Severity
from ...path_resolver import get_items, build_item_path


class PromptDescriptionRequired(Rule):
    """Validates that all prompts have a non-empty description."""
    
    id = "prompt-description-required"
    description = "Prompts must have a non-empty description field"
    default_severity = Severity.ERROR
    category = "prompt"
    docs_url = "https://github.com/cisco-ai-defense/mcp-scanner/blob/main/docs/design/mcp-schema-linter-design.md#built-in-rules"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        prompts, is_wrapped = get_items(data, "prompts")
        
        for i, prompt in enumerate(prompts):
            if not isinstance(prompt, dict):
                continue
                
            desc = prompt.get("description", "")
            if not desc or (isinstance(desc, str) and not desc.strip()):
                path = build_item_path("prompts", i, is_wrapped)
                findings.append(self.create_finding(
                    message=f"Prompt '{prompt.get('name', 'unnamed')}' is missing a description",
                    path=f"{path}.description",
                    config=config,
                    source=source,
                    suggestion="Add a meaningful description that explains what the prompt does",
                ))
        
        return findings


class PromptArgumentsDescription(Rule):
    """Validates that prompt arguments have descriptions."""
    
    id = "prompt-arguments-description"
    description = "Prompt arguments should have descriptions explaining their purpose"
    default_severity = Severity.WARN
    category = "prompt"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        prompts, is_wrapped = get_items(data, "prompts")
        
        for i, prompt in enumerate(prompts):
            if not isinstance(prompt, dict):
                continue
            
            arguments = prompt.get("arguments", [])
            if not isinstance(arguments, list):
                continue
            
            prompt_name = prompt.get("name", "unnamed")
            base_path = build_item_path("prompts", i, is_wrapped)
            
            for j, arg in enumerate(arguments):
                if not isinstance(arg, dict):
                    continue
                
                arg_name = arg.get("name", "unnamed")
                arg_desc = arg.get("description", "")
                
                if not arg_desc or (isinstance(arg_desc, str) and not arg_desc.strip()):
                    findings.append(self.create_finding(
                        message=f"Prompt '{prompt_name}' argument '{arg_name}' is missing description",
                        path=f"{base_path}.arguments[{j}].description",
                        config=config,
                        source=source,
                        suggestion=f"Add a description explaining what '{arg_name}' is used for",
                    ))
        
        return findings


class PromptArgumentTypeDefined(Rule):
    """Validates that prompt arguments have a type defined."""
    
    id = "prompt-argument-type-defined"
    description = "Prompt arguments should have a type defined for validation"
    default_severity = Severity.INFO
    category = "prompt"
    
    VALID_TYPES = {"string", "number", "boolean", "integer", "array", "object"}
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        prompts, is_wrapped = get_items(data, "prompts")
        
        for i, prompt in enumerate(prompts):
            if not isinstance(prompt, dict):
                continue
            
            arguments = prompt.get("arguments", [])
            if not isinstance(arguments, list):
                continue
            
            prompt_name = prompt.get("name", "unnamed")
            base_path = build_item_path("prompts", i, is_wrapped)
            
            for j, arg in enumerate(arguments):
                if not isinstance(arg, dict):
                    continue
                
                arg_name = arg.get("name", "unnamed")
                arg_type = arg.get("type")
                
                if not arg_type:
                    findings.append(self.create_finding(
                        message=f"Prompt '{prompt_name}' argument '{arg_name}' has no type defined",
                        path=f"{base_path}.arguments[{j}].type",
                        config=config,
                        source=source,
                        suggestion="Add a type (string, number, boolean, etc.) for input validation",
                    ))
                elif arg_type not in self.VALID_TYPES:
                    findings.append(self.create_finding(
                        message=f"Prompt '{prompt_name}' argument '{arg_name}' has unknown type '{arg_type}'",
                        path=f"{base_path}.arguments[{j}].type",
                        config=config,
                        source=source,
                        suggestion=f"Use a valid type: {', '.join(sorted(self.VALID_TYPES))}",
                    ))
        
        return findings


class PromptRequiredArgumentsExist(Rule):
    """Validates that required arguments are defined in arguments list."""
    
    id = "prompt-required-arguments-exist"
    description = "Arguments marked as required must exist in the arguments list"
    default_severity = Severity.ERROR
    category = "prompt"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        prompts, is_wrapped = get_items(data, "prompts")
        
        for i, prompt in enumerate(prompts):
            if not isinstance(prompt, dict):
                continue
            
            arguments = prompt.get("arguments", [])
            if not isinstance(arguments, list):
                continue
            
            prompt_name = prompt.get("name", "unnamed")
            base_path = build_item_path("prompts", i, is_wrapped)
            
            # Collect defined argument names
            defined_args = {arg.get("name") for arg in arguments if isinstance(arg, dict) and arg.get("name")}
            
            # Check if there's a separate 'required' array (schema-style)
            required = prompt.get("required", [])
            if isinstance(required, list):
                for req_arg in required:
                    if req_arg not in defined_args:
                        findings.append(self.create_finding(
                            message=f"Prompt '{prompt_name}' requires '{req_arg}' but it's not in arguments",
                            path=f"{base_path}.required",
                            config=config,
                            source=source,
                            suggestion=f"Add '{req_arg}' to arguments or remove from required",
                        ))
            
            # Also check individual argument 'required' flags consistency
            for j, arg in enumerate(arguments):
                if not isinstance(arg, dict):
                    continue
                
                arg_name = arg.get("name")
                is_required = arg.get("required", False)
                
                # If argument says it's required, ensure it has a name
                if is_required and not arg_name:
                    findings.append(self.create_finding(
                        message=f"Prompt '{prompt_name}' has a required argument without a name",
                        path=f"{base_path}.arguments[{j}]",
                        config=config,
                        source=source,
                        suggestion="Add a name to the required argument",
                    ))
        
        return findings


class PromptNoDuplicateNames(Rule):
    """Validates that prompt names are unique."""
    
    id = "prompt-no-duplicate-names"
    description = "Prompt names must be unique within a definition"
    default_severity = Severity.ERROR
    category = "prompt"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        prompts, is_wrapped = get_items(data, "prompts")
        
        seen_names: dict[str, int] = {}
        
        for i, prompt in enumerate(prompts):
            if not isinstance(prompt, dict):
                continue
            
            name = prompt.get("name", "")
            if not name:
                continue
            
            if name in seen_names:
                path = build_item_path("prompts", i, is_wrapped)
                findings.append(self.create_finding(
                    message=f"Duplicate prompt name '{name}' (first at index {seen_names[name]})",
                    path=f"{path}.name",
                    config=config,
                    source=source,
                    suggestion="Rename to be unique",
                ))
            else:
                seen_names[name] = i
        
        return findings


class PromptNoDuplicateArguments(Rule):
    """Validates that argument names within a prompt are unique."""
    
    id = "prompt-no-duplicate-arguments"
    description = "Prompt argument names must be unique within each prompt"
    default_severity = Severity.ERROR
    category = "prompt"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        prompts, is_wrapped = get_items(data, "prompts")
        
        for i, prompt in enumerate(prompts):
            if not isinstance(prompt, dict):
                continue
            
            arguments = prompt.get("arguments", [])
            if not isinstance(arguments, list):
                continue
            
            prompt_name = prompt.get("name", "unnamed")
            base_path = build_item_path("prompts", i, is_wrapped)
            
            seen_args: dict[str, int] = {}
            
            for j, arg in enumerate(arguments):
                if not isinstance(arg, dict):
                    continue
                
                arg_name = arg.get("name", "")
                if not arg_name:
                    continue
                
                if arg_name in seen_args:
                    findings.append(self.create_finding(
                        message=f"Prompt '{prompt_name}' has duplicate argument '{arg_name}'",
                        path=f"{base_path}.arguments[{j}].name",
                        config=config,
                        source=source,
                        suggestion="Rename to be unique",
                    ))
                else:
                    seen_args[arg_name] = j
        
        return findings
