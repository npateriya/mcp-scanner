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

"""Built-in linting rules for MCP Resource definitions.

These rules validate resource definitions for:
- Required fields (name, description)
- MIME type specification
- URI format
"""

import re
from urllib.parse import urlparse

from ...rule_base import Rule, RuleConfig, Finding, Severity
from ...path_resolver import get_items, build_item_path


def _get_resource_items(data: dict | list) -> tuple[list[dict], bool]:
    """Extract resource items, handling the 'uri' identifier case."""
    if isinstance(data, dict):
        if "resources" in data:
            items = data["resources"]
            if isinstance(items, list):
                return items, True
            return [], True
        # Check if data itself is a single resource (has 'name' or 'uri')
        if "name" in data or "uri" in data:
            return [data], False
        return [], False
    elif isinstance(data, list):
        return data, False
    return [], False


class ResourceDescriptionRequired(Rule):
    """Validates that all resources have a non-empty description."""
    
    id = "resource-description-required"
    description = "Resources must have a non-empty description field"
    default_severity = Severity.WARN
    category = "resource"
    docs_url = "https://github.com/cisco-ai-defense/mcp-scanner/blob/main/docs/design/mcp-schema-linter-design.md#built-in-rules"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        resources, is_wrapped = _get_resource_items(data)
        
        for i, resource in enumerate(resources):
            if not isinstance(resource, dict):
                continue
                
            desc = resource.get("description", "")
            if not desc or (isinstance(desc, str) and not desc.strip()):
                path = build_item_path("resources", i, is_wrapped)
                # Use 'name' or 'uri' as identifier
                identifier = resource.get("name", resource.get("uri", "unnamed"))
                findings.append(self.create_finding(
                    message=f"Resource '{identifier}' is missing a description",
                    path=f"{path}.description",
                    config=config,
                    source=source,
                    suggestion="Add a meaningful description that explains what this resource provides",
                ))
        
        return findings


class ResourceMimeType(Rule):
    """Validates that resources have a MIME type specified."""
    
    id = "resource-mime-type"
    description = "Resources should have a mimeType specified for proper content handling"
    default_severity = Severity.INFO
    category = "resource"
    
    # Common valid MIME types for MCP resources
    COMMON_MIME_TYPES = {
        "text/plain",
        "text/html",
        "text/markdown",
        "text/csv",
        "application/json",
        "application/xml",
        "application/octet-stream",
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/webp",
    }
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        validate_format = config.options.get("validate_format", True)
        resources, is_wrapped = _get_resource_items(data)
        
        for i, resource in enumerate(resources):
            if not isinstance(resource, dict):
                continue
            
            path = build_item_path("resources", i, is_wrapped)
            identifier = resource.get("name", resource.get("uri", "unnamed"))
            
            mime_type = resource.get("mimeType")
            
            if not mime_type:
                findings.append(self.create_finding(
                    message=f"Resource '{identifier}' is missing mimeType",
                    path=f"{path}.mimeType",
                    config=config,
                    source=source,
                    suggestion="Add a mimeType (e.g., 'text/plain', 'application/json')",
                ))
            elif validate_format and isinstance(mime_type, str):
                # Basic MIME type format validation
                if "/" not in mime_type:
                    findings.append(self.create_finding(
                        message=f"Resource '{identifier}' has invalid mimeType format: '{mime_type}'",
                        path=f"{path}.mimeType",
                        config=config,
                        source=source,
                        suggestion="MIME types should be in format 'type/subtype' (e.g., 'text/plain')",
                    ))
        
        return findings


class ResourceUriValid(Rule):
    """Validates that resource URIs are properly formatted."""
    
    id = "resource-uri-valid"
    description = "Resource URIs must be valid and properly formatted"
    default_severity = Severity.ERROR
    category = "resource"
    
    # Common URI schemes for MCP resources (expanded based on real server analysis)
    ALLOWED_SCHEMES = {
        "file", "http", "https",          # Standard
        "s3", "gs", "azure",              # Cloud storage
        "data", "memory",                 # In-memory
        "test", "mock", "example",        # Testing (common in demo servers)
        "custom",                         # Custom protocols
    }
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        
        # Get allowed schemes from options or use defaults
        allowed_schemes = set(config.options.get("allowed_schemes", self.ALLOWED_SCHEMES))
        resources, is_wrapped = _get_resource_items(data)
        
        for i, resource in enumerate(resources):
            if not isinstance(resource, dict):
                continue
            
            path = build_item_path("resources", i, is_wrapped)
            identifier = resource.get("name", "unnamed")
            uri = resource.get("uri", "")
            
            if not uri:
                findings.append(self.create_finding(
                    message=f"Resource '{identifier}' is missing URI",
                    path=f"{path}.uri",
                    config=config,
                    source=source,
                    suggestion="Add a URI that identifies the resource location",
                ))
                continue
            
            if not isinstance(uri, str):
                findings.append(self.create_finding(
                    message=f"Resource '{identifier}' URI must be a string",
                    path=f"{path}.uri",
                    config=config,
                    source=source,
                ))
                continue
            
            # Parse and validate URI
            try:
                parsed = urlparse(uri)
                
                # Check scheme
                if not parsed.scheme:
                    findings.append(self.create_finding(
                        message=f"Resource '{identifier}' URI '{uri}' is missing scheme",
                        path=f"{path}.uri",
                        config=config,
                        source=source,
                        suggestion="Add a URI scheme (e.g., 'file://', 'https://')",
                    ))
                elif parsed.scheme not in allowed_schemes:
                    findings.append(self.create_finding(
                        message=f"Resource '{identifier}' URI has unsupported scheme '{parsed.scheme}'",
                        path=f"{path}.uri",
                        config=config,
                        source=source,
                        suggestion=f"Use a supported scheme: {', '.join(sorted(allowed_schemes))}",
                    ))
                
                # Check for empty path on file URIs
                if parsed.scheme == "file" and not parsed.path:
                    findings.append(self.create_finding(
                        message=f"Resource '{identifier}' file URI is missing path",
                        path=f"{path}.uri",
                        config=config,
                        source=source,
                        suggestion="Specify the file path (e.g., 'file:///path/to/file')",
                    ))
                
            except Exception as e:
                findings.append(self.create_finding(
                    message=f"Resource '{identifier}' URI '{uri}' is malformed: {e}",
                    path=f"{path}.uri",
                    config=config,
                    source=source,
                ))
        
        return findings


class ResourceNoDuplicateNames(Rule):
    """Validates that resource names are unique."""
    
    id = "resource-no-duplicate-names"
    description = "Resource names must be unique within a definition"
    default_severity = Severity.ERROR
    category = "resource"
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        resources, is_wrapped = _get_resource_items(data)
        
        seen_names: dict[str, int] = {}
        
        for i, resource in enumerate(resources):
            if not isinstance(resource, dict):
                continue
            
            name = resource.get("name", "")
            if not name:
                continue
            
            if name in seen_names:
                path = build_item_path("resources", i, is_wrapped)
                findings.append(self.create_finding(
                    message=f"Duplicate resource name '{name}' (first at index {seen_names[name]})",
                    path=f"{path}.name",
                    config=config,
                    source=source,
                    suggestion="Rename to be unique",
                ))
            else:
                seen_names[name] = i
        
        return findings


class ResourceUriTemplateValid(Rule):
    """Validates URI template syntax for templated resources."""
    
    id = "resource-uri-template-valid"
    description = "URI templates must have valid placeholder syntax"
    default_severity = Severity.ERROR
    category = "resource"
    
    # Pattern to detect URI template placeholders
    TEMPLATE_PATTERN = re.compile(r'\{([^}]*)\}')
    VALID_PLACEHOLDER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    
    def check(self, data: dict, config: RuleConfig, source: str = "") -> list[Finding]:
        findings = []
        resources, is_wrapped = _get_resource_items(data)
        
        for i, resource in enumerate(resources):
            if not isinstance(resource, dict):
                continue
            
            uri = resource.get("uri", "")
            if not isinstance(uri, str):
                continue
            
            path = build_item_path("resources", i, is_wrapped)
            identifier = resource.get("name", "unnamed")
            
            # Find all template placeholders
            placeholders = self.TEMPLATE_PATTERN.findall(uri)
            
            for placeholder in placeholders:
                if not placeholder:
                    findings.append(self.create_finding(
                        message=f"Resource '{identifier}' has empty placeholder {{}} in URI",
                        path=f"{path}.uri",
                        config=config,
                        source=source,
                        suggestion="Add a variable name inside the braces, e.g., {id}",
                    ))
                elif not self.VALID_PLACEHOLDER_PATTERN.match(placeholder):
                    findings.append(self.create_finding(
                        message=f"Resource '{identifier}' has invalid placeholder '{{{placeholder}}}' in URI",
                        path=f"{path}.uri",
                        config=config,
                        source=source,
                        suggestion="Use valid variable names (letters, numbers, underscores)",
                    ))
            
            # Check for unbalanced braces
            open_count = uri.count('{')
            close_count = uri.count('}')
            if open_count != close_count:
                findings.append(self.create_finding(
                    message=f"Resource '{identifier}' URI has unbalanced braces",
                    path=f"{path}.uri",
                    config=config,
                    source=source,
                    suggestion="Ensure all {{ have matching }}",
                ))
        
        return findings


class ResourceNameCasing(Rule):
    """Validates that resource names follow a consistent naming convention."""
    
    id = "resource-name-casing"
    description = "Resource names should follow a consistent naming convention"
    default_severity = Severity.INFO
    category = "resource"
    
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
        
        resources, is_wrapped = _get_resource_items(data)
        
        for i, resource in enumerate(resources):
            if not isinstance(resource, dict):
                continue
            
            name = resource.get("name", "")
            if name and not pattern.match(name):
                path = build_item_path("resources", i, is_wrapped)
                findings.append(self.create_finding(
                    message=f"Resource name '{name}' doesn't follow {convention}",
                    path=f"{path}.name",
                    config=config,
                    source=source,
                    suggestion=f"Rename to follow {convention} convention",
                ))
        
        return findings
