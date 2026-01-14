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

"""Schema validation rules for MCP Tool definitions.

These rules validate inputSchema and outputSchema:
- Schema structure and type requirements
- Property definitions and types
- Required properties validation
- Enum consistency
- Additional properties handling
"""

from ...rule_base import Rule, RuleConfig, Finding, Severity
from ...path_resolver import get_items, build_item_path


class ToolInputSchemaRequired(Rule):
    """Validates that tools have an inputSchema defined."""
    
    id = "tool-input-schema-required"
    description = "Tools should have an inputSchema that defines expected parameters"
    default_severity = Severity.WARN
    category = "tool"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
                
            schema = tool.get("inputSchema")
            if schema is None:
                path = build_item_path("tools", i, is_wrapped)
                findings.append(self.create_finding(
                    message=f"Tool '{tool.get('name', 'unnamed')}' is missing inputSchema",
                    path=f"{path}.inputSchema",
                    config=config,
                    source=source,
                    suggestion="Add an inputSchema defining the expected parameters using JSON Schema format",
                ))
        
        return findings


class ToolInputSchemaProperties(Rule):
    """Validates that inputSchema has properly defined properties."""
    
    id = "tool-input-schema-properties"
    description = "Tool inputSchema should have type 'object' and defined properties"
    default_severity = Severity.WARN
    category = "tool"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        require_property_descriptions = config.options.get("require_property_descriptions", False)
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
                
            schema = tool.get("inputSchema", {})
            if not isinstance(schema, dict):
                continue
            
            path = build_item_path("tools", i, is_wrapped)
            tool_name = tool.get("name", "unnamed")
            
            # Check type is 'object'
            schema_type = schema.get("type")
            if schema_type and schema_type != "object":
                findings.append(self.create_finding(
                    message=f"Tool '{tool_name}' inputSchema type should be 'object', got '{schema_type}'",
                    path=f"{path}.inputSchema.type",
                    config=config,
                    source=source,
                ))
            
            # Check if properties are defined (warn if empty)
            properties = schema.get("properties", {})
            if schema and not properties:
                # Only warn if schema exists but has no properties
                if schema.get("type") == "object":
                    findings.append(self.create_finding(
                        message=f"Tool '{tool_name}' inputSchema has no properties defined",
                        path=f"{path}.inputSchema.properties",
                        config=config,
                        source=source,
                        suggestion="Define properties for the tool's input parameters",
                    ))
            
            # Check property descriptions if required
            if require_property_descriptions and properties:
                for prop_name, prop_schema in properties.items():
                    if isinstance(prop_schema, dict) and not prop_schema.get("description"):
                        findings.append(self.create_finding(
                            message=f"Tool '{tool_name}' property '{prop_name}' is missing description",
                            path=f"{path}.inputSchema.properties.{prop_name}.description",
                            config=config,
                            source=source,
                            suggestion=f"Add a description for the '{prop_name}' parameter",
                        ))
        
        return findings


class ToolRequiredPropertiesExist(Rule):
    """Validates that properties listed in 'required' array exist in 'properties'."""
    
    id = "tool-required-properties-exist"
    description = "Properties listed in required array must be defined in properties"
    default_severity = Severity.ERROR
    category = "tool"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
            
            schema = tool.get("inputSchema", {})
            if not isinstance(schema, dict):
                continue
            
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            if not isinstance(required, list):
                continue
            
            path = build_item_path("tools", i, is_wrapped)
            tool_name = tool.get("name", "unnamed")
            
            for req_prop in required:
                if req_prop not in properties:
                    findings.append(self.create_finding(
                        message=f"Tool '{tool_name}' requires '{req_prop}' but it's not defined in properties",
                        path=f"{path}.inputSchema.required",
                        config=config,
                        source=source,
                        suggestion=f"Add '{req_prop}' to inputSchema.properties or remove from required",
                    ))
        
        return findings


class ToolPropertyTypeDefined(Rule):
    """Validates that all properties have a type defined."""
    
    id = "tool-property-type-defined"
    description = "Every property in inputSchema should have a type defined"
    default_severity = Severity.WARN
    category = "tool"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
            
            schema = tool.get("inputSchema", {})
            if not isinstance(schema, dict):
                continue
            
            properties = schema.get("properties", {})
            path = build_item_path("tools", i, is_wrapped)
            tool_name = tool.get("name", "unnamed")
            
            for prop_name, prop_schema in properties.items():
                if isinstance(prop_schema, dict) and "type" not in prop_schema:
                    # Check if it has $ref or oneOf/anyOf/allOf (valid alternatives)
                    if not any(k in prop_schema for k in ["$ref", "oneOf", "anyOf", "allOf"]):
                        findings.append(self.create_finding(
                            message=f"Tool '{tool_name}' property '{prop_name}' has no type defined",
                            path=f"{path}.inputSchema.properties.{prop_name}",
                            config=config,
                            source=source,
                            suggestion="Add 'type' to property (string, number, boolean, object, array)",
                        ))
        
        return findings


class ToolSchemaNoEmptyObject(Rule):
    """Validates that schemas don't use empty objects without properties."""
    
    id = "tool-schema-no-empty-object"
    description = "Avoid empty object schemas without defined properties"
    default_severity = Severity.WARN
    category = "tool"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
            
            schema = tool.get("inputSchema", {})
            if not isinstance(schema, dict):
                continue
            
            path = build_item_path("tools", i, is_wrapped)
            tool_name = tool.get("name", "unnamed")
            
            # Check for empty schema {}
            if schema == {}:
                findings.append(self.create_finding(
                    message=f"Tool '{tool_name}' has an empty inputSchema",
                    path=f"{path}.inputSchema",
                    config=config,
                    source=source,
                    suggestion="Define the schema structure or remove if tool takes no parameters",
                ))
                continue
            
            # Check nested properties for empty objects
            properties = schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                if isinstance(prop_schema, dict):
                    if prop_schema == {} or prop_schema == {"type": "object"}:
                        findings.append(self.create_finding(
                            message=f"Tool '{tool_name}' property '{prop_name}' is an empty object",
                            path=f"{path}.inputSchema.properties.{prop_name}",
                            config=config,
                            source=source,
                            suggestion="Define the object's properties or use a more specific type",
                        ))
        
        return findings


class ToolEnumTypeConsistent(Rule):
    """Validates that enum values match the declared type."""
    
    id = "tool-enum-type-consistent"
    description = "Enum values must match the declared property type"
    default_severity = Severity.WARN
    category = "tool"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
            
            schema = tool.get("inputSchema", {})
            if not isinstance(schema, dict):
                continue
            
            path = build_item_path("tools", i, is_wrapped)
            tool_name = tool.get("name", "unnamed")
            
            properties = schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                if not isinstance(prop_schema, dict):
                    continue
                
                enum_values = prop_schema.get("enum", [])
                prop_type = prop_schema.get("type")
                
                if enum_values and prop_type:
                    for val in enum_values:
                        if not self._type_matches(val, prop_type):
                            findings.append(self.create_finding(
                                message=f"Tool '{tool_name}' enum value '{val}' doesn't match type '{prop_type}'",
                                path=f"{path}.inputSchema.properties.{prop_name}.enum",
                                config=config,
                                source=source,
                                suggestion=f"Ensure all enum values are of type '{prop_type}'",
                            ))
                            break  # Only report once per property
        
        return findings
    
    def _type_matches(self, value, expected_type: str) -> bool:
        """Check if a value matches the expected JSON Schema type."""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "null": type(None),
        }
        expected = type_map.get(expected_type)
        if expected:
            return isinstance(value, expected)
        return True  # Unknown types pass


class ToolEnumNoDuplicates(Rule):
    """Validates that enum values are unique."""
    
    id = "tool-enum-no-duplicates"
    description = "Enum values must be unique within a property"
    default_severity = Severity.ERROR
    category = "tool"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
            
            schema = tool.get("inputSchema", {})
            if not isinstance(schema, dict):
                continue
            
            path = build_item_path("tools", i, is_wrapped)
            tool_name = tool.get("name", "unnamed")
            
            properties = schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                if not isinstance(prop_schema, dict):
                    continue
                
                enum_values = prop_schema.get("enum", [])
                if enum_values:
                    seen = set()
                    for val in enum_values:
                        # Convert to string for hashability
                        val_key = str(val)
                        if val_key in seen:
                            findings.append(self.create_finding(
                                message=f"Tool '{tool_name}' has duplicate enum value '{val}'",
                                path=f"{path}.inputSchema.properties.{prop_name}.enum",
                                config=config,
                                source=source,
                                suggestion="Remove duplicate enum values",
                            ))
                            break
                        seen.add(val_key)
        
        return findings


class ToolAdditionalPropertiesExplicit(Rule):
    """Validates that additionalProperties is explicitly set."""
    
    id = "tool-additional-properties-explicit"
    description = "inputSchema should explicitly set additionalProperties"
    default_severity = Severity.INFO
    category = "tool"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
            
            schema = tool.get("inputSchema", {})
            if not isinstance(schema, dict) or not schema:
                continue
            
            path = build_item_path("tools", i, is_wrapped)
            tool_name = tool.get("name", "unnamed")
            
            # Only check if schema has type: object and properties
            if schema.get("type") == "object" and schema.get("properties"):
                if "additionalProperties" not in schema:
                    findings.append(self.create_finding(
                        message=f"Tool '{tool_name}' doesn't explicitly set additionalProperties",
                        path=f"{path}.inputSchema",
                        config=config,
                        source=source,
                        suggestion="Add 'additionalProperties: false' to reject unknown properties",
                    ))
        
        return findings


# =============================================================================
# Output Schema Rules (MCP 2025-11-25+)
# =============================================================================

class ToolOutputSchemaDefined(Rule):
    """Validates that tools define an outputSchema for structured results.
    
    The outputSchema field was added in MCP spec 2025-11-25 to allow tools
    to define the structure of their output in the structuredContent field.
    """
    
    id = "tool-output-schema-defined"
    description = "Tools should define an outputSchema for structured, predictable results"
    default_severity = Severity.INFO  # INFO since this is new and not widely adopted
    category = "tool"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
            
            output_schema = tool.get("outputSchema")
            if output_schema is None:
                path = build_item_path("tools", i, is_wrapped)
                findings.append(self.create_finding(
                    message=f"Tool '{tool.get('name', 'unnamed')}' has no outputSchema defined",
                    path=f"{path}.outputSchema",
                    config=config,
                    source=source,
                    suggestion="Add an outputSchema to define the structure of tool results",
                ))
        
        return findings


class ToolOutputSchemaProperties(Rule):
    """Validates that outputSchema has properly defined properties."""
    
    id = "tool-output-schema-properties"
    description = "Tool outputSchema should have type 'object' and defined properties"
    default_severity = Severity.WARN
    category = "tool"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        tools, is_wrapped = get_items(data, "tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                continue
            
            output_schema = tool.get("outputSchema")
            if not isinstance(output_schema, dict) or not output_schema:
                continue  # No outputSchema or not a dict - skip
            
            path = build_item_path("tools", i, is_wrapped)
            tool_name = tool.get("name", "unnamed")
            
            # Check type is 'object'
            schema_type = output_schema.get("type")
            if schema_type and schema_type != "object":
                findings.append(self.create_finding(
                    message=f"Tool '{tool_name}' outputSchema type should be 'object', got '{schema_type}'",
                    path=f"{path}.outputSchema.type",
                    config=config,
                    source=source,
                ))
            
            # Check if properties are defined
            properties = output_schema.get("properties", {})
            if output_schema.get("type") == "object" and not properties:
                findings.append(self.create_finding(
                    message=f"Tool '{tool_name}' outputSchema has no properties defined",
                    path=f"{path}.outputSchema.properties",
                    config=config,
                    source=source,
                    suggestion="Define properties for the tool's output structure",
                ))
        
        return findings

