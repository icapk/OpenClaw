# TASK: MyClaw Harness Phase 1 - Integration & Documentation

## Context

Phase 1 components are **already implemented** in MyClaw:

1. `ContextAssembler` — `~/MyClaw/src/context/context-assembler.ts`
   - 7-layer pipeline, feature flag (enabled=false by default), token budget, layer override
   - Fully tested in `context-assembler.test.ts`

2. `Stage1 Memory Automation` — `~/MyClaw/src/memory/stage1-memory-automation.ts`
   - Reads daily logs, extracts fragments, deduplicates, merges to MEMORY.md, archives to JSONL
   - Fully tested in `stage1-memory-automation.test.ts`
   - CLI: `node dist/memory/stage1-memory-automation.js --workspace <dir> --days 7`

## What Needs to Be Done

### 1. Wire ContextAssembler into MyClawCore (MyClaw/src/index.ts)

Modify `MyClawCore.assembleContext()` to optionally use the new `ContextAssembler`:

```typescript
// In MyClawCore constructor or assembleContext:
// If contextAssemblerEnabled is true, use new ContextAssembler
// Otherwise fall back to existing assembleLayeredContext
```

The new `ContextAssembler` should be stored as a field and used in `assembleContext()`.
Feature flag env var: `MYCLAW_CONTEXT_ASSEMBLER_ENABLED=true`

### 2. Wire Daily Stage1 Memory Consolidation into OpenClaw

The Stage1 Memory Automation script needs to run daily. Options:
- Create a cron script at `~/.openclaw/scripts/daily-memory-consolidation.sh`
- Or integrate into OpenClaw's existing cron/heartbeat system
- Should run: `node dist/memory/stage1-memory-automation.js --workspace ~/.openclaw/workspace --days 7 --verbose`

### 3. Create Documentation

Create `~/.openclaw/workspace/docs/myclaw-harness-phase1-usage.md` with:

```markdown
# MyClaw Harness Phase 1 - Usage Guide

## ContextAssembler

### Enabling the Enhanced Context System

Set environment variable:
```bash
export MYCLAW_CONTEXT_ASSEMBLER_ENABLED=true
```

Or in code:
```typescript
const assembler = new ContextAssembler({ enabled: true });
```

### 7-Layer Pipeline

| Layer | Priority | Override | Description |
|-------|---------|---------|-------------|
| base | 100 | ❌ | OpenClaw built-in system instructions |
| workspace | 90 | ✅ | AGENTS.md + SOUL.md + USER.md + IDENTITY.md + TOOLS.md |
| memory | 80 | ✅ | MEMORY.md content + compressed history |
| skill | 70 | ✅ | Active skill contents |
| session | 60 | ✅ | Recent session history (last 20 messages) |
| permission | 50 | ✅ | Permission level + allowed/blocked commands |
| inject | 40 | ✅ | Final assembled prompt → Model |

### Token Budget

Default: 8000 tokens. Configurable:
```typescript
const assembler = new ContextAssembler({
  tokenBudget: 12000,
  charsPerToken: 4,
});
```

### Layer Override Strategy

Higher-priority layers can override lower-priority ones when content conflicts.
Set `canOverride: false` for base layer to prevent any override.

## Stage1 Memory Automation

### Running Manually

```bash
node dist/memory/stage1-memory-automation.js \
  --workspace ~/.openclaw/workspace \
  --days 7 \
  --verbose
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--workspace <dir>` | cwd | Workspace directory |
| `--days <n>` | 7 | Look back N days |
| `--dry-run` | false | Preview without modifying |
| `--verbose` | false | Detailed output |
| `--no-archive` | false | Skip archiving |
| `--archive-dir <dir>` | memory/archived | Archive location |
| `--min-quality <f>` | 0.4 | Quality threshold 0-1 |

### How It Works

1. Reads all `memory/YYYY-MM-DD.md` files from last N days
2. Extracts high-value fragments:
   - **Decisions** (quality: high) — "decided to", "chose to", "agreed to"
   - **Facts** (quality: high) — "the goal is", "we are working on"
   - **Tasks** (quality: medium) — TODO, "need to", "next step"
   - **Preferences** (quality: high) — "i prefer", "my habit is"
3. Deduplicates against existing MEMORY.md (Jaccard similarity > 0.6)
4. Merges unique fragments into MEMORY.md
5. Archives source daily logs to JSONL at `memory/archived/YYYY-MM-DD.jsonl`
6. Deletes source daily log files

### Daily Automation Setup

Add to crontab (`crontab -e`):
```cron
# Run Stage1 Memory consolidation every day at 6am
0 6 * * * cd ~/MyClaw && node dist/memory/stage1-memory-automation.js --workspace ~/.openclaw/workspace --days 7 --verbose >> ~/.openclaw/logs/memory-consolidation.log 2>&1
```

### Fragment Quality

| Quality | Types | Included by default |
|---------|-------|---------------------|
| high | decision, fact, preference | ✅ |
| medium | task, general (section headings) | ✅ (if min-quality ≤ 0.3) |

### Programmatic Usage

```typescript
import { runConsolidation } from './memory/stage1-memory-automation';

const result = await runConsolidation({
  workspaceDir: '~/.openclaw/workspace',
  lookbackDays: 7,
  minQuality: 0.4,
  archive: true,
  dryRun: false,
  verbose: true,
});

console.log(`Merged ${result.merged} fragments, skipped ${result.skipped} duplicates`);
```

## Reversibility

Both Phase 1 features are **fully reversible**:

1. **ContextAssembler**: Set `MYCLAW_CONTEXT_ASSEMBLER_ENABLED=false` or `enabled: false` in config → reverts to legacy `assembleLayeredContext`
2. **Memory Automation**: Daily logs are archived to JSONL before deletion. To restore:
   ```typescript
   // Read archived JSONL and write back to memory/
   ```

## Architecture Diagram

```
User Input
    ↓
OpenClaw Runtime
    ↓
ContextAssembler (if enabled)  OR  Legacy Assembler
    ↓ (7-layer pipeline)         ↓ (L0-L3)
base_context                      base + workspace bootstrap
    ↓                                 ↓
workspace_context                  (memory injected separately)
    ↓
memory_context
    ↓
skill_context
    ↓
session_context
    ↓
permission_context
    ↓
inject_context → Model
```
```

## Integration with MyClawCore

```typescript
import { ContextAssembler } from './context/context-assembler';
import { assembleLayeredContext } from './context/assembler';

class MyClawCore {
  private contextAssembler: ContextAssembler;
  
  constructor(options: MyClawCoreOptions) {
    this.contextAssembler = new ContextAssembler({
      enabled: process.env.MYCLAW_CONTEXT_ASSEMBLER_ENABLED === 'true',
    });
  }
  
  async assembleContext(opts) {
    if (this.contextAssembler.isEnabled()) {
      return this.contextAssembler.assemble(opts);
    }
    // Legacy path
    return assembleLayeredContext(opts);
  }
}
```

## Testing

```bash
# Test ContextAssembler
cd ~/MyClaw && npm test -- --testPathPattern=context-assembler

# Test Stage1 Memory Automation
cd ~/MyClaw && npm test -- --testPathPattern=stage1-memory-automation

# Dry run memory consolidation
node dist/memory/stage1-memory-automation.js \
  --workspace ~/.openclaw/workspace --days 7 --dry-run --verbose
```
