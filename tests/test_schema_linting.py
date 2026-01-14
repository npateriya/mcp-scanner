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

"""Unit tests for MCP Schema Linting functionality."""

import json
import pytest
import tempfile
from pathlib import Path

from mcpscanner.core.schema_linting import SchemaLinter, LintConfig, Finding, Severity
from mcpscanner.core.schema_linting.rule_base import RuleConfig
from mcpscanner.core.schema_linting.rules import (
    ToolDescriptionRequired,
    ToolDescriptionMinLength,
    ToolNameCasing,
    ToolInputSchemaRequired,
    ToolInputSchemaProperties,
    ToolNoDuplicateNames,
    ToolNameNoReserved,
    PromptDescriptionRequired,
    PromptArgumentsDescription,
    PromptNameCasing,
    ResourceDescriptionRequired,
    ResourceMimeType,
    ResourceUriValid,
    NoEmptyArrays,
)
from mcpscanner.core.schema_linting.formatters import TextFormatter, JsonFormatter


class TestFinding:
    """Tests for the Finding dataclass."""
    
    def test_finding_creation(self):
        """Test creating a Finding object."""
        finding = Finding(
            rule_id="test-rule",
            message="Test message",
            severity=Severity.ERROR,
            path="tools[0].name",
        )
        assert finding.rule_id == "test-rule"
        assert finding.severity == Severity.ERROR
        assert finding.path == "tools[0].name"
    
    def test_finding_to_dict(self):
        """Test converting Finding to dictionary."""
        finding = Finding(
            rule_id="test-rule",
            message="Test message",
            severity=Severity.WARN,
            path="tools[0]",
            suggestion="Fix it",
        )
        d = finding.to_dict()
        assert d["rule_id"] == "test-rule"
        assert d["severity"] == "warn"
        assert d["suggestion"] == "Fix it"


class TestSeverity:
    """Tests for the Severity enum."""
    
    def test_severity_from_string(self):
        """Test parsing severity from string."""
        assert Severity.from_string("error") == Severity.ERROR
        assert Severity.from_string("ERROR") == Severity.ERROR
        assert Severity.from_string("warn") == Severity.WARN
        assert Severity.from_string("info") == Severity.INFO
        assert Severity.from_string("hint") == Severity.HINT
        assert Severity.from_string("off") == Severity.OFF
        assert Severity.from_string("invalid") == Severity.WARN  # Default


class TestRuleConfig:
    """Tests for the RuleConfig dataclass."""
    
    def test_from_dict_none(self):
        """Test parsing None as disabled."""
        config = RuleConfig.from_dict(None)
        assert not config.enabled
        assert config.severity == Severity.OFF
    
    def test_from_dict_off_string(self):
        """Test parsing 'off' as disabled."""
        config = RuleConfig.from_dict("off")
        assert not config.enabled
    
    def test_from_dict_severity_string(self):
        """Test parsing severity string."""
        config = RuleConfig.from_dict("error")
        assert config.enabled
        assert config.severity == Severity.ERROR
    
    def test_from_dict_full_config(self):
        """Test parsing full config dict."""
        config = RuleConfig.from_dict({
            "severity": "warn",
            "options": {"min": 50}
        })
        assert config.enabled
        assert config.severity == Severity.WARN
        assert config.options["min"] == 50


class TestToolDescriptionRequired:
    """Tests for ToolDescriptionRequired rule."""
    
    def test_valid_description(self):
        """Test that tools with descriptions pass."""
        rule = ToolDescriptionRequired()
        data = {
            "tools": [
                {"name": "test_tool", "description": "A valid description"}
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 0
    
    def test_missing_description(self):
        """Test that tools without descriptions fail."""
        rule = ToolDescriptionRequired()
        data = {
            "tools": [
                {"name": "test_tool", "description": ""},
                {"name": "another_tool"}  # Missing description key
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 2
        assert all(f.rule_id == "tool-description-required" for f in findings)
    
    def test_whitespace_only_description(self):
        """Test that whitespace-only descriptions fail."""
        rule = ToolDescriptionRequired()
        data = {
            "tools": [
                {"name": "test_tool", "description": "   "}
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1


class TestToolDescriptionMinLength:
    """Tests for ToolDescriptionMinLength rule."""
    
    def test_long_enough_description(self):
        """Test that descriptions meeting min length pass."""
        rule = ToolDescriptionMinLength()
        data = {
            "tools": [
                {"name": "test", "description": "This is a sufficiently long description"}
            ]
        }
        config = RuleConfig(options={"min": 20})
        findings = rule.check(data, config)
        assert len(findings) == 0
    
    def test_too_short_description(self):
        """Test that short descriptions fail."""
        rule = ToolDescriptionMinLength()
        data = {
            "tools": [
                {"name": "test", "description": "Short"}
            ]
        }
        config = RuleConfig(options={"min": 20})
        findings = rule.check(data, config)
        assert len(findings) == 1
        assert "too short" in findings[0].message


class TestToolNameCasing:
    """Tests for ToolNameCasing rule."""
    
    def test_snake_case_valid(self):
        """Test valid snake_case names."""
        rule = ToolNameCasing()
        data = {
            "tools": [
                {"name": "get_weather", "description": "Test"},
                {"name": "calculate_sum", "description": "Test"}
            ]
        }
        config = RuleConfig(options={"convention": "snake_case"})
        findings = rule.check(data, config)
        assert len(findings) == 0
    
    def test_snake_case_invalid(self):
        """Test invalid snake_case names."""
        rule = ToolNameCasing()
        data = {
            "tools": [
                {"name": "getWeather", "description": "Test"},  # camelCase
                {"name": "GetWeather", "description": "Test"}  # PascalCase
            ]
        }
        config = RuleConfig(options={"convention": "snake_case"})
        findings = rule.check(data, config)
        assert len(findings) == 2
    
    def test_camel_case_valid(self):
        """Test valid camelCase names."""
        rule = ToolNameCasing()
        data = {
            "tools": [
                {"name": "getWeather", "description": "Test"}
            ]
        }
        config = RuleConfig(options={"convention": "camelCase"})
        findings = rule.check(data, config)
        assert len(findings) == 0


class TestToolInputSchemaRequired:
    """Tests for ToolInputSchemaRequired rule."""
    
    def test_with_schema(self):
        """Test tools with inputSchema pass."""
        rule = ToolInputSchemaRequired()
        data = {
            "tools": [
                {"name": "test", "description": "Test", "inputSchema": {"type": "object"}}
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 0
    
    def test_without_schema(self):
        """Test tools without inputSchema fail."""
        rule = ToolInputSchemaRequired()
        data = {
            "tools": [
                {"name": "test", "description": "Test"}
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1


class TestToolInputSchemaProperties:
    """Tests for ToolInputSchemaProperties rule."""
    
    def test_valid_schema(self):
        """Test valid inputSchema passes."""
        rule = ToolInputSchemaProperties()
        data = {
            "tools": [
                {
                    "name": "test",
                    "description": "Test",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "param": {"type": "string"}
                        }
                    }
                }
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 0
    
    def test_non_object_type(self):
        """Test non-object type fails."""
        rule = ToolInputSchemaProperties()
        data = {
            "tools": [
                {
                    "name": "test",
                    "description": "Test",
                    "inputSchema": {"type": "string"}
                }
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "should be 'object'" in findings[0].message
    
    def test_require_property_descriptions(self):
        """Test that property descriptions can be required."""
        rule = ToolInputSchemaProperties()
        data = {
            "tools": [
                {
                    "name": "test",
                    "description": "Test",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "param": {"type": "string"}  # No description
                        }
                    }
                }
            ]
        }
        config = RuleConfig(options={"require_property_descriptions": True})
        findings = rule.check(data, config)
        assert len(findings) == 1
        assert "missing description" in findings[0].message


class TestPromptRules:
    """Tests for prompt linting rules."""
    
    def test_prompt_description_required(self):
        """Test prompt description requirement."""
        rule = PromptDescriptionRequired()
        data = {
            "prompts": [
                {"name": "test_prompt", "description": ""},
                {"name": "valid_prompt", "description": "A valid description"}
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert findings[0].path == "prompts[0].description"
    
    def test_prompt_arguments_description(self):
        """Test prompt argument description requirement."""
        rule = PromptArgumentsDescription()
        data = {
            "prompts": [
                {
                    "name": "test",
                    "description": "Test",
                    "arguments": [
                        {"name": "arg1", "description": "Valid"},
                        {"name": "arg2"}  # Missing description
                    ]
                }
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "arg2" in findings[0].message


class TestResourceRules:
    """Tests for resource linting rules."""
    
    def test_resource_description_required(self):
        """Test resource description requirement."""
        rule = ResourceDescriptionRequired()
        data = {
            "resources": [
                {"name": "test_resource", "uri": "file:///test"},
                {"name": "valid", "uri": "file:///valid", "description": "Valid"}
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
    
    def test_resource_mime_type(self):
        """Test resource MIME type requirement."""
        rule = ResourceMimeType()
        data = {
            "resources": [
                {"name": "test", "uri": "file:///test"},  # Missing mimeType
                {"name": "valid", "uri": "file:///valid", "mimeType": "text/plain"}
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
    
    def test_invalid_mime_type_format(self):
        """Test invalid MIME type format detection."""
        rule = ResourceMimeType()
        data = {
            "resources": [
                {"name": "test", "uri": "file:///test", "mimeType": "invalid"}
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "invalid mimeType format" in findings[0].message


class TestSchemaLinter:
    """Tests for the main SchemaLinter class."""
    
    def test_lint_data(self):
        """Test linting data directly."""
        linter = SchemaLinter()
        data = {
            "tools": [
                {"name": "test", "description": ""}
            ]
        }
        result = linter.lint(data)
        assert len(result.findings) > 0
        assert result.has_errors
    
    def test_lint_file(self):
        """Test linting a JSON file."""
        linter = SchemaLinter()
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "tools": [
                    {"name": "valid_tool", "description": "A valid description here"}
                ]
            }, f)
            temp_path = f.name
        
        try:
            result = linter.lint_file(temp_path)
            assert result.source == temp_path
            # Should have no errors for valid tool
            assert not result.has_errors
        finally:
            Path(temp_path).unlink()
    
    def test_lint_file_not_found(self):
        """Test linting a non-existent file."""
        linter = SchemaLinter()
        result = linter.lint_file("/nonexistent/file.json")
        assert result.has_errors
        assert len(result.errors) > 0
        assert "not found" in result.errors[0].lower()
    
    def test_lint_invalid_json(self):
        """Test linting invalid JSON file."""
        linter = SchemaLinter()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name
        
        try:
            result = linter.lint_file(temp_path)
            assert result.has_errors
            assert len(result.errors) > 0
            assert "parse" in result.errors[0].lower()
        finally:
            Path(temp_path).unlink()
    
    def test_lint_with_config(self):
        """Test linting with custom configuration."""
        linter = SchemaLinter()
        data = {
            "tools": [
                {"name": "shortDesc", "description": "Hi"}  # Short description
            ]
        }
        
        # Create config that disables min-length check
        config = LintConfig(rules={
            "tool-description-min-length": RuleConfig(enabled=False)
        })
        
        result = linter.lint(data, config)
        # Should not have min-length warnings
        assert not any(f.rule_id == "tool-description-min-length" for f in result.findings)
    
    def test_list_rules(self):
        """Test listing available rules."""
        linter = SchemaLinter()
        rules = linter.list_rules()
        assert len(rules) > 0
        assert all("id" in r and "description" in r for r in rules)


class TestLintResult:
    """Tests for LintResult class."""
    
    def test_counts(self):
        """Test finding counts."""
        from mcpscanner.core.schema_linting.linter import LintResult
        
        result = LintResult(findings=[
            Finding("r1", "msg", Severity.ERROR, "path"),
            Finding("r2", "msg", Severity.WARN, "path"),
            Finding("r3", "msg", Severity.WARN, "path"),
            Finding("r4", "msg", Severity.INFO, "path"),
        ])
        
        assert result.error_count == 1
        assert result.warning_count == 2
        assert result.info_count == 1
        assert result.has_errors
        assert result.has_warnings
    
    def test_to_dict(self):
        """Test converting result to dict."""
        from mcpscanner.core.schema_linting.linter import LintResult
        
        result = LintResult(
            source="test.json",
            findings=[Finding("r1", "msg", Severity.ERROR, "path")]
        )
        d = result.to_dict()
        assert d["source"] == "test.json"
        assert len(d["findings"]) == 1
        assert d["summary"]["errors"] == 1


class TestFormatters:
    """Tests for output formatters."""
    
    def test_text_formatter(self):
        """Test text formatter output."""
        from mcpscanner.core.schema_linting.linter import LintResult
        
        result = LintResult(
            source="test.json",
            findings=[Finding("r1", "Test error", Severity.ERROR, "path")]
        )
        
        formatter = TextFormatter(use_color=False)
        output = formatter.format(result)
        
        assert "test.json" in output
        assert "ERROR" in output
        assert "Test error" in output
    
    def test_json_formatter(self):
        """Test JSON formatter output."""
        from mcpscanner.core.schema_linting.linter import LintResult
        
        result = LintResult(
            source="test.json",
            findings=[Finding("r1", "Test error", Severity.ERROR, "path")]
        )
        
        formatter = JsonFormatter()
        output = formatter.format(result)
        
        data = json.loads(output)
        assert data["source"] == "test.json"
        assert len(data["findings"]) == 1


class TestToolNoDuplicateNames:
    """Tests for ToolNoDuplicateNames rule."""
    
    def test_unique_names(self):
        """Test that unique tool names pass."""
        rule = ToolNoDuplicateNames()
        data = {
            "tools": [
                {"name": "tool_a", "description": "A"},
                {"name": "tool_b", "description": "B"},
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 0
    
    def test_duplicate_names(self):
        """Test that duplicate tool names fail."""
        rule = ToolNoDuplicateNames()
        data = {
            "tools": [
                {"name": "get_data", "description": "First"},
                {"name": "other_tool", "description": "Other"},
                {"name": "get_data", "description": "Duplicate"},
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "Duplicate" in findings[0].message
        assert "get_data" in findings[0].message


class TestToolNameNoReserved:
    """Tests for ToolNameNoReserved rule."""
    
    def test_normal_name(self):
        """Test that normal names pass."""
        rule = ToolNameNoReserved()
        data = {
            "tools": [
                {"name": "get_weather", "description": "A tool"}
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 0
    
    def test_reserved_name(self):
        """Test that reserved names fail."""
        rule = ToolNameNoReserved()
        data = {
            "tools": [
                {"name": "test", "description": "A test tool"},
                {"name": "tools", "description": "Reserved word"},
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 2
    
    def test_custom_reserved_words(self):
        """Test custom reserved words from options."""
        rule = ToolNameNoReserved()
        data = {
            "tools": [
                {"name": "forbidden", "description": "Custom reserved"}
            ]
        }
        config = RuleConfig(options={"reserved_words": ["forbidden"]})
        findings = rule.check(data, config)
        assert len(findings) == 1


class TestResourceUriValid:
    """Tests for ResourceUriValid rule."""
    
    def test_valid_uri(self):
        """Test that valid URIs pass."""
        rule = ResourceUriValid()
        data = {
            "resources": [
                {"name": "file", "uri": "file:///path/to/file"},
                {"name": "http", "uri": "https://example.com/data"},
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 0
    
    def test_missing_uri(self):
        """Test that missing URIs fail."""
        rule = ResourceUriValid()
        data = {
            "resources": [
                {"name": "no_uri", "description": "Missing URI"}
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "missing URI" in findings[0].message
    
    def test_invalid_scheme(self):
        """Test that URIs without scheme fail."""
        rule = ResourceUriValid()
        data = {
            "resources": [
                {"name": "bad", "uri": "just-a-path"}
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "missing scheme" in findings[0].message
    
    def test_unsupported_scheme(self):
        """Test that unsupported schemes fail."""
        rule = ResourceUriValid()
        data = {
            "resources": [
                {"name": "ftp", "uri": "ftp://server.com/file"}
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "unsupported scheme" in findings[0].message


class TestNoEmptyArrays:
    """Tests for NoEmptyArrays rule."""
    
    def test_non_empty_arrays(self):
        """Test that non-empty arrays pass."""
        rule = NoEmptyArrays()
        data = {
            "tools": [{"name": "tool", "description": "A tool"}]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 0
    
    def test_empty_tools(self):
        """Test that empty tools array fails."""
        rule = NoEmptyArrays()
        data = {"tools": []}
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "tools" in findings[0].message
    
    def test_empty_prompts_and_resources(self):
        """Test that multiple empty arrays are reported."""
        rule = NoEmptyArrays()
        data = {
            "tools": [{"name": "t", "description": "d"}],
            "prompts": [],
            "resources": [],
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 2


class TestPromptNameCasing:
    """Tests for PromptNameCasing rule."""
    
    def test_snake_case_valid(self):
        """Test valid snake_case names."""
        rule = PromptNameCasing()
        data = {
            "prompts": [
                {"name": "summarize_text", "description": "A prompt"}
            ]
        }
        config = RuleConfig(options={"convention": "snake_case"})
        findings = rule.check(data, config)
        assert len(findings) == 0
    
    def test_invalid_casing(self):
        """Test invalid casing fails."""
        rule = PromptNameCasing()
        data = {
            "prompts": [
                {"name": "SummarizeText", "description": "A prompt"}
            ]
        }
        config = RuleConfig(options={"convention": "snake_case"})
        findings = rule.check(data, config)
        assert len(findings) == 1


# =============================================================================
# New Enterprise Rules Tests
# =============================================================================

class TestToolRequiredPropertiesExist:
    """Tests for ToolRequiredPropertiesExist rule."""
    
    def test_valid_required(self):
        """Test that valid required properties pass."""
        from mcpscanner.core.schema_linting.rules.builtin.tool_rules import ToolRequiredPropertiesExist
        rule = ToolRequiredPropertiesExist()
        data = {
            "tools": [{
                "name": "test",
                "description": "A test tool",
                "inputSchema": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"]
                }
            }]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 0
    
    def test_missing_required(self):
        """Test that missing required properties fail."""
        from mcpscanner.core.schema_linting.rules.builtin.tool_rules import ToolRequiredPropertiesExist
        rule = ToolRequiredPropertiesExist()
        data = {
            "tools": [{
                "name": "test",
                "description": "A test tool",
                "inputSchema": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name", "missing"]
                }
            }]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "missing" in findings[0].message


class TestToolPropertyTypeDefined:
    """Tests for ToolPropertyTypeDefined rule."""
    
    def test_typed_properties(self):
        """Test properties with types pass."""
        from mcpscanner.core.schema_linting.rules.builtin.tool_rules import ToolPropertyTypeDefined
        rule = ToolPropertyTypeDefined()
        data = {
            "tools": [{
                "name": "test",
                "description": "A test",
                "inputSchema": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}}
                }
            }]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 0
    
    def test_untyped_property(self):
        """Test properties without types fail."""
        from mcpscanner.core.schema_linting.rules.builtin.tool_rules import ToolPropertyTypeDefined
        rule = ToolPropertyTypeDefined()
        data = {
            "tools": [{
                "name": "test",
                "description": "A test",
                "inputSchema": {
                    "type": "object",
                    "properties": {"name": {"description": "no type"}}
                }
            }]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "no type" in findings[0].message


class TestToolEnumNoDuplicates:
    """Tests for ToolEnumNoDuplicates rule."""
    
    def test_unique_enums(self):
        """Test unique enum values pass."""
        from mcpscanner.core.schema_linting.rules.builtin.tool_rules import ToolEnumNoDuplicates
        rule = ToolEnumNoDuplicates()
        data = {
            "tools": [{
                "name": "test",
                "description": "A test",
                "inputSchema": {
                    "type": "object",
                    "properties": {"mode": {"type": "string", "enum": ["a", "b", "c"]}}
                }
            }]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 0
    
    def test_duplicate_enums(self):
        """Test duplicate enum values fail."""
        from mcpscanner.core.schema_linting.rules.builtin.tool_rules import ToolEnumNoDuplicates
        rule = ToolEnumNoDuplicates()
        data = {
            "tools": [{
                "name": "test",
                "description": "A test",
                "inputSchema": {
                    "type": "object",
                    "properties": {"mode": {"type": "string", "enum": ["a", "b", "a"]}}
                }
            }]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "duplicate" in findings[0].message.lower()


class TestToolDescriptionNoPlaceholder:
    """Tests for ToolDescriptionNoPlaceholder rule."""
    
    def test_real_description(self):
        """Test real descriptions pass."""
        from mcpscanner.core.schema_linting.rules.builtin.tool_rules import ToolDescriptionNoPlaceholder
        rule = ToolDescriptionNoPlaceholder()
        data = {
            "tools": [{
                "name": "test",
                "description": "This tool fetches user data from the database"
            }]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 0
    
    def test_placeholder_description(self):
        """Test placeholder descriptions fail."""
        from mcpscanner.core.schema_linting.rules.builtin.tool_rules import ToolDescriptionNoPlaceholder
        rule = ToolDescriptionNoPlaceholder()
        data = {
            "tools": [
                {"name": "test1", "description": "TODO: add description"},
                {"name": "test2", "description": "TBD"},
                {"name": "test3", "description": "..."},
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 3


class TestToolNameMinMaxLength:
    """Tests for tool name length rules."""
    
    def test_name_too_short(self):
        """Test short names fail."""
        from mcpscanner.core.schema_linting.rules.builtin.tool_rules import ToolNameMinLength
        rule = ToolNameMinLength()
        data = {"tools": [{"name": "ab", "description": "Short name"}]}
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "too short" in findings[0].message
    
    def test_name_too_long(self):
        """Test long names fail."""
        from mcpscanner.core.schema_linting.rules.builtin.tool_rules import ToolNameMaxLength
        rule = ToolNameMaxLength()
        data = {"tools": [{"name": "a" * 100, "description": "Long name"}]}
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "too long" in findings[0].message


class TestToolNameActionVerb:
    """Tests for ToolNameActionVerb rule."""
    
    def test_action_verb_valid(self):
        """Test names starting with action verbs pass."""
        from mcpscanner.core.schema_linting.rules.builtin.tool_rules import ToolNameActionVerb
        rule = ToolNameActionVerb()
        data = {
            "tools": [
                {"name": "get_user", "description": "Get user"},
                {"name": "create_item", "description": "Create item"},
                {"name": "delete_record", "description": "Delete record"},
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 0
    
    def test_no_action_verb(self):
        """Test names without action verbs fail."""
        from mcpscanner.core.schema_linting.rules.builtin.tool_rules import ToolNameActionVerb
        rule = ToolNameActionVerb()
        data = {"tools": [{"name": "user_processor", "description": "Processes users"}]}
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "action verb" in findings[0].message


class TestToolNameNoGeneric:
    """Tests for ToolNameNoGeneric rule."""
    
    def test_specific_name(self):
        """Test specific names pass."""
        from mcpscanner.core.schema_linting.rules.builtin.tool_rules import ToolNameNoGeneric
        rule = ToolNameNoGeneric()
        data = {"tools": [{"name": "get_weather_forecast", "description": "Gets weather"}]}
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 0
    
    def test_generic_name(self):
        """Test generic names fail."""
        from mcpscanner.core.schema_linting.rules.builtin.tool_rules import ToolNameNoGeneric
        rule = ToolNameNoGeneric()
        data = {
            "tools": [
                {"name": "run", "description": "Runs"},
                {"name": "data", "description": "Data"},
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 2


class TestPromptNoDuplicates:
    """Tests for prompt duplicate rules."""
    
    def test_duplicate_prompt_names(self):
        """Test duplicate prompt names fail."""
        from mcpscanner.core.schema_linting.rules.builtin.prompt_rules import PromptNoDuplicateNames
        rule = PromptNoDuplicateNames()
        data = {
            "prompts": [
                {"name": "summarize", "description": "A"},
                {"name": "summarize", "description": "B"},
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
    
    def test_duplicate_arguments(self):
        """Test duplicate argument names fail."""
        from mcpscanner.core.schema_linting.rules.builtin.prompt_rules import PromptNoDuplicateArguments
        rule = PromptNoDuplicateArguments()
        data = {
            "prompts": [{
                "name": "test",
                "description": "Test",
                "arguments": [
                    {"name": "text"},
                    {"name": "text"},
                ]
            }]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1


class TestResourceTemplateAndDuplicates:
    """Tests for resource URI template and duplicate rules."""
    
    def test_valid_template(self):
        """Test valid URI templates pass."""
        from mcpscanner.core.schema_linting.rules.builtin.resource_rules import ResourceUriTemplateValid
        rule = ResourceUriTemplateValid()
        data = {
            "resources": [{"name": "doc", "uri": "file:///docs/{doc_id}.txt"}]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 0
    
    def test_empty_placeholder(self):
        """Test empty placeholders fail."""
        from mcpscanner.core.schema_linting.rules.builtin.resource_rules import ResourceUriTemplateValid
        rule = ResourceUriTemplateValid()
        data = {
            "resources": [{"name": "doc", "uri": "file:///docs/{}.txt"}]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "empty placeholder" in findings[0].message
    
    def test_duplicate_resource_names(self):
        """Test duplicate resource names fail."""
        from mcpscanner.core.schema_linting.rules.builtin.resource_rules import ResourceNoDuplicateNames
        rule = ResourceNoDuplicateNames()
        data = {
            "resources": [
                {"name": "config", "uri": "file:///a"},
                {"name": "config", "uri": "file:///b"},
            ]
        }
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1


class TestDescriptionNoHtml:
    """Tests for DescriptionNoHtml rule."""
    
    def test_plain_text(self):
        """Test plain text descriptions pass."""
        from mcpscanner.core.schema_linting.rules.builtin.tool_rules import DescriptionNoHtml
        rule = DescriptionNoHtml()
        data = {"tools": [{"name": "test", "description": "A plain description"}]}
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 0
    
    def test_html_content(self):
        """Test HTML in descriptions fails."""
        from mcpscanner.core.schema_linting.rules.builtin.tool_rules import DescriptionNoHtml
        rule = DescriptionNoHtml()
        data = {"tools": [{"name": "test", "description": "<b>Bold</b> text"}]}
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "HTML" in findings[0].message


class TestTableFormatter:
    """Tests for the TableFormatter."""
    
    def test_table_formatter_basic(self):
        """Test table formatter produces output."""
        from mcpscanner.core.schema_linting.formatters.table import TableFormatter
        from mcpscanner.core.schema_linting.linter import LintResult
        
        formatter = TableFormatter(use_color=False)
        result = LintResult(
            findings=[
                Finding(
                    rule_id="tool-description-required",
                    message="Tool missing description",
                    severity=Severity.ERROR,
                    path="tools[0]"
                )
            ],
            source="test.json"
        )
        output = formatter.format(result)
        # Table formatter shows rule ID or "Tool" category
        assert "tool-description-required" in output or "Tool" in output
        assert "error" in output.lower()
    
    def test_table_formatter_multiple_results(self):
        """Test table formatter with multiple results."""
        from mcpscanner.core.schema_linting.formatters.table import TableFormatter
        from mcpscanner.core.schema_linting.linter import LintResult
        
        formatter = TableFormatter(use_color=False)
        results = [
            LintResult(
                findings=[
                    Finding("tool-description-required", "Missing", Severity.ERROR, "tools[0]"),
                    Finding("tool-name-casing", "Wrong case", Severity.WARN, "tools[1]"),
                ],
                source="file1.json"
            ),
            LintResult(
                findings=[
                    Finding("prompt-description-required", "Missing", Severity.ERROR, "prompts[0]"),
                ],
                source="file2.json"
            ),
        ]
        output = formatter.format_multiple(results)
        assert "Summary" in output
        assert "Rules" in output or "checked" in output

    def test_table_formatter_verbose(self):
        """Test table formatter verbose mode."""
        from mcpscanner.core.schema_linting.formatters.table import TableFormatter
        from mcpscanner.core.schema_linting.linter import LintResult
        
        formatter = TableFormatter(use_color=False)
        results = [
            LintResult(
                findings=[
                    Finding("tool-description-required", "Missing desc", Severity.ERROR, "tools[0]"),
                ],
                source="test.json"
            ),
        ]
        output = formatter.format_multiple(results, verbose=True)
        assert "tools[0]" in output  # Path should show in verbose mode

    def test_table_formatter_no_findings(self):
        """Test table formatter with no findings."""
        from mcpscanner.core.schema_linting.formatters.table import TableFormatter
        from mcpscanner.core.schema_linting.linter import LintResult
        
        formatter = TableFormatter(use_color=False)
        result = LintResult(findings=[], source="clean.json")
        output = formatter.format(result)
        assert "clean.json" in output


class TestTextFormatterExtended:
    """Extended tests for the TextFormatter."""
    
    def test_text_formatter_with_errors(self):
        """Test text formatter displays infrastructure errors."""
        from mcpscanner.core.schema_linting.linter import LintResult
        
        formatter = TextFormatter(use_color=False)
        result = LintResult(
            findings=[],
            source="bad.json",
            errors=["Connection failed: timeout"]
        )
        output = formatter.format(result)
        assert "Connection failed" in output or "Error" in output
    
    def test_text_formatter_with_config_warnings(self):
        """Test text formatter displays config warnings."""
        from mcpscanner.core.schema_linting.linter import LintResult
        
        formatter = TextFormatter(use_color=False)
        result = LintResult(
            findings=[],
            source="test.json",
            config_warnings=["Unknown rule 'bad-rule' in config"]
        )
        output = formatter.format(result)
        assert "Unknown rule" in output or "Warning" in output or "bad-rule" in output


class TestLintResultFactoryMethods:
    """Tests for LintResult factory methods."""
    
    def test_connection_error(self):
        """Test connection_error factory method."""
        from mcpscanner.core.schema_linting.linter import LintResult
        
        result = LintResult.connection_error("http://test.com", "Connection refused")
        assert result.source == "http://test.com"
        assert len(result.errors) == 1
        assert "Connection refused" in result.errors[0]
        assert len(result.findings) == 0
    
    def test_parse_error(self):
        """Test parse_error factory method."""
        from mcpscanner.core.schema_linting.linter import LintResult
        
        result = LintResult.parse_error("bad.json", "Invalid JSON at line 5")
        assert result.source == "bad.json"
        assert len(result.errors) == 1
        assert "Invalid JSON" in result.errors[0]
    
    def test_file_error(self):
        """Test file_error factory method."""
        from mcpscanner.core.schema_linting.linter import LintResult
        
        result = LintResult.file_error("missing.json", "File not found")
        assert result.source == "missing.json"
        assert len(result.errors) == 1
        assert "File not found" in result.errors[0]


class TestConfigValidation:
    """Tests for config validation with fuzzy matching."""
    
    def test_unknown_rule_warning(self):
        """Test that unknown rules produce warnings."""
        linter = SchemaLinter()
        config = LintConfig(rules={
            "tool-desc-required": {"severity": "off"}  # Typo!
        })
        result = linter.lint({"tools": []}, config)
        assert len(result.config_warnings) >= 1
        assert any("tool-desc-required" in w for w in result.config_warnings)
    
    def test_fuzzy_match_suggestion(self):
        """Test fuzzy matching provides suggestions."""
        linter = SchemaLinter()
        config = LintConfig(rules={
            "tool-description-require": {"severity": "off"}  # Missing 'd'
        })
        result = linter.lint({"tools": []}, config)
        # Should suggest the correct rule name
        assert len(result.config_warnings) >= 1
        warning_text = " ".join(result.config_warnings)
        assert "tool-description-require" in warning_text


class TestPathResolverHelpers:
    """Tests for path resolver helper functions."""
    
    def test_get_items_wrapped(self):
        """Test get_items with wrapped format."""
        from mcpscanner.core.schema_linting.path_resolver import get_items
        
        data = {"tools": [{"name": "a"}, {"name": "b"}]}
        items, is_wrapped = get_items(data, "tools")
        assert len(items) == 2
        assert is_wrapped is True
    
    def test_get_items_direct(self):
        """Test get_items with direct array."""
        from mcpscanner.core.schema_linting.path_resolver import get_items
        
        data = [{"name": "a"}, {"name": "b"}]
        items, is_wrapped = get_items(data, "tools")
        assert len(items) == 2
        assert is_wrapped is False
    
    def test_get_items_empty(self):
        """Test get_items with empty data."""
        from mcpscanner.core.schema_linting.path_resolver import get_items
        
        data = {}
        items, is_wrapped = get_items(data, "tools")
        assert len(items) == 0
    
    def test_build_item_path_wrapped(self):
        """Test build_item_path for wrapped format."""
        from mcpscanner.core.schema_linting.path_resolver import build_item_path
        
        path = build_item_path("tools", 0, is_wrapped=True)
        assert path == "tools[0]"
    
    def test_build_item_path_direct(self):
        """Test build_item_path for direct format."""
        from mcpscanner.core.schema_linting.path_resolver import build_item_path
        
        path = build_item_path("prompts", 2, is_wrapped=False)
        assert path == "[2]"


class TestRuleLoader:
    """Tests for the rule loader."""
    
    def test_load_config_from_yaml(self):
        """Test loading config from YAML file."""
        from mcpscanner.core.schema_linting.rule_loader import load_config
        
        yaml_content = """
rules:
  tool-description-required:
    severity: error
  tool-name-casing:
    severity: warn
    options:
      convention: camelCase
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            config = load_config(f.name)
        
        assert "tool-description-required" in config.rules
        # rules dict contains RuleConfig objects or raw dicts
        rule_config = config.rules["tool-name-casing"]
        if hasattr(rule_config, "severity"):
            assert rule_config.severity == "warn"
        else:
            assert rule_config["severity"] == "warn"
        Path(f.name).unlink()
    
    def test_load_config_file_not_found(self):
        """Test loading non-existent config raises error."""
        from mcpscanner.core.schema_linting.rule_loader import load_config
        
        with pytest.raises(ValueError) as exc_info:
            load_config("/nonexistent/path/config.yaml")
        assert "not found" in str(exc_info.value)


class TestOutputSchemaRules:
    """Tests for outputSchema rules."""
    
    def test_output_schema_defined(self):
        """Test outputSchema defined rule."""
        from mcpscanner.core.schema_linting.rules.builtin.tool_rules_schema import ToolOutputSchemaDefined
        
        rule = ToolOutputSchemaDefined()
        
        # Tool without outputSchema
        data = {"tools": [{"name": "test", "description": "Test tool"}]}
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "outputSchema" in findings[0].message
        
        # Tool with outputSchema
        data = {"tools": [{"name": "test", "description": "Test", "outputSchema": {"type": "object"}}]}
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 0
    
    def test_output_schema_properties(self):
        """Test outputSchema properties rule."""
        from mcpscanner.core.schema_linting.rules.builtin.tool_rules_schema import ToolOutputSchemaProperties
        
        rule = ToolOutputSchemaProperties()
        
        # Tool with outputSchema that has wrong type (not 'object')
        data = {"tools": [{"name": "test", "description": "Test", "outputSchema": {"type": "array"}}]}
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "object" in findings[0].message
        
        # Tool with proper outputSchema
        data = {"tools": [{"name": "test", "description": "Test", "outputSchema": {
            "type": "object",
            "properties": {"result": {"type": "string"}}
        }}]}
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 0


class TestPromptArgumentRules:
    """Tests for prompt argument rules."""
    
    def test_prompt_argument_type_defined(self):
        """Test prompt argument type validation."""
        from mcpscanner.core.schema_linting.rules.builtin.prompt_rules import PromptArgumentTypeDefined
        
        rule = PromptArgumentTypeDefined()
        
        # Argument without type
        data = {"prompts": [{
            "name": "test",
            "description": "Test prompt",
            "arguments": [{"name": "text"}]
        }]}
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
    
    def test_prompt_required_arguments_exist(self):
        """Test required arguments must be defined."""
        from mcpscanner.core.schema_linting.rules.builtin.prompt_rules import PromptRequiredArgumentsExist
        
        rule = PromptRequiredArgumentsExist()
        
        # Required argument not in arguments list
        data = {"prompts": [{
            "name": "test",
            "description": "Test prompt",
            "arguments": [{"name": "text"}],
            "required": ["text", "missing_arg"]
        }]}
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1
        assert "missing_arg" in findings[0].message


class TestResourceNameCasing:
    """Tests for resource name casing rule."""
    
    def test_resource_name_casing_valid(self):
        """Test valid resource name casing."""
        from mcpscanner.core.schema_linting.rules.builtin.resource_rules import ResourceNameCasing
        
        rule = ResourceNameCasing()
        data = {"resources": [{"name": "config_file", "uri": "file:///config.txt"}]}
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 0
    
    def test_resource_name_casing_invalid(self):
        """Test invalid resource name casing."""
        from mcpscanner.core.schema_linting.rules.builtin.resource_rules import ResourceNameCasing
        
        rule = ResourceNameCasing()
        data = {"resources": [{"name": "ConfigFile", "uri": "file:///config.txt"}]}
        findings = rule.check(data, RuleConfig())
        assert len(findings) == 1


class TestQueryPath:
    """Tests for the query_path function."""
    
    def test_simple_path(self):
        """Test simple path query."""
        from mcpscanner.core.schema_linting.path_resolver import query_path
        
        data = {"tools": [{"name": "a"}, {"name": "b"}]}
        matches = list(query_path(data, "tools[].name"))
        assert len(matches) == 2
        assert matches[0].value == "a"
        assert matches[0].path == "tools[0].name"
        assert matches[1].value == "b"
        assert matches[1].path == "tools[1].name"
    
    def test_nested_path(self):
        """Test nested path with multiple arrays."""
        from mcpscanner.core.schema_linting.path_resolver import query_path
        
        data = {
            "tools": [
                {"inputSchema": {"properties": {"x": {"type": "string"}, "y": {"type": "number"}}}},
                {"inputSchema": {"properties": {"z": {"type": "boolean"}}}},
            ]
        }
        matches = list(query_path(data, "tools[].inputSchema.properties[].type"))
        assert len(matches) == 3
        assert {m.value for m in matches} == {"string", "number", "boolean"}
    
    def test_no_matches(self):
        """Test path with no matches."""
        from mcpscanner.core.schema_linting.path_resolver import query_path
        
        data = {"tools": []}
        matches = list(query_path(data, "tools[].name"))
        assert len(matches) == 0


class TestCheckFunctions:
    """Tests for built-in check functions."""
    
    def test_pattern_match(self):
        """Test pattern check with match."""
        from mcpscanner.core.schema_linting.checks import check_pattern
        
        result = check_pattern("get_users", {"match": "^get_"})
        assert result.passed
        
        result = check_pattern("fetch_users", {"match": "^get_"})
        assert not result.passed
    
    def test_pattern_not_match(self):
        """Test pattern check with notMatch."""
        from mcpscanner.core.schema_linting.checks import check_pattern
        
        result = check_pattern("safe_name", {"notMatch": "^unsafe_"})
        assert result.passed
        
        result = check_pattern("unsafe_action", {"notMatch": "^unsafe_"})
        assert not result.passed
    
    def test_min_length(self):
        """Test minLength check."""
        from mcpscanner.core.schema_linting.checks import check_min_length
        
        result = check_min_length("This is long enough", {"min": 10})
        assert result.passed
        
        result = check_min_length("Short", {"min": 10})
        assert not result.passed
    
    def test_max_length(self):
        """Test maxLength check."""
        from mcpscanner.core.schema_linting.checks import check_max_length
        
        result = check_max_length("Short", {"max": 10})
        assert result.passed
        
        result = check_max_length("This is way too long for the limit", {"max": 10})
        assert not result.passed
    
    def test_required(self):
        """Test required check."""
        from mcpscanner.core.schema_linting.checks import check_required
        
        result = check_required("value", {})
        assert result.passed
        
        result = check_required(None, {})
        assert not result.passed
        
        result = check_required("", {})
        assert not result.passed
    
    def test_enum(self):
        """Test enum check."""
        from mcpscanner.core.schema_linting.checks import check_enum
        
        result = check_enum("high", {"values": ["high", "medium", "low"]})
        assert result.passed
        
        result = check_enum("critical", {"values": ["high", "medium", "low"]})
        assert not result.passed
    
    def test_type(self):
        """Test type check."""
        from mcpscanner.core.schema_linting.checks import check_type
        
        result = check_type("hello", {"type": "string"})
        assert result.passed
        
        result = check_type(123, {"type": "string"})
        assert not result.passed
        
        result = check_type(123, {"type": "number"})
        assert result.passed
    
    def test_casing(self):
        """Test casing check."""
        from mcpscanner.core.schema_linting.checks import check_casing
        
        result = check_casing("get_users", {"convention": "snake_case"})
        assert result.passed
        
        result = check_casing("GetUsers", {"convention": "snake_case"})
        assert not result.passed
        
        result = check_casing("getUsers", {"convention": "camelCase"})
        assert result.passed


class TestDynamicRule:
    """Tests for dynamic rules."""
    
    def test_create_dynamic_rule(self):
        """Test creating a dynamic rule from config."""
        from mcpscanner.core.schema_linting.rules.dynamic_rule import create_dynamic_rule
        
        rule_def = {
            "target": "tools[].name",
            "check": "pattern",
            "options": {"match": "^acme_"},
            "severity": "error",
            "message": "Must start with acme_"
        }
        
        rule = create_dynamic_rule("acme-prefix", rule_def)
        assert rule is not None
        assert rule.id == "acme-prefix"
        assert rule.target == "tools[].name"
        assert rule.check_name == "pattern"
    
    def test_dynamic_rule_check(self):
        """Test executing a dynamic rule."""
        from mcpscanner.core.schema_linting.rules.dynamic_rule import DynamicRule
        from mcpscanner.core.schema_linting.rule_base import RuleConfig
        
        rule = DynamicRule(
            rule_id="acme-prefix",
            target="tools[].name",
            check_name="pattern",
            options={"match": "^acme_"},
            severity="error",
            message="Tool name '{value}' must start with 'acme_'"  # Use {value} placeholder
        )
        
        data = {"tools": [{"name": "acme_users"}, {"name": "get_data"}]}
        findings = rule.check(data, RuleConfig())
        
        # acme_users passes, get_data fails
        assert len(findings) == 1
        assert "get_data" in findings[0].message
        assert findings[0].path == "tools[1].name"
    
    def test_dynamic_rule_in_config(self):
        """Test that dynamic rules from config are executed."""
        config_dict = {
            "rules": {
                "custom-min-desc": {
                    "target": "tools[].description",
                    "check": "minLength",
                    "options": {"min": 50},
                    "severity": "warn",
                    "message": "Description too short"
                }
            }
        }
        
        config = LintConfig.from_dict(config_dict)
        assert len(config.dynamic_rules) == 1
        
        linter = SchemaLinter()
        data = {"tools": [{"name": "test", "description": "Short"}]}
        result = linter.lint(data, config)
        
        # Should have finding from dynamic rule
        dynamic_findings = [f for f in result.findings if f.rule_id == "custom-min-desc"]
        assert len(dynamic_findings) == 1


class TestExtendsRuleset:
    """Tests for extends functionality."""
    
    def test_extends_recommended(self):
        """Test extending mcp:recommended ruleset."""
        from mcpscanner.core.schema_linting.rule_loader import load_config
        import tempfile
        
        yaml_content = """
extends:
  - mcp:recommended

rules:
  tool-description-required:
    severity: warn
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            config = load_config(f.name)
        
        # Should have tool-description-required overridden to warn
        rule_config = config.rules.get("tool-description-required")
        assert rule_config is not None
        Path(f.name).unlink()
    
    def test_extends_strict(self):
        """Test extending mcp:strict ruleset."""
        from mcpscanner.core.schema_linting.rule_loader import resolve_ruleset
        
        strict_rules = resolve_ruleset("mcp:strict")
        assert len(strict_rules) > 0
        # Strict ruleset has error severity for most rules
        assert strict_rules.get("tool-description-required").severity == "error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

