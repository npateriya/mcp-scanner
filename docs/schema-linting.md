# MCP Schema Linter

## Overview

The **MCP Schema Linter** validates MCP (Model Context Protocol) server definitions for quality, completeness, and best practices. Similar to [Spectral](https://stoplight.io/open-source/spectral) for OpenAPI, it provides automated quality checks for your MCP tools, prompts, and resources.

## Features

✅ **37 Built-in Rules** - Comprehensive coverage for tools, prompts, and resources  
✅ **Multiple Input Sources** - Local files and remote HTTP servers  
✅ **Configurable Severity** - Customize rules via `.mcp-lint.yaml`  
✅ **Multiple Output Formats** - Table (summary), Text (detailed), JSON (CI/CD)  
✅ **Enterprise-Ready** - Rules based on [Cisco API Insights](https://github.com/CiscoDevNet/api-insights-openapi-rulesets/)  
✅ **CI/CD Integration** - Non-zero exit codes for failed checks

---

## Quick Start

### Lint a Local File

```bash
# Lint a static JSON file
mcp-scanner lint tools.json

# Lint multiple files
mcp-scanner lint tools.json prompts.json resources.json
```

### Lint a Remote MCP Server

```bash
# Lint DeepWiki MCP server
mcp-scanner lint --server-url https://mcp.deepwiki.com/mcp

# With verbose output (show each occurrence)
mcp-scanner lint --server-url https://mcp.deepwiki.com/mcp -v
```

### Lint with Custom Config

```bash
# Use a custom ruleset configuration
mcp-scanner lint --config .mcp-lint.yaml tools.json
```

---

## CLI Reference

```bash
mcp-scanner lint [OPTIONS] [FILES...]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `FILES` | One or more JSON/YAML files to lint |

### Options

| Option | Description |
|--------|-------------|
| `--server-url URL` | Lint a live MCP server (HTTP/SSE) |
| `--config PATH` | Path to custom `.mcp-lint.yaml` config file |
| `--format FORMAT` | Output format: `table` (default), `text`, `json` |
| `--rule OVERRIDE` | Override rule severity (e.g., `rule-id:off`, `rule-id:warn`) |
| `--fail-on-warn` | Exit with error code if warnings are found |
| `--no-color` | Disable colored output |
| `-v, --verbose` | Show individual occurrences (with `--format table`) |
| `--list-rules` | List all available rules and exit |

---

## Output Formats

### Table Format (Default)

The table format provides a grouped summary, similar to [api-insights-cli](https://github.com/CiscoDevNet/api-insights-cli).

```bash
mcp-scanner lint --server-url https://mcp.deepwiki.com/mcp
```

<details>
<summary>📋 Click to expand sample output</summary>

```
🔍 Linting: https://mcp.deepwiki.com/mcp

Tool Quality
SEVERITY   CODE                              FINDINGS                                RECOMMENDATION                              AFFECTED
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
warn       tool-schema-has-examples          Schema properties lack examples         Add 'example' to schema properties              5
hint       tool-output-schema-defined        No output schema defined                Add outputSchema for predictable results        5

Prompt Quality
SEVERITY   CODE                              FINDINGS                                RECOMMENDATION                              AFFECTED
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
(no issues found)

Resource Quality
SEVERITY   CODE                              FINDINGS                                RECOMMENDATION                              AFFECTED
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
(no issues found)

Summary by Category
CATEGORY   ERROR   WARN   INFO   HINT
────────────────────────────────────────
Tool           0      5      0      5
Prompt         0      0      0      0
Resource       0      0      0      0

============================================================
📊 Summary
  Rules checked: 37
  Rules passed:  35 (94%)
  Rules failed:  2
  Total issues:  10
    • 5 warnings
    • 5 hints
```

</details>

### Verbose Table Format

Add `-v` to see individual occurrences with JSONPath locations:

```bash
mcp-scanner lint --server-url https://mcp.deepwiki.com/mcp -v
```

<details>
<summary>📋 Click to expand verbose output</summary>

```
🔍 Linting: https://mcp.deepwiki.com/mcp

Tool Quality
SEVERITY   CODE                              FINDINGS                                RECOMMENDATION                              AFFECTED
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
warn       tool-schema-has-examples          Schema properties lack examples         Add 'example' to schema properties              5
             └─ tools[0].inputSchema.properties.repo_url: Add 'example' to property 'repo_url'
             └─ tools[1].inputSchema.properties.query: Add 'example' to property 'query'
             └─ tools[2].inputSchema.properties.filepath: Add 'example' to property 'filepath'
             └─ tools[3].inputSchema.properties.question: Add 'example' to property 'question'
             └─ tools[4].inputSchema.properties.path: Add 'example' to property 'path'
hint       tool-output-schema-defined        No output schema defined                Add outputSchema for predictable results        5
             └─ tools[0]: Tool 'read_wiki_structure' has no outputSchema
             └─ tools[1]: Tool 'search_wiki' has no outputSchema
             └─ tools[2]: Tool 'read_wiki_contents' has no outputSchema
             └─ tools[3]: Tool 'ask_wiki_page' has no outputSchema
             └─ tools[4]: Tool 'get_wiki_path_content' has no outputSchema

...
```

</details>

### Text Format

Detailed output showing each finding with full context:

```bash
mcp-scanner lint --format text tools.json
```

<details>
<summary>📋 Click to expand text output</summary>

```
=== MCP Schema Linting Results ===

Source: tools.json

  ⚠ warn  tool-description-min-length
    Path: tools[0].description
    Tool description should be at least 20 characters for clarity
    
  ⚠ warn  tool-schema-has-examples
    Path: tools[0].inputSchema.properties.query
    Add 'example' to property 'query' for better documentation
    
  ℹ hint  tool-output-schema-defined
    Path: tools[0]
    Tool 'search' has no outputSchema - consider adding one for predictable results

────────────────────────────────────────
Summary: 0 errors, 2 warnings, 0 info, 1 hint
```

</details>

### JSON Format

Machine-readable output for CI/CD pipelines:

```bash
mcp-scanner lint --format json tools.json
```

<details>
<summary>📋 Click to expand JSON output</summary>

```json
{
  "source": "tools.json",
  "findings": [
    {
      "rule_id": "tool-description-min-length",
      "message": "Tool description should be at least 20 characters for clarity",
      "severity": "warn",
      "path": "tools[0].description",
      "line": null,
      "column": null
    },
    {
      "rule_id": "tool-schema-has-examples",
      "message": "Add 'example' to property 'query'",
      "severity": "warn",
      "path": "tools[0].inputSchema.properties.query",
      "line": null,
      "column": null
    }
  ],
  "summary": {
    "total": 2,
    "errors": 0,
    "warnings": 2,
    "info": 0,
    "hints": 0
  }
}
```

</details>

---

## Configuration

Create a `.mcp-lint.yaml` file to customize rule behavior:

```yaml
# .mcp-lint.yaml

# Extend the recommended ruleset
extends: ["mcp:recommended"]

# Override specific rules
rules:
  # Disable a rule entirely
  tool-output-schema-defined: off
  
  # Change severity
  tool-description-min-length:
    severity: error
  
  # Customize options
  tool-name-casing:
    severity: warn
    options:
      convention: "snake_case"  # snake_case, camelCase, kebab-case
  
  # Adjust minimum length
  tool-description-min-length:
    severity: warn
    options:
      min: 50
```

### CLI Rule Overrides

Override rules directly from the command line:

```bash
# Disable a rule
mcp-scanner lint --rule "tool-output-schema-defined:off" tools.json

# Change severity to error
mcp-scanner lint --rule "tool-description-min-length:error" tools.json
```

---

## Built-in Rules

Use `--list-rules` to see all available rules:

```bash
mcp-scanner lint --list-rules
```

### Tool Rules

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `tool-description-required` | error | Tool must have a description |
| `tool-description-min-length` | warn | Description should be ≥20 characters |
| `tool-description-max-length` | warn | Description should be ≤500 characters |
| `tool-description-no-placeholder` | warn | No placeholder text like "TODO" or "TBD" |
| `tool-name-casing` | warn | Name should follow consistent casing |
| `tool-name-min-length` | warn | Name should be ≥3 characters |
| `tool-name-max-length` | warn | Name should be ≤64 characters |
| `tool-name-action-verb` | info | Name should start with an action verb |
| `tool-name-no-generic` | info | Avoid generic names like "process" |
| `tool-name-no-reserved` | error | Avoid reserved words in names |
| `tool-no-duplicate-names` | error | Tool names must be unique |
| `tool-input-schema-required` | error | Tool must have inputSchema |
| `tool-input-schema-properties` | warn | inputSchema should have properties |
| `tool-required-properties-exist` | error | Required properties must be defined |
| `tool-property-type-defined` | warn | Properties should have explicit types |
| `tool-schema-no-empty-object` | warn | Avoid empty object schemas |
| `tool-enum-type-consistent` | error | Enum values must match property type |
| `tool-enum-no-duplicates` | error | Enum values must be unique |
| `tool-additional-properties-explicit` | info | Explicitly set additionalProperties |
| `tool-schema-has-examples` | warn | Properties should have examples |
| `tool-output-schema-defined` | hint | Define outputSchema for predictability |
| `tool-output-schema-properties` | warn | outputSchema should have properties |

### Prompt Rules

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `prompt-description-required` | error | Prompt must have a description |
| `prompt-name-casing` | warn | Name should follow consistent casing |
| `prompt-arguments-description` | warn | Arguments should have descriptions |
| `prompt-argument-type-defined` | warn | Arguments should have explicit types |
| `prompt-required-arguments-exist` | error | Required arguments must be defined |
| `prompt-no-duplicate-names` | error | Prompt names must be unique |
| `prompt-no-duplicate-arguments` | error | Argument names must be unique |

### Resource Rules

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `resource-description-required` | warn | Resource should have a description |
| `resource-mime-type` | warn | Resource should specify mimeType |
| `resource-uri-valid` | error | URI must have valid scheme |
| `resource-uri-template-valid` | warn | URI template syntax must be valid |
| `resource-no-duplicate-names` | error | Resource names must be unique |
| `resource-name-casing` | warn | Name should follow consistent casing |

### General Rules

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `no-empty-arrays` | warn | Avoid empty tools/prompts/resources arrays |
| `description-no-html` | warn | Descriptions should not contain HTML |

---

## Examples with Public MCP Servers

### DeepWiki

```bash
# Lint DeepWiki MCP server
mcp-scanner lint --server-url https://mcp.deepwiki.com/mcp
```

<details>
<summary>📋 Click to expand DeepWiki lint results</summary>

```
🔍 Linting: https://mcp.deepwiki.com/mcp

Tool Quality
SEVERITY   CODE                              FINDINGS                                RECOMMENDATION                              AFFECTED
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
warn       tool-schema-has-examples          Schema properties lack examples         Add 'example' to schema properties              5
hint       tool-output-schema-defined        No output schema defined                Add outputSchema for predictable results        5

============================================================
📊 Summary
  Rules checked: 37
  Rules passed:  35 (94%)
  Rules failed:  2
  Total issues:  10
```

</details>

### Other Public MCP Servers

```bash
# Lint any public MCP server that exposes an HTTP endpoint
mcp-scanner lint --server-url https://your-mcp-server.com/mcp
```

### Local Tool Definition

```bash
# Create a sample tools.json
cat > tools.json << 'EOF'
{
  "tools": [
    {
      "name": "searchUsers",
      "description": "Search for users in the database by various criteria including name, email, or department.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Search query string",
            "example": "john.doe@example.com"
          },
          "limit": {
            "type": "integer",
            "description": "Maximum results to return",
            "example": 10
          }
        },
        "required": ["query"]
      }
    }
  ]
}
EOF

# Lint it
mcp-scanner lint tools.json
```

<details>
<summary>📋 Click to expand well-defined tool results</summary>

```
🔍 Linting: tools.json

Tool Quality
(no issues found)

============================================================
📊 Summary
  Rules checked: 37
  Rules passed:  37 (100%)
  Rules failed:  0
  Total issues:  0
    
✅ All checks passed!
```

</details>

---

## CI/CD Integration

### GitHub Actions

```yaml
name: MCP Schema Lint

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install MCP Scanner
        run: pip install cisco-ai-mcp-scanner
      
      - name: Lint MCP Definitions
        run: |
          mcp-scanner lint \
            --format json \
            --fail-on-warn \
            mcp-definitions/*.json
```

### GitLab CI

```yaml
mcp-lint:
  image: python:3.11
  script:
    - pip install cisco-ai-mcp-scanner
    - mcp-scanner lint --fail-on-warn mcp-definitions/*.json
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: mcp-lint
        name: MCP Schema Lint
        entry: mcp-scanner lint
        language: python
        files: '\.json$'
        additional_dependencies: ['cisco-ai-mcp-scanner']
```

---

## Comparison with Security Scanning

The schema linter focuses on **quality and documentation** while other MCP Scanner features focus on **security**:

| Aspect | Schema Linter | Security Analyzers |
|--------|---------------|-------------------|
| **Purpose** | Quality & completeness | Threat detection |
| **Checks** | Descriptions, examples, naming | Injection, poisoning, exfiltration |
| **Speed** | Instant (no API calls) | May require LLM/API |
| **Output** | Linting findings | Security findings |
| **CI/CD Use** | Style enforcement | Security gates |

Use **both** for comprehensive MCP server validation:

```bash
# Quality checks
mcp-scanner lint tools.json

# Security checks
mcp-scanner --analyzers yara static --tools tools.json
```

---

## Troubleshooting

### Connection Errors

```bash
# If server connection fails, check the URL
mcp-scanner lint --server-url https://mcp.example.com/mcp

# Output shows infrastructure errors separately
# ❌ Errors:
#   • Connection error: Failed to connect to https://mcp.example.com/mcp
```

### Unknown Rule Warnings

If you specify an unknown rule in config, you'll get a suggestion:

```yaml
# .mcp-lint.yaml
rules:
  tool-desc-required: off  # Typo!
```

```bash
mcp-scanner lint --config .mcp-lint.yaml tools.json
# ⚠️ Config Warnings:
#   • Unknown rule 'tool-desc-required' in config. Did you mean 'tool-description-required'?
```

---

## Related Documentation

- **[Architecture](architecture.md)** - System design overview
- **[Static Scanning](static-scanning.md)** - Offline security scanning
- **[Design Document](design/mcp-schema-linter-design.md)** - Detailed design rationale

---

**Status**: ✅ Production Ready  
**Rules**: 37 built-in  
**License**: Apache 2.0

