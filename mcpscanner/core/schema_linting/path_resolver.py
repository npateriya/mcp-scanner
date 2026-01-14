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

"""JSONPath-like path resolution for navigating MCP schema structures.

This module provides utilities for:
- Building paths to elements in nested structures
- Resolving paths to get values from data
- Formatting paths for human-readable output
"""

from typing import Any, Iterator
from dataclasses import dataclass


@dataclass
class PathMatch:
    """Result of a path query.
    
    Attributes:
        path: The full path to this element (e.g., "tools[0].description")
        value: The value at this path
        parent: The parent object containing this element
        key: The key/index used to access this element from parent
    """
    path: str
    value: Any
    parent: Any
    key: str | int


def build_path(*parts: str | int) -> str:
    """Build a JSONPath-like string from parts.
    
    Examples:
        build_path("tools", 0, "description") -> "tools[0].description"
        build_path("prompts", 1, "arguments", 0, "name") -> "prompts[1].arguments[0].name"
    """
    result = []
    for part in parts:
        if isinstance(part, int):
            result.append(f"[{part}]")
        elif result:  # Not first element
            result.append(f".{part}")
        else:
            result.append(str(part))
    return "".join(result)


def get_by_path(data: Any, path: str) -> Any | None:
    """Get a value from nested data using a path string.
    
    Args:
        data: The root data structure
        path: Path string like "tools[0].description"
        
    Returns:
        The value at the path, or None if not found
        
    Example:
        data = {"tools": [{"name": "test", "description": "A test"}]}
        get_by_path(data, "tools[0].description") -> "A test"
    """
    if not path:
        return data
    
    current = data
    parts = _parse_path(path)
    
    for part in parts:
        if current is None:
            return None
        
        if isinstance(part, int):
            if isinstance(current, list) and 0 <= part < len(current):
                current = current[part]
            else:
                return None
        else:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
    
    return current


def _parse_path(path: str) -> list[str | int]:
    """Parse a path string into parts.
    
    "tools[0].description" -> ["tools", 0, "description"]
    """
    parts: list[str | int] = []
    current = ""
    i = 0
    
    while i < len(path):
        char = path[i]
        
        if char == ".":
            if current:
                parts.append(current)
                current = ""
        elif char == "[":
            if current:
                parts.append(current)
                current = ""
            # Find closing bracket
            j = i + 1
            while j < len(path) and path[j] != "]":
                j += 1
            index_str = path[i + 1 : j]
            try:
                parts.append(int(index_str))
            except ValueError:
                parts.append(index_str)  # Keep as string if not numeric
            i = j  # Skip to closing bracket
        else:
            current += char
        
        i += 1
    
    if current:
        parts.append(current)
    
    return parts


def iterate_items(
    data: dict | list,
    item_type: str,
    base_path: str = "",
) -> Iterator[PathMatch]:
    """Iterate over items of a specific type in MCP data.
    
    Args:
        data: MCP definition data
        item_type: Type of items to iterate ("tools", "prompts", "resources")
        base_path: Base path prefix
        
    Yields:
        PathMatch for each item found
        
    Example:
        for match in iterate_items(data, "tools"):
            print(f"Tool at {match.path}: {match.value.get('name')}")
    """
    if isinstance(data, dict):
        items = data.get(item_type, [])
        if isinstance(items, list):
            for i, item in enumerate(items):
                path = build_path(item_type, i) if not base_path else build_path(base_path, item_type, i)
                yield PathMatch(
                    path=path,
                    value=item,
                    parent=items,
                    key=i,
                )
    elif isinstance(data, list):
        # Direct list of items
        for i, item in enumerate(data):
            path = f"[{i}]" if not base_path else f"{base_path}[{i}]"
            yield PathMatch(
                path=path,
                value=item,
                parent=data,
                key=i,
            )


def iterate_fields(
    obj: dict,
    base_path: str = "",
) -> Iterator[PathMatch]:
    """Iterate over all fields in a dictionary.
    
    Args:
        obj: Dictionary to iterate
        base_path: Base path prefix
        
    Yields:
        PathMatch for each field
    """
    for key, value in obj.items():
        path = f"{base_path}.{key}" if base_path else key
        yield PathMatch(
            path=path,
            value=value,
            parent=obj,
            key=key,
        )


def get_items(data: dict | list, key: str) -> tuple[list[dict], bool]:
    """Extract items from MCP data, handling both wrapped and direct formats.
    
    This helper eliminates the repetitive pattern:
        tools = data.get("tools", []) if isinstance(data, dict) else data
        if not isinstance(tools, list):
            tools = [data] if isinstance(data, dict) and "name" in data else []
    
    Args:
        data: MCP definition data (dict with key or direct list)
        key: The key to extract ("tools", "prompts", "resources")
        
    Returns:
        Tuple of (list of items, is_wrapped) where is_wrapped indicates
        if items came from data[key] vs being the data itself
        
    Example:
        # Wrapped format
        data = {"tools": [{"name": "a"}, {"name": "b"}]}
        items, wrapped = get_items(data, "tools")  # ([{...}, {...}], True)
        
        # Direct list format  
        data = [{"name": "a"}, {"name": "b"}]
        items, wrapped = get_items(data, "tools")  # ([{...}, {...}], False)
        
        # Single item format
        data = {"name": "a", "description": "..."}
        items, wrapped = get_items(data, "tools")  # ([{...}], False)
    """
    if isinstance(data, dict):
        if key in data:
            items = data[key]
            if isinstance(items, list):
                return items, True
            return [], True
        # Check if data itself is a single item (has 'name' key)
        if "name" in data:
            return [data], False
        return [], False
    elif isinstance(data, list):
        return data, False
    return [], False


def build_item_path(key: str, index: int, is_wrapped: bool) -> str:
    """Build the correct path prefix for an item based on data format.
    
    Args:
        key: The item type key ("tools", "prompts", "resources")
        index: The item index
        is_wrapped: Whether the item came from data[key]
        
    Returns:
        Path string like "tools[0]" or "[0]"
        
    Example:
        build_item_path("tools", 0, True)   # "tools[0]"
        build_item_path("tools", 0, False)  # "[0]"
    """
    if is_wrapped:
        return build_path(key, index)
    return f"[{index}]"
