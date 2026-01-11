# Known Issues and Solutions

**Last Updated**: 2026-01-12

This document tracks issues discovered during implementation and their solutions.

## Gemini CLI Integration

### Issue 1: Rate Limits on Free Tier

**Problem**: Gemini Flash 3 free tier has very restrictive rate limits:
- 5 requests per minute
- Quota resets after 60 seconds
- Error: "You exceeded your current quota"

**Impact**: Running multiple validation tests hits the limit immediately

**Solution**: Implemented in Phase 3.5 - Execution modes:
- **Fast mode**: Switch to Claude Haiku immediately when rate limited
- **Cost-Effective mode**: Wait up to 60 seconds for rate limit reset

**Status**: Needs execution modes feature (Phase 3.5 deferred)

**Documentation updates needed**:
- ✅ Added rate limit info to KNOWN-ISSUES.md  - Add rate limit warning to README- Recommend sequential testing with 60s waits for free tier
- Add paid tier pricing information

### Issue 1.1: Daily Quota Exhaustion

**Problem**: Gemini Flash 3 free tier has very low daily quota:
- Only 250 requests per day total
- Easily exhausted during testing/development

**Error encountered**:
```
API Error: You have exhausted your daily quota on this model.
```

**Impact**: Cannot run full validation suite or test Gemini integration after quota exhausted

**Workarounds**:
1. Wait 24 hours for quota reset
2. Use paid tier (removes daily limit)
3. Implement fallback to Claude Haiku when quota exhausted (already works!)

**Status**: ✅ Executor correctly falls back to Haiku when Gemini fails - no action needed!

**Tested**: Gemini CLI works correctly when quota available, fallback to Haiku verified when quota exhausted

### Issue 2: Gemini CLI Acts as Agent, Not Simple Text Model

**Problem**: When given prompts like "Fix typo: change 'installtion' to 'installation'", Gemini CLI tries to use file system tools (search_file_content, read_file) instead of just returning corrected text.

**Error encountered**:
```
Error executing tool run_shell_command: Tool "run_shell_command" not found in registry
```

**Impact**: GeminiClient expects simple text responses, but gets tool execution attempts

**Workaround**: Use more explicit prompts that don't trigger tool use, e.g., "Just respond with the corrected word: installtion"

**Documentation updates needed**:
- Add note about Gemini CLI agent behavior
- Recommend specific prompt patterns for simple tasks
- Consider adding `--no-tools` flag if available

### Issue 3: GEMINI_API_KEY Environment Variable Required

**Problem**: Gemini CLI requires GEMINI_API_KEY to be set in environment

**Error**: "When using Gemini API, you must specify the GEMINI_API_KEY environment variable"

**Solution**:
- Updated installation scripts to check for API key
- Added instructions to set in shell profile
- GeminiClient now checks for API key and provides helpful error

**Documentation updates needed**:
- ✅ Added to INSTALL.sh
- ✅ Added to LINUX-INSTALL.md
- ✅ Added to README.md
- Add troubleshooting section for missing API key

### Issue 4: Incorrect CLI Command Structure

**Problem**: Original GeminiClient tried to use non-existent `gemini generate` subcommand with flags like `--model`, `--max-tokens`, `--prompt`

**Error**: Command not recognized by Gemini CLI

**Solution**: ✅ FIXED - Updated to correct syntax: `gemini -p "prompt"`

**Changes made**:
- Line 103-107 in gemini.py: Changed cmd to use `-p` flag
- Removed unsupported `--max-tokens` flag
- Added MODEL_MAPPING for future model selection support
- Added EnvironmentError handling for missing API key

**Status**: ✅ Resolved in commit (pending)

## Installation Issues

### Issue 5: Node.js Required for Gemini CLI

**Problem**: Gemini CLI requires Node.js 20+ which may not be installed

**Solution**:
- Added Node.js to prerequisites
- Updated all installation scripts to check/install Node.js

**Documentation updates needed**:
- ✅ Added to README requirements
- ✅ Added to LINUX-INSTALL.md prerequisites
- Add troubleshooting for Node.js version conflicts

## Testing Issues

### Issue 6: Can't Run Full Validation Suite Due to Rate Limits

**Problem**: Phase 5 validation tests would exceed free tier limits (5 req/min)

**Options**:
1. Run validation sequentially with 60s waits (slow but free)
2. Use paid tier for validation (fast but costs money)
3. Mock Gemini responses for validation (fast but not real)

**Recommendation**: Use Cost-Effective mode with sequential testing

**Documentation updates needed**:
- Add note about validation time with free tier
- Provide estimated validation time: ~20 minutes for full suite

## Documentation Improvements Needed

Based on issues discovered:

### README.md
- [ ] Add "Limitations and Known Issues" section
- [ ] Warn about Gemini free tier rate limits
- [ ] Add troubleshooting section
- [ ] Document execution modes more prominently

### INSTALL.sh
- [x] Check for Gemini CLI
- [x] Check for GEMINI_API_KEY
- [ ] Add retry logic for rate-limited API key validation

### LINUX-INSTALL.md
- [x] Add Node.js prerequisite
- [x] Add Gemini CLI installation
- [x] Add API key setup
- [ ] Add troubleshooting section

### Orchestrator README
- [ ] Document Gemini CLI syntax
- [ ] Add examples of prompt patterns that work well
- [ ] Warn about agent behavior vs simple text responses

### Validation Report
- [ ] Note rate limits encountered
- [ ] Document actual test execution time
- [ ] Add cost breakdown for paid tier validation

---

## Next Steps

1. Complete Phase 3: Update pricing in registry ($0.01 → $0.50)
2. Complete Phase 3.5: Implement execution modes
3. Test with Cost-Effective mode to avoid rate limits
4. Update all documentation based on issues above
5. Add comprehensive troubleshooting section to README
