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

"""Rule registry for managing and discovering linting rules."""

from typing import Type
from ..rule_base import Rule


class RuleRegistry:
    """Registry for linting rules.
    
    Provides a central place to register, discover, and instantiate rules.
    Supports both built-in rules and custom user-defined rules.
    
    Example:
        registry = RuleRegistry()
        registry.register(MyCustomRule)
        
        for rule in registry.get_all():
            findings = rule.check(data, config)
    """
    
    def __init__(self):
        self._rules: dict[str, Type[Rule]] = {}
        self._instances: dict[str, Rule] = {}
    
    def register(self, rule_class: Type[Rule]) -> None:
        """Register a rule class.
        
        Args:
            rule_class: A Rule subclass to register
            
        Raises:
            ValueError: If rule has no id or is already registered
        """
        if not rule_class.id:
            raise ValueError(f"Rule {rule_class.__name__} has no id defined")
        
        if rule_class.id in self._rules:
            raise ValueError(f"Rule '{rule_class.id}' is already registered")
        
        self._rules[rule_class.id] = rule_class
    
    def get(self, rule_id: str) -> Rule | None:
        """Get a rule instance by id.
        
        Args:
            rule_id: The unique rule identifier
            
        Returns:
            Rule instance or None if not found
        """
        if rule_id not in self._rules:
            return None
        
        # Cache instances for reuse
        if rule_id not in self._instances:
            self._instances[rule_id] = self._rules[rule_id]()
        
        return self._instances[rule_id]
    
    def get_all(self) -> list[Rule]:
        """Get instances of all registered rules."""
        return [self.get(rule_id) for rule_id in self._rules if self.get(rule_id)]
    
    def get_by_category(self, category: str) -> list[Rule]:
        """Get all rules in a specific category.
        
        Args:
            category: Category name (tool, prompt, resource, general)
            
        Returns:
            List of rules in that category
        """
        return [
            rule for rule in self.get_all()
            if rule.category == category
        ]
    
    def list_ids(self) -> list[str]:
        """Get list of all registered rule IDs."""
        return list(self._rules.keys())
    
    def __len__(self) -> int:
        return len(self._rules)
    
    def __contains__(self, rule_id: str) -> bool:
        return rule_id in self._rules


# Default registry with built-in rules
_default_registry: RuleRegistry | None = None


def get_default_registry() -> RuleRegistry:
    """Get the default registry with all built-in rules registered.
    
    This is lazily initialized to avoid import cycles.
    """
    global _default_registry
    
    if _default_registry is None:
        _default_registry = RuleRegistry()
        
        # Import and register built-in rules
        from .builtin.tool_rules import (
            ToolDescriptionRequired,
            ToolDescriptionMinLength,
            ToolNameCasing,
            ToolInputSchemaRequired,
            ToolInputSchemaProperties,
            ToolNoDuplicateNames,
            ToolNameNoReserved,
            # Schema validation rules
            ToolRequiredPropertiesExist,
            ToolPropertyTypeDefined,
            ToolSchemaNoEmptyObject,
            ToolEnumTypeConsistent,
            ToolEnumNoDuplicates,
            ToolAdditionalPropertiesExplicit,
            # Documentation rules
            ToolSchemaHasExamples,
            ToolDescriptionNoPlaceholder,
            ToolDescriptionMaxLength,
            DescriptionNoHtml,
            # Naming rules
            ToolNameMinLength,
            ToolNameMaxLength,
            ToolNameActionVerb,
            ToolNameNoGeneric,
            # Output schema rules (MCP 2025-11-25+)
            ToolOutputSchemaDefined,
            ToolOutputSchemaProperties,
        )
        from .builtin.prompt_rules import (
            PromptDescriptionRequired,
            PromptArgumentsDescription,
            PromptArgumentTypeDefined,
            PromptRequiredArgumentsExist,
            PromptNoDuplicateNames,
            PromptNoDuplicateArguments,
        )
        from .builtin.resource_rules import (
            ResourceDescriptionRequired,
            ResourceMimeType,
            ResourceUriValid,
            ResourceNoDuplicateNames,
            ResourceUriTemplateValid,
            ResourceNameCasing,
        )
        from .builtin.general_rules import (
            NoEmptyArrays,
            PromptNameCasing,
        )
        
        # Register tool rules - basic
        _default_registry.register(ToolDescriptionRequired)
        _default_registry.register(ToolDescriptionMinLength)
        _default_registry.register(ToolNameCasing)
        _default_registry.register(ToolInputSchemaRequired)
        _default_registry.register(ToolInputSchemaProperties)
        _default_registry.register(ToolNoDuplicateNames)
        _default_registry.register(ToolNameNoReserved)
        
        # Register tool rules - schema validation
        _default_registry.register(ToolRequiredPropertiesExist)
        _default_registry.register(ToolPropertyTypeDefined)
        _default_registry.register(ToolSchemaNoEmptyObject)
        _default_registry.register(ToolEnumTypeConsistent)
        _default_registry.register(ToolEnumNoDuplicates)
        _default_registry.register(ToolAdditionalPropertiesExplicit)
        
        # Register tool rules - documentation
        _default_registry.register(ToolSchemaHasExamples)
        _default_registry.register(ToolDescriptionNoPlaceholder)
        _default_registry.register(ToolDescriptionMaxLength)
        _default_registry.register(DescriptionNoHtml)
        
        # Register tool rules - naming
        _default_registry.register(ToolNameMinLength)
        _default_registry.register(ToolNameMaxLength)
        _default_registry.register(ToolNameActionVerb)
        _default_registry.register(ToolNameNoGeneric)
        
        # Register tool rules - output schema (MCP 2025-11-25+)
        _default_registry.register(ToolOutputSchemaDefined)
        _default_registry.register(ToolOutputSchemaProperties)
        
        # Register prompt rules
        _default_registry.register(PromptDescriptionRequired)
        _default_registry.register(PromptArgumentsDescription)
        _default_registry.register(PromptNameCasing)
        _default_registry.register(PromptArgumentTypeDefined)
        _default_registry.register(PromptRequiredArgumentsExist)
        _default_registry.register(PromptNoDuplicateNames)
        _default_registry.register(PromptNoDuplicateArguments)
        
        # Register resource rules
        _default_registry.register(ResourceDescriptionRequired)
        _default_registry.register(ResourceMimeType)
        _default_registry.register(ResourceUriValid)
        _default_registry.register(ResourceNoDuplicateNames)
        _default_registry.register(ResourceUriTemplateValid)
        _default_registry.register(ResourceNameCasing)
        
        # Register general rules
        _default_registry.register(NoEmptyArrays)
    
    return _default_registry

