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

"""JSON formatter for MCP Schema Linting results."""

import json
from typing import Any

from ..linter import LintResult


class JsonFormatter:
    """Formats linting results as JSON output.
    
    Produces machine-readable output suitable for CI/CD integration
    and programmatic consumption.
    """
    
    def __init__(self, pretty: bool = True):
        """Initialize formatter.
        
        Args:
            pretty: Whether to pretty-print JSON with indentation
        """
        self.pretty = pretty
    
    def format(self, result: LintResult) -> str:
        """Format a single LintResult as JSON.
        
        Args:
            result: The linting result to format
            
        Returns:
            JSON string
        """
        return self._to_json(result.to_dict())
    
    def format_multiple(self, results: list[LintResult]) -> str:
        """Format multiple LintResults as JSON.
        
        Args:
            results: List of linting results
            
        Returns:
            JSON string containing array of results with summary
        """
        output = {
            "results": [r.to_dict() for r in results],
            "summary": {
                "files_checked": len(results),
                "total_findings": sum(len(r.findings) for r in results),
                "total_errors": sum(r.error_count for r in results),
                "total_warnings": sum(r.warning_count for r in results),
                "total_info": sum(r.info_count for r in results),
                "total_hints": sum(r.hint_count for r in results),
                "passed": all(not r.has_errors for r in results),
            },
        }
        return self._to_json(output)
    
    def _to_json(self, data: dict[str, Any]) -> str:
        """Convert data to JSON string."""
        if self.pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)

