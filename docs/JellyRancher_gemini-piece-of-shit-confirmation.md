# Gemini CLI: Piece of Shit Confirmation

**Date:** 2025-11-14  
**Analysis Source:** `checkpoint-shitball.json` conversation log

## Executive Summary

Gemini CLI has systemic failures that make it unusable for serious development work. Most critically, it **destroyed the user's entire development journal** by overwriting it when the model intended to append.

## Critical Failures Documented

### 1. Shell Command Execution: 100% Failure Rate

**Evidence from checkpoint:**
- Every single `run_shell_command` call fails with: `"Command rejected because it could not be parsed safely"`
- Failed commands include:
  - Simple Python one-liners: `python -c "import datetime; print(...)"`
  - Basic PowerShell: `Get-Date -Format "..."`, `Remove-Item -Path ...`
  - Windows commands: `del temp_time.py`
  - Even plain text messages (line 764)

**Impact:** Cannot perform basic file operations, get timestamps, or execute any shell commands.

### 2. Code Editing: Regex Stack Overflow

**Evidence from checkpoint (line 163):**
- `replace` function generates invalid regex patterns when trying to match large code blocks
- Error: `"Invalid regular expression: /^(\\s*)from\\s*scripts\\.media\\.media_metadata_lookup..."` (hundreds of lines of escaped regex)
- Causes stack overflow errors
- Model acknowledges: `"replace failed due to size. I'll break it down."`

**Impact:** Cannot edit large code files. Forces breaking edits into tiny pieces, making development workflow painful.

### 3. Network Operations: Complete Failure

**Evidence from checkpoint (line 524):**
- `web_fetch` fails with: `"Error during fallback fetch for https://worldclockapi.com/api/json/utc/now: fetch failed"`
- Multiple attempts to get current time all fail

**Impact:** Cannot fetch data from web APIs, breaking functionality that depends on external data.

### 4. DATA DESTRUCTION: Journal Overwritten

**The Most Critical Failure - Evidence from checkpoint:**

**Line 662:** Model says: *"I'll **append** the Phase 23 entry to `agent-journal.md`"*

**Line 668-669:** Uses `write_file` with **ONLY** Phase 23 content (not the full file)

**Line 683:** Response: *"Successfully **overwrote** file"* - NOT appended, **OVERWROTE**

**Line 1022 & 1053:** Model realizes mistake: *"I only see Phase 23. I need the full `agent-journal.md`"*

**What Happened:**
1. Model intended to **append** Phase 23 to existing journal
2. Gemini CLI's `write_file` function **only supports overwrite** (no append mode)
3. Tool overwrote entire file with just Phase 23
4. **Phases 1-22 completely deleted**
5. Model didn't realize until later when trying to add attribution

**Impact:** Complete loss of development history. This is not a limitation - this is **data destruction** caused by a fundamental design flaw.

## Root Cause Analysis

### Design Flaws

1. **Overly Restrictive Command Parser**
   - Security-first approach that blocks ALL commands
   - No distinction between safe and unsafe commands
   - Even basic, harmless commands are rejected

2. **No Append Operation**
   - `write_file` only supports overwrite
   - No `append_file` or similar function
   - Model cannot append to files, only overwrite
   - This directly led to data loss

3. **Regex Generation Doesn't Scale**
   - Tries to match entire large code blocks as single regex
   - Creates invalid patterns that cause stack overflows
   - No fallback or chunking mechanism

4. **Network Fetch Unreliability**
   - Basic HTTP requests fail
   - No retry logic or error handling

## What Actually Works

- `write_file` (for new files or intentional overwrites)
- Small `replace` operations (on small code blocks)
- `read_file` operations

**That's it.** Everything else fails.

## Verdict

**Gemini CLI is a piece of shit.**

This is not hyperbole. A tool that:
- Cannot run basic shell commands (100% failure rate)
- Cannot edit large code files (regex failures)
- Has no append operation (only overwrite)
- **Destroys user data** when the model intends to append
- Has unreliable network operations

...is not just broken. It's **dangerous** and **unfit for production use**.

The journal deletion alone makes this tool unacceptable. The combination of all these failures makes it completely unusable for serious development work.

## Recommendations

1. **Do not use Gemini CLI** for any critical work
2. **Check backups** - the journal may be recoverable from backup files
3. **Report these issues** to Google/Gemini team (if they have a bug tracker)
4. **Use alternative tools** that actually work

## Evidence Location

All evidence documented in: `checkpoint-shitball.json`
- Shell command failures: Lines 461, 493, 556, 651, 715, 747, 779
- Regex failure: Line 163
- Web fetch failure: Line 524
- Journal overwrite: Lines 662-683, 1022-1053

---

*This document serves as a permanent record of Gemini CLI's systemic failures and the data loss it caused.*

