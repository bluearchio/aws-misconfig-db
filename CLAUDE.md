# AWS Misconfiguration Database - Claude Code Instructions

## Ingest Pipeline Workflow

When running the ingest pipeline (or when the user asks to "run the pipeline", "ingest", "fetch new recommendations", etc.), follow these steps **in order**:

### Step 1: Fetch & Stage
```bash
python3 scripts/ingest/cli.py fetch
```
This scans all enabled sources, deduplicates against existing recommendations, converts via Claude API, validates against schema, and stages new candidates in `data/staging/`.

For dry runs (no LLM conversion or staging):
```bash
python3 scripts/ingest/cli.py fetch --dry-run
```

### Step 2: Show Staged Recommendations to User
```bash
python3 scripts/ingest/cli.py show-staged --format detail
```
Always show staged recommendations to the user for review. Use `--format detail` so they can see full context including dedup scores and closest existing matches.

### Step 3: User Approves or Denies Each Recommendation
For each staged recommendation, ask the user whether to promote or reject it. Do NOT auto-promote.

- **Promote** (user approves):
  ```bash
  python3 scripts/ingest/cli.py promote <uuid>
  ```
- **Reject** (user denies):
  ```bash
  python3 scripts/ingest/cli.py reject <uuid> --reason "<reason>"
  ```

Always include a rejection reason when rejecting.

### Step 4: Post-Promote Validation & Regeneration
After all promote/reject decisions are made, if any recommendations were promoted:

```bash
# Validate schema compliance
python3 scripts/validate.py data/by-service/

# Regenerate SUMMARY.md and stats
python3 scripts/generate.py

# Rebuild DuckDB database
python3 scripts/db-init.py
```

### Step 5: Update README Totals
The README.md has hardcoded recommendation and service counts in two places:
1. The ASCII banner (line ~27): `🔥 NNN Recommendations • NN Services 🔥`
2. The footer (line ~569): `**🔥 NNN recommendations • NN services • ...`

After promoting, count the actual totals:
```python
import json
from pathlib import Path
total = sum(json.loads(f.read_text())['count'] for f in Path('data/by-service').glob('*.json'))
services = len(list(Path('data/by-service').glob('*.json')))
```

Then update BOTH locations in README.md with the new counts. Do not leave stale numbers.

### Step 6: Commit
After all updates, commit the changes with a message like:
```
Promote N ingest pipeline recommendations (OLD_COUNT → NEW_COUNT)
```

## Important Rules
- **Never auto-promote** staged recommendations without user review
- **Never skip validation** after promoting
- **Always update README totals** after promoting - they are hardcoded and will go stale
- The `status` field was removed from the schema - do not add it back
- JSON format: 2-space indent, `ensure_ascii=False`, trailing newline
- IDs are UUID v4, timestamps ISO 8601 UTC with Z suffix

## Project Structure
- **Source of truth**: `data/by-service/*.json`
- **Schema**: `schema/misconfig-schema.json`
- **Staging**: `data/staging/*.json`
- **Scripts**: `scripts/` (Python 3.9+)
- **Tests**: `tests/` (pytest)

## Running Tests
```bash
python3 -m pytest tests/ -v
```
