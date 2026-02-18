# Non-Python File Metadata Tests

**Test Execution Date**: 1771401340.938862
**Files Tested**: 6

## Summary Statistics

- **Total files**: 6
- **Total full tokens**: 15,869
- **Total metadata tokens**: 1,316
- **Average token reduction**: 91.7%
- **File types tested**: toml, json, markdown

---

## Results by File Type

### Json Files

#### .planning/config.json

- **Full size**: 410 bytes (102 tokens)
- **Metadata size**: 119 bytes (29 tokens)
- **Token reduction**: 71.6%
- **Cost savings**: $0.000219
- **Lines**: 18

**Metadata content:**
```
Configuration: config.json
Type: .json
Lines: 18
Size: 410 bytes

Structure:
Top-level keys: mode, depth, gates, safety
```

**Assessment:**
- ⚠️ Low reduction (<80%) — expected for small config files
- Information density: HIGH (structural keys/sections)
- **Usefulness score**: 4/5

---

### Markdown Files

#### README.md

- **Full size**: 24,303 bytes (6,075 tokens)
- **Metadata size**: 2,908 bytes (727 tokens)
- **Token reduction**: 88.0%
- **Cost savings**: $0.016044
- **Lines**: 699

**Metadata content:**
```
Document: README.md
Type: .md
Lines: 699
Headers:
# Token-Efficient Coding Stack
## Results (Validated 2026-01-12)
## Quick Install
### macOS (Automated)
# One-command installation (clones repo and installs everything)
### Linux (Manual)
# Clone repository
# Install packages
# Configure MCP servers
# Copy skills
# Restart Claude Code
## How You'll Save Money and Tokens
### 1. AuZoom - Progressive Discovery of Context
### 2. Orchestrator - Pay Less Per Task
### 3. Get Shit Done (GSD) - Meta-Prompting System
## How They Work Together
## Real-World Impact
### Your Cost Savings by Task Type (Validated)
## Tools & Capabilities
### Your AuZoom MCP Tools
# You'll read files progressively (pay only for what you need)
# You'll find code without reading files
# You'll analyze dependencies without reading files
# You'll check cache performance
# You'll validate code structure
### Your Orchestrator MCP Tools
# You'll get routing recommendation
# You'll get: {model: "sonnet", complexity_score: 7.8, cost: "$0.045"}
# You'll execute on specific model
# You'll get: {success: true, response: "...", tokens: 1234, cost: "$0.001"}
# You'll validate output quality
# You'll get: {pass: true, confidence: 0.92}
## Usage Examples
### Example 1: Explore + Route + Execute
# 1. You'll understand codebase with minimal tokens
# 2. You'll route the task to appropriate model
# You'll get: "sonnet" (complexity 7.8)
# 3. You'll implement using recommended model via Task tool
# 4. You'll validate structure
# You'll get: compliant: True
### Example 2: Find + Fix
# 1. You'll locate code instantly
# You'll get: src/auth.py::authenticate
# 2. You'll route the fix
# You'll get: "haiku" (complexity 2.5)
# 3. You'll fix with cheap model - you save 93%
### Example 3: Refactor with Validation
# 1. You'll check for violations
# You'll get: [function too long, module too large]
# 2. You'll route refactoring
# You'll get: "haiku" (complexity 3.2)
# 3. You'll fix and re-validate
## Validation Results
### Test Methodology
### Your Performance by Category
### Key Findings
## Architecture
### Component Details
## Your Skills for Claude Code
# Your main skill - quick reference
# Your detailed patterns (on-demand)
## Your Workflow Templates
## Testing
# You'll test AuZoom (39 tests)
# You'll test Orchestrator (65 tests)
# Your total: 104 tests, 100% pass rate
## Project Structure
## When You'll Use What
### Always Use
### You'll Use AuZoom For
### You'll Skip AuZoom For
### Your Model Routing Guide
## Platform Compatibility
### Supported Platforms
### Dependencies (All Cross-Platform)
### Platform-Specific Notes
## Contributing
### Testing Status
## Roadmap
### V1 (Complete) ✅
### V2 (Future)
## License
## Roadmap
### Current Status (v1.0)
### Planned Features (v1.1+)
#### High Priority
#### Medium Priority
#### Research Items
### Your Known Limitations
## Support & Credits
### Support
### Credits
## Sources
```

**Assessment:**
- ⚠️ Moderate reduction (80-90%)
- Information density: HIGH (complete document outline)
- **Usefulness score**: 4.5/5

---

#### VALIDATION-SUMMARY.md

- **Full size**: 17,663 bytes (4,415 tokens)
- **Metadata size**: 778 bytes (194 tokens)
- **Token reduction**: 95.6%
- **Cost savings**: $0.012663
- **Lines**: 342

**Metadata content:**
```
Document: VALIDATION-SUMMARY.md
Type: .md
Lines: 342
Headers:
# Validation Summary
## Task-by-Task Results
## How Each Component Contributes
### AuZoom: Progressive Context Discovery
### Orchestrator: Intelligent Model Routing
## Cost Analysis
### By Task Complexity
## Success Rates by Complexity
## Where the Stack Excels
## Where the Stack Struggles
## Usage Recommendations
### You'll Use This For:
### You'll Avoid This For:
### Best Practice:
## Validation Methodology
## Bottom Line
## Audit Findings
### What Was Audited
### Key Findings
#### 1. Cost Savings Claim PARTIALLY REFUTED
#### 2. Token Savings Claim REFUTED
#### 3. Quality Claims NOT VALIDATED
### Recommendations
#### Immediate Fixes Required
#### Strategic Validation (Phase 12 or Post-V1)
### Fix Tracking
```

**Assessment:**
- ✅ Excellent reduction (≥95%)
- Information density: HIGH (complete document outline)
- **Usefulness score**: 4.5/5

---

#### .planning/ROADMAP.md

- **Full size**: 12,523 bytes (3,130 tokens)
- **Metadata size**: 992 bytes (248 tokens)
- **Token reduction**: 92.1%
- **Cost savings**: $0.008646
- **Lines**: 260

**Metadata content:**
```
Document: ROADMAP.md
Type: .md
Lines: 260
Headers:
# Roadmap: Token-Efficient AI Coding Stack - V1 Comprehensive Audit
## Overview
## Domain Expertise
## Phases
## Phase Details
### Phase 1: Audit Foundation & Traceability
### Phase 2: AuZoom Core Verification
### Phase 3: AuZoom Structural Compliance
### Phase 4: Orchestrator Core Verification
### Phase 5: Validation Metrics Re-execution ✅ Complete (2026-01-13)
### Phase 6.5: Progressive Traversal & Graph Navigation Validation ⚠️ CRITICAL GAP
### Phase 7: Gemini Flash Real Integration (formerly Phase 6)
### Phase 8: Small File Overhead Assessment (formerly Phase 7)
### Phase 9: Non-Python File Handling Audit (formerly Phase 8) ✅ Complete (2026-02-11)
### Phase 10: Deferred Work Legitimacy Assessment (formerly Phase 9) ✅ Complete (2026-02-12)
### Phase 11: Integration Testing (formerly Phase 10)
### Phase 12: Gap Analysis & Reporting (formerly Phase 11)
### Phase 13: Critical Fixes & V1.1 Roadmap (formerly Phase 12)
## Progress
```

**Assessment:**
- ✅ Good reduction (90-95%)
- Information density: HIGH (complete document outline)
- **Usefulness score**: 4.5/5

---

#### .planning/PROJECT.md

- **Full size**: 8,051 bytes (2,012 tokens)
- **Metadata size**: 310 bytes (77 tokens)
- **Token reduction**: 96.2%
- **Cost savings**: $0.005805
- **Lines**: 150

**Metadata content:**
```
Document: PROJECT.md
Type: .md
Lines: 150
Headers:
# Token-Efficient AI Coding Stack - V1 Comprehensive Audit
## What This Is
## Core Value
## Requirements
### Validated
### Active
### Out of Scope
## Context
### Audit Motivation
### Existing Implementation
### Audit Philosophy
## Constraints
## Key Decisions
```

**Assessment:**
- ✅ Excellent reduction (≥95%)
- Information density: HIGH (complete document outline)
- **Usefulness score**: 4.5/5

---

### Toml Files

#### orchestrator/pyproject.toml

- **Full size**: 540 bytes (135 tokens)
- **Metadata size**: 167 bytes (41 tokens)
- **Token reduction**: 69.6%
- **Cost savings**: $0.000282
- **Lines**: 25

**Metadata content:**
```
Configuration: pyproject.toml
Type: .toml
Lines: 25
Size: 540 bytes

Structure:
Sections: build-system, project, project.optional-dependencies, tool.pytest.ini_options
```

**Assessment:**
- ⚠️ Low reduction (<80%) — expected for small config files
- Information density: HIGH (structural keys/sections)
- **Usefulness score**: 4/5

---

