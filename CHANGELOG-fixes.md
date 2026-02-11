# OrbVeil Library Fixes — 2026-02-09

## Summary

Audit-driven fixes for critical issues identified in `AUDIT.md` and `TECHNICAL-AUDIT.md`.

## Changes

### 1. Logging added throughout (C3) ✅
Already present in all core modules: `screening.py`, `propagation.py`, `risk.py`, `formations.py`, `tle.py`, `cdm.py`, `spacetrack.py`, `probability.py`. Each uses `logging.getLogger(__name__)` with DEBUG/INFO/WARNING/ERROR levels as appropriate.

### 2. Timezone handling fixed (C5) ✅
- `cdm.py:_parse_datetime()` returns timezone-aware UTC datetimes via `.replace(tzinfo=timezone.utc)`
- `screening.py` uses `datetime.now(timezone.utc)` for reference times
- `tle.py` creates epochs with `tzinfo=timezone.utc`
- `risk.py` uses `datetime.now(timezone.utc)` and handles naive TCA datetimes

### 3. `now` parameter added to risk.py (R6) ✅
`assess_risk()` accepts optional `now: datetime | None` parameter for testability. Defaults to `datetime.now(timezone.utc)` when not provided.

### 4. `from __future__ import annotations` added to ALL Python files (C4) ✅
Previously missing from 5 files:
- `src/orbveil/core/__init__.py`
- `src/orbveil/data/__init__.py`
- `src/orbveil/api/__init__.py`
- `src/orbveil/utils/__init__.py`
- `src/orbveil/utils/constants.py`

Now present in every `.py` file under `src/orbveil/`.

### 5. `__import__()` calls removed (C6) ✅
`tle.py` uses proper `import math` and `from datetime import timedelta` at module level.

### 6. Screening performance fixes (C1, C2) ✅
- `screen()` batches primary + candidates in single `propagate_batch()` call (C2 fix)
- `_refine_tca()` uses direct `satrec.sgp4()` calls instead of `propagate_batch` (C1 fix)
- `_sgp4_single()` helper added for efficient single-object propagation
- Constants imported from `utils/constants.py` instead of hardcoded (R1)

### 7. Unused imports cleaned (R8) ✅
- `propagation.py`: unused `import math` removed
- `screening.py`: imports `MU` and `RE` from `constants.py`

## Test Results
All 143 tests pass.
