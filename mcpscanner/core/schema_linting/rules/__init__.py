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

"""Rule registry and built-in rules for MCP Schema Linting."""

from .registry import RuleRegistry, get_default_registry
from .builtin import (
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

__all__ = [
    "RuleRegistry",
    "get_default_registry",
    # Tool rules
    "ToolDescriptionRequired",
    "ToolDescriptionMinLength",
    "ToolNameCasing",
    "ToolInputSchemaRequired",
    "ToolInputSchemaProperties",
    "ToolNoDuplicateNames",
    "ToolNameNoReserved",
    # Prompt rules
    "PromptDescriptionRequired",
    "PromptArgumentsDescription",
    "PromptNameCasing",
    # Resource rules
    "ResourceDescriptionRequired",
    "ResourceMimeType",
    "ResourceUriValid",
    # General rules
    "NoEmptyArrays",
]

