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

"""Lint orchestrator - handles all lint input sources and coordination.

This module provides a clean interface for the CLI, encapsulating:
- Multiple input source handling (files, HTTP server)
- MCP client connections
- Result aggregation

Usage:
    orchestrator = LintOrchestrator()
    results = await orchestrator.run(
        files=["tools.json"],
        server_url="https://mcp.example.com",
        config=lint_config,
        verbose=True,
    )
"""

from dataclasses import dataclass
from typing import Callable
import sys

from .linter import SchemaLinter, LintConfig, LintResult


@dataclass
class LintOptions:
    """Options for running the linter."""
    files: list[str] | None = None
    server_url: str | None = None
    bearer_token: str | None = None
    custom_headers: dict[str, str] | None = None
    config: LintConfig | None = None
    verbose: bool = False
    log: Callable[[str], None] | None = None
    
    def _log(self, msg: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose and self.log:
            self.log(msg)


class LintOrchestrator:
    """Orchestrates linting across multiple input sources.
    
    This class encapsulates the complexity of:
    - Handling different input sources (files, HTTP servers)
    - Managing MCP client connections
    - Aggregating results from multiple sources
    
    Example:
        orchestrator = LintOrchestrator()
        results = await orchestrator.run(LintOptions(
            files=["tools.json"],
            server_url="https://mcp.example.com",
            verbose=True,
        ))
    """
    
    def __init__(self):
        self.linter = SchemaLinter()
    
    def list_rules(self) -> list[dict]:
        """List all available linting rules."""
        return self.linter.list_rules()
    
    async def run(self, options: LintOptions) -> list[LintResult]:
        """Run linting with the given options.
        
        Args:
            options: Configuration for the lint run
            
        Returns:
            List of LintResult objects from all sources
        """
        config = options.config or LintConfig()
        results: list[LintResult] = []
        
        # 1. Lint static files
        if options.files:
            file_results = self.linter.lint_files(options.files, config)
            results.extend(file_results)
        
        # 2. Lint live HTTP server
        if options.server_url:
            server_results = await self._lint_server(options, config)
            results.extend(server_results)
        
        return results
    
    async def _lint_server(
        self, 
        options: LintOptions, 
        config: LintConfig
    ) -> list[LintResult]:
        """Lint a live MCP server via HTTP.
        
        Args:
            options: Lint options including server_url and auth
            config: Lint configuration
            
        Returns:
            List of LintResult for tools, prompts, and resources
        """
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client
        
        results: list[LintResult] = []
        server_url = options.server_url
        
        options._log(f"🔍 Fetching definitions from {server_url}...")
        
        try:
            # Build headers
            headers = {}
            if options.bearer_token:
                headers["Authorization"] = f"Bearer {options.bearer_token}"
            if options.custom_headers:
                headers.update(options.custom_headers)
            
            async with streamablehttp_client(server_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Lint tools
                    tools_result = await session.list_tools()
                    tools_data = {"tools": [
                        {
                            "name": t.name, 
                            "description": t.description or "", 
                            "inputSchema": t.inputSchema,
                            "outputSchema": getattr(t, 'outputSchema', None),
                        }
                        for t in tools_result.tools
                    ]}
                    result = self.linter.lint(tools_data, config, source=f"{server_url}/tools")
                    results.append(result)
                    options._log(f"   ✓ Found {len(tools_result.tools)} tools")
                    
                    # Lint prompts (may not be supported)
                    try:
                        prompts_result = await session.list_prompts()
                        prompts_data = {"prompts": [
                            {
                                "name": p.name, 
                                "description": p.description or "", 
                                "arguments": p.arguments or []
                            }
                            for p in prompts_result.prompts
                        ]}
                        result = self.linter.lint(prompts_data, config, source=f"{server_url}/prompts")
                        results.append(result)
                        options._log(f"   ✓ Found {len(prompts_result.prompts)} prompts")
                    except Exception:
                        pass  # Server may not support prompts
                    
                    # Lint resources (may not be supported)
                    try:
                        resources_result = await session.list_resources()
                        resources_data = {"resources": [
                            {
                                "name": r.name, 
                                "description": r.description or "", 
                                "uri": str(r.uri), 
                                "mimeType": r.mimeType
                            }
                            for r in resources_result.resources
                        ]}
                        result = self.linter.lint(resources_data, config, source=f"{server_url}/resources")
                        results.append(result)
                        options._log(f"   ✓ Found {len(resources_result.resources)} resources")
                    except Exception:
                        pass  # Server may not support resources
                        
        except Exception as e:
            # P1: Use factory method for clean error handling
            results.append(LintResult.connection_error(server_url, str(e)))
        
        return results
    
    def has_errors(self, results: list[LintResult]) -> bool:
        """Check if any results have errors."""
        return any(r.has_errors for r in results)
    
    def has_warnings(self, results: list[LintResult]) -> bool:
        """Check if any results have warnings."""
        return any(r.has_warnings for r in results)

