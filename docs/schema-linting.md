# MCP Schema Linter

## Overview

The **MCP Schema Linter** validates MCP (Model Context Protocol) server definitions for quality, completeness, and best practices. Similar to [Spectral](https://stoplight.io/open-source/spectral) for OpenAPI, it provides automated quality checks for your MCP tools, prompts, and resources.

## Features

✅ **37 Built-in Rules** - Comprehensive coverage for tools, prompts, and resources  
✅ **Custom Dynamic Rules** - Create your own rules in YAML without writing code  
✅ **3 Built-in Rulesets** - `mcp:recommended` (default), `mcp:strict`, `mcp:quality` presets  
✅ **Multiple Input Sources** - Local files and remote HTTP servers  
✅ **Configurable Severity** - Customize rules via `.mcp-lint.yaml`  
✅ **Multiple Output Formats** - Table (summary), Text (detailed), JSON (CI/CD)  
✅ **Enterprise-Ready** - Rules based on [Cisco API Insights](https://github.com/CiscoDevNet/api-insights-openapi-rulesets/)  
✅ **CI/CD Integration** - Non-zero exit codes for failed checks

---

## Quick Start

### Lint a Remote MCP Server

```bash
# Lint DeepWiki MCP server
mcp-scanner lint --server-url https://mcp.deepwiki.com/mcp

# With verbose output (show each occurrence)
mcp-scanner lint --server-url https://mcp.deepwiki.com/mcp -v
```

### Lint a Local File

```bash
# Lint a static JSON file
mcp-scanner lint tools.json

# Lint multiple files
mcp-scanner lint tools.json prompts.json resources.json
```

### Lint with Custom Config

```bash
# Use a custom configuration file
mcp-scanner lint --config .mcp-lint.yaml tools.json

# Use strict ruleset (create a config file first)
echo 'extends: ["mcp:strict"]' > strict.yaml
mcp-scanner lint --config strict.yaml tools.json
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

## Built-in Rules

The linter includes **37 built-in rules** covering tools, prompts, resources, and general quality. Use `--list-rules` to see all available rules:

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

## Customizing Rules

Once you're familiar with the built-in rules, you can customize their behavior.

### CLI Rule Overrides

Override rules directly from the command line (quick one-off changes):

```bash
# Disable a rule for this run
mcp-scanner lint --rule "tool-output-schema-defined:off" tools.json

# Change severity to error
mcp-scanner lint --rule "tool-description-min-length:error" tools.json
```

### Configuration File Overrides

For persistent customization, use a `.mcp-lint.yaml` file:

```yaml
# .mcp-lint.yaml
extends: ["mcp:recommended"]

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
      convention: "camelCase"  # Change from default snake_case
  
  # Require longer descriptions
  tool-description-min-length:
    severity: warn
    options:
      min: 50  # Increase from default 20
```

### Built-in Rulesets

**What is a ruleset?** A ruleset is a pre-configured bundle of rule settings (severity levels and options) that you can inherit from. Instead of configuring each rule individually, you extend a ruleset and only override what you need.

Use `extends` in your config file to inherit from a ruleset:

```yaml
extends: ["mcp:recommended"]  # Start with this ruleset
```

#### Available Rulesets

| Ruleset | Best For | Description |
|---------|----------|-------------|
| `mcp:recommended` | Most users | **Default.** Balanced defaults - errors for critical issues, warnings for best practices |
| `mcp:strict` | Production/CI | Everything as errors with stricter thresholds - fails fast |
| `mcp:quality` | Documentation | Focus on description quality with longer minimum lengths |

#### Ruleset Comparison

The following table shows how each ruleset configures the **core rules** (all 37 built-in rules run, but these are the ones with explicit configuration):

| Rule | `mcp:recommended` ⭐ | `mcp:strict` | `mcp:quality` |
|------|-------------------|--------------|---------------|
| **Tool Rules** ||||
| `tool-description-required` | error | error | error |
| `tool-description-min-length` | warn (20 chars) | **error (30 chars)** | warn **(50 chars)** |
| `tool-name-casing` | warn | **error** | info |
| `tool-input-schema-required` | warn | **error** | warn |
| `tool-input-schema-properties` | info | **error** | warn |
| **Prompt Rules** ||||
| `prompt-description-required` | error | error | error |
| `prompt-arguments-description` | warn | **error** | **error** |
| **Resource Rules** ||||
| `resource-description-required` | warn | **error** | **error** |
| `resource-mime-type` | info | warn | info |

**Key differences:**
- **`mcp:strict`** — Upgrades most warnings to errors, uses stricter thresholds (30 char min description)
- **`mcp:quality`** — Requires longer descriptions (50 chars), requires property descriptions in schemas

#### Running with Different Rulesets

**Method 1: Create a config file**

Create `.mcp-lint.yaml` in your project root:
```yaml
extends: ["mcp:strict"]  # Use strict ruleset
```

Then run (auto-discovers config):
```bash
mcp-scanner lint tools.json
```

**Method 2: Use explicit config file**

Create `strict-rules.yaml`:
```yaml
extends: ["mcp:strict"]
```

Run with `--config`:
```bash
# Use strict ruleset
mcp-scanner lint --config strict-rules.yaml tools.json

# Or quality ruleset
mcp-scanner lint --config quality-rules.yaml tools.json
```

**Method 3: Quick switch without config file**

Currently, you need a config file to switch rulesets. For quick testing, create minimal files:

```bash
# Create strict config
echo 'extends: ["mcp:strict"]' > .mcp-lint-strict.yaml

# Run with strict rules
mcp-scanner lint --config .mcp-lint-strict.yaml tools.json
```

#### Customizing Rulesets

**Start strict, then relax specific rules:**
```yaml
# strict-relaxed.yaml
extends: ["mcp:strict"]

rules:
  tool-output-schema-defined: off     # Disable this rule
  tool-description-min-length:
    severity: warn                    # Downgrade to warning
```

**Combine rulesets (later ones override earlier):**
```yaml
extends: ["mcp:recommended", "mcp:quality"]  # quality settings override recommended
```

**Default behavior:** If you don't specify `extends` or use a config file, `mcp:recommended` is used automatically.

---

## Custom Dynamic Rules (Advanced)

The Dynamic Rulesets feature lets you create your own custom linting rules using simple YAML configuration — **no Python coding required**. Think of it like creating custom spell-check rules for your MCP tool definitions.

#### Why Use Custom Rules?

| Use Case | Example Rule |
|----------|--------------|
| **Enforce naming conventions** | All tools must start with `mycompany_` |
| **Require documentation** | All schema properties need descriptions |
| **Limit complexity** | Tool names can't exceed 40 characters |
| **Block patterns** | No placeholder text like "TODO" in descriptions |
| **Standardize formats** | All resource URIs must use `https://` |

#### How Rules Work

Every custom rule has **3 essential parts**:

```yaml
my-rule-name:
  target: "tools[].description"   # 1️⃣ WHERE to look (path pattern)
  check: "minLength"              # 2️⃣ WHAT to check (built-in function)
  options:                        # 3️⃣ HOW to check (parameters)
    min: 50
  severity: warn                  # error, warn, info, or hint
  message: "Description too short"
```

#### Complete Example

```yaml
# .mcp-lint.yaml
extends: ["mcp:recommended"]  # Start with sensible defaults

rules:
  # Custom rule: enforce company naming prefix
  acme-tool-prefix:
    target: "tools[].name"
    check: "pattern"
    options:
      match: "^acme_|^internal_"
    severity: error
    message: "Tool name '{value}' must start with 'acme_' or 'internal_'"
    recommendation: "Rename tool to use company prefix"
  
  # Custom rule: require property descriptions
  require-prop-descriptions:
    target: "tools[].inputSchema.properties[].description"
    check: "required"
    severity: warn
    message: "Property at {path} is missing description"
  
  # Custom rule: block placeholder text
  no-placeholder-text:
    target: "tools[].description"
    check: "pattern"
    options:
      notMatch: "(TODO|FIXME|TBD|placeholder)"
    severity: error
    message: "Description contains placeholder text"
  
  # Custom rule: enforce max length on tool names
  tool-name-max-length:
    target: "tools[].name"
    check: "maxLength"
    options:
      max: 40
    severity: warn
    message: "Tool name exceeds 40 characters"
```

#### Path Patterns (WHERE to look)

The `target` field uses a simplified path syntax to specify what values to check:

| Pattern | What It Checks |
|---------|----------------|
| `tools[].name` | All tool names |
| `tools[].description` | All tool descriptions |
| `tools[].inputSchema.properties[].type` | All property types in input schemas |
| `tools[].inputSchema.properties[].description` | All property descriptions |
| `prompts[].name` | All prompt names |
| `prompts[].arguments[].description` | All prompt argument descriptions |
| `resources[].uri` | All resource URIs |

The `[]` syntax means "iterate over all items in the array or object".

#### Check Functions (WHAT to check)

| Check | Description | Options | Example |
|-------|-------------|---------|---------|
| `pattern` | Regex matching | `match`, `notMatch` | `match: "^get_"` |
| `minLength` | Minimum string length | `min` | `min: 20` |
| `maxLength` | Maximum string length | `max` | `max: 100` |
| `required` | Value must exist and be non-empty | `allowEmpty` | - |
| `notEmpty` | Value not null/empty | - | - |
| `enum` | Value in allowed list | `values` | `values: [a, b, c]` |
| `type` | JSON type check | `type` | `type: string` |
| `casing` | Naming convention | `convention` | `convention: snake_case` |
| `startsWith` | String prefix | `prefix` | `prefix: "get_"` |
| `endsWith` | String suffix | `suffix` | `suffix: "_id"` |
| `range` | Numeric range | `min`, `max` | `min: 1, max: 100` |

**Casing options:** `snake_case`, `camelCase`, `kebab-case`, `PascalCase`

**Type options:** `string`, `number`, `integer`, `boolean`, `object`, `array`, `null`

#### Message Templates

Custom messages support placeholders:

| Placeholder | Description | Example Output |
|-------------|-------------|----------------|
| `{value}` | The actual value that failed | `get_users` |
| `{path}` | Full path to the value | `tools[0].name` |

```yaml
message: "Tool '{value}' at {path} violates naming convention"
# Output: "Tool 'BadName' at tools[2].name violates naming convention"
```

#### Built-in Rulesets (extends)

Start with a pre-configured ruleset and customize from there:

| Ruleset | Description |
|---------|-------------|
| `mcp:recommended` | Balanced defaults (used by default) |
| `mcp:strict` | All rules as errors, stricter thresholds |
| `mcp:quality` | Focus on documentation quality |

```yaml
# Start strict, then relax specific rules
extends: ["mcp:strict"]

rules:
  tool-output-schema-defined: off     # Disable this rule
  tool-description-min-length:
    severity: warn                    # Downgrade to warning
```

#### More Examples

**Enforce HTTPS for resources:**
```yaml
https-only:
  target: "resources[].uri"
  check: "startsWith"
  options:
    prefix: "https://"
  severity: error
  message: "Resource URI must use HTTPS"
```

**Require enum values to be strings:**
```yaml
string-enums:
  target: "tools[].inputSchema.properties[].enum[]"
  check: "type"
  options:
    type: "string"
  severity: info
  message: "Enum values should be strings for consistent LLM handling"
```

**Limit description length:**
```yaml
concise-descriptions:
  target: "tools[].description"
  check: "maxLength"
  options:
    max: 500
  severity: warn
  message: "Description exceeds 500 characters - consider being more concise"
```

See `examples/custom-rules.mcp-lint.yaml` for a complete working example.

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

