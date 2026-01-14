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

"""Built-in linting rules for MCP Tool definitions.

This module re-exports all tool rules from their respective submodules:
- tool_rules_basic: Naming and description validation
- tool_rules_schema: inputSchema/outputSchema validation  
- tool_rules_docs: Documentation quality rules

For cleaner code organization, rules are split into:
- tool_rules_basic.py (~300 lines): Core naming and description rules
- tool_rules_schema.py (~350 lines): Schema structure validation
- tool_rules_docs.py (~150 lines): Documentation quality rules
"""

# Re-export all rules for backward compatibility
from .tool_rules_basic import (
    ToolDescriptionRequired,
    ToolDescriptionMinLength,
    ToolNameCasing,
    ToolNoDuplicateNames,
    ToolNameNoReserved,
    ToolNameMinLength,
    ToolNameMaxLength,
    ToolNameActionVerb,
    ToolNameNoGeneric,
)

from .tool_rules_schema import (
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
)

from .tool_rules_docs import (
    ToolSchemaHasExamples,
    ToolDescriptionNoPlaceholder,
    ToolDescriptionMaxLength,
    DescriptionNoHtml,
)

__all__ = [
    # Basic rules (naming, description)
    "ToolDescriptionRequired",
    "ToolDescriptionMinLength",
    "ToolNameCasing",
    "ToolNoDuplicateNames",
    "ToolNameNoReserved",
    "ToolNameMinLength",
    "ToolNameMaxLength",
    "ToolNameActionVerb",
    "ToolNameNoGeneric",
    # Schema rules (inputSchema, outputSchema)
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
    # Documentation quality rules
    "ToolSchemaHasExamples",
    "ToolDescriptionNoPlaceholder",
    "ToolDescriptionMaxLength",
    "DescriptionNoHtml",
]
