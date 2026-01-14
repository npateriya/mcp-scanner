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

"""Built-in linting rules for MCP Schema validation.

Rules are organized by category:
- Tool rules: Validate tool definitions (split into basic, schema, docs)
- Prompt rules: Validate prompt definitions
- Resource rules: Validate resource definitions
- General rules: Cross-cutting validation rules
"""

# Tool rules (re-exported from submodules)
from .tool_rules import (
    # Basic rules
    ToolDescriptionRequired,
    ToolDescriptionMinLength,
    ToolNameCasing,
    ToolNoDuplicateNames,
    ToolNameNoReserved,
    ToolNameMinLength,
    ToolNameMaxLength,
    ToolNameActionVerb,
    ToolNameNoGeneric,
    # Schema rules
    ToolInputSchemaRequired,
    ToolInputSchemaProperties,
    ToolRequiredPropertiesExist,
    ToolPropertyTypeDefined,
    ToolSchemaNoEmptyObject,
    ToolEnumTypeConsistent,
    ToolEnumNoDuplicates,
    ToolAdditionalPropertiesExplicit,
    ToolOutputSchemaDefined,
    ToolOutputSchemaProperties,
    # Documentation rules
    ToolSchemaHasExamples,
    ToolDescriptionNoPlaceholder,
    ToolDescriptionMaxLength,
    DescriptionNoHtml,
)

from .prompt_rules import (
    PromptDescriptionRequired,
    PromptArgumentsDescription,
    PromptArgumentTypeDefined,
    PromptRequiredArgumentsExist,
    PromptNoDuplicateNames,
    PromptNoDuplicateArguments,
)

from .resource_rules import (
    ResourceDescriptionRequired,
    ResourceMimeType,
    ResourceUriValid,
    ResourceNoDuplicateNames,
    ResourceUriTemplateValid,
    ResourceNameCasing,
)

from .general_rules import (
    NoEmptyArrays,
    PromptNameCasing,
)

__all__ = [
    # Tool rules - Basic
    "ToolDescriptionRequired",
    "ToolDescriptionMinLength",
    "ToolNameCasing",
    "ToolNoDuplicateNames",
    "ToolNameNoReserved",
    "ToolNameMinLength",
    "ToolNameMaxLength",
    "ToolNameActionVerb",
    "ToolNameNoGeneric",
    # Tool rules - Schema
    "ToolInputSchemaRequired",
    "ToolInputSchemaProperties",
    "ToolRequiredPropertiesExist",
    "ToolPropertyTypeDefined",
    "ToolSchemaNoEmptyObject",
    "ToolEnumTypeConsistent",
    "ToolEnumNoDuplicates",
    "ToolAdditionalPropertiesExplicit",
    "ToolOutputSchemaDefined",
    "ToolOutputSchemaProperties",
    # Tool rules - Documentation
    "ToolSchemaHasExamples",
    "ToolDescriptionNoPlaceholder",
    "ToolDescriptionMaxLength",
    "DescriptionNoHtml",
    # Prompt rules
    "PromptDescriptionRequired",
    "PromptArgumentsDescription",
    "PromptArgumentTypeDefined",
    "PromptRequiredArgumentsExist",
    "PromptNoDuplicateNames",
    "PromptNoDuplicateArguments",
    "PromptNameCasing",
    # Resource rules
    "ResourceDescriptionRequired",
    "ResourceMimeType",
    "ResourceUriValid",
    "ResourceNoDuplicateNames",
    "ResourceUriTemplateValid",
    "ResourceNameCasing",
    # General rules
    "NoEmptyArrays",
]
