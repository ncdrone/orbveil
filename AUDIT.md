# OrbVeil Library Audit Report

**Date:** 2025-02-09  
**Scope:** `src/orbveil/` (2,269 lines) + `tests/` (2,002 lines)  
**Auditor:** Automated deep review

---

## Executive Summary

OrbVeil is a well-structured, readable conjunction assessment library with clean module separation and solid test coverage of happy paths. The physics and math are fundamentally correct but have performance issues in screening (O(n²) per timestep with repeated single-object `propagate_batch` calls in refinement). **The biggest risk for v0.1.0 is the screening module's performance** — it will not scale to full catalog operations — and the **complete absence of logging** across all modules.

---

## Strengths

1. **Clean architecture** — `core/`, `data/`, `api/`, `utils/` separation is logical and has no circular dependencies
2. **Well-defined public API** — `__init__.py` exports are explicit with `__all__`; good top-level docstring
3. **`from __future__ import annotations`** used consistently in all source files (Python 3.10 compatible)
4. **No bare `except: pass` blocks** — the previously-reported bug class is absent
5. **Good docstrings** throughout — Google-style with Args/Returns/Raises sections
6. **Type hints** on all public functions and dataclass fields
7. **CDM parsing** is thorough — handles both KVN and XML formats, covariance matrix construction is correct
8. **Frozen TLE dataclass** — immutability prevents accidental mutation
9. **Test fixtures use real-world TLEs** (ISS, CSS, Hubble, GEO) — not fabricated data
10. **Formation detection** is a genuinely useful feature that most conjunction tools lack

---

## Critical Issues (Must Fix Before v0.1.0)

### C1. Screening refinement is catastrophically slow
**File:** `core/screening.py:164-199` (`_refine_tca`)

The refinement loop calls `propagate_batch([primary], current)` and `propagate_batch([secondary], current)` **individually per timestep** inside a while loop that halves step size from 1800s to 1s. That's ~10+ propagation rounds × many time samples per round. For each conjunction candidate, this creates hundreds of `SatrecArray` objects for single satellites.

**Fix:** Propagate both objects together in one `propagate_batch` call, or better yet, use `satrec.sgp4()` directly (no need for `SatrecArray` with n=1). Even better: compute the distance function analytically and use scipy's `minimize_scalar`.

### C2. Screening coarse search propagates primary separately every timestep
**File:** `core/screening.py:108-130`

`propagate_batch([prim], current_time)` is called inside the time loop, creating a new `SatrecArray` of size 1 each iteration. The primary should be propagated together with all candidates in a single batch call.

**Fix:** Combine `[prim] + candidates` into one `propagate_batch` call per timestep.

### C3. No logging anywhere
**Grep confirms:** zero `import logging` or `getLogger` calls in the entire library.

For a safety-critical library, this is unacceptable. Screening failures, propagation errors, CDM parse warnings, and API authentication events should all be logged.

**Fix:** Add `logger = logging.getLogger(__name__)` to each module. Log at DEBUG for routine operations, WARNING for degraded results, ERROR for failures.

### C4. `__init__.py` missing `from __future__ import annotations`
**File:** `__init__.py:1`

The top-level `__init__.py` is the only source file without the future annotations import. While it currently doesn't use any 3.10+ syntax, it should have it for consistency and to prevent breakage when someone adds type annotations.

### C5. CDM datetime parsing lacks timezone awareness
**File:** `data/cdm.py:173-180` (`_parse_datetime`)

Parsed datetimes are naive (no tzinfo). CDMs are always UTC per CCSDS standard. This will cause issues when comparing with timezone-aware datetimes (e.g., risk assessment's `datetime.now(timezone.utc)` comparison).

**Fix:** Add `tzinfo=timezone.utc` to all parsed datetimes, or use `.replace(tzinfo=timezone.utc)`.

### C6. `tle.py` uses inline `__import__()` calls
**File:** `core/tle.py:77-84`

```python
__import__("datetime").timedelta(days=day_of_year - 1)
__import__("math").pi
```

This is called multiple times inside `from_lines`. It's ugly, hard to read, and slightly slower. `math` and `timedelta` are already available or trivially importable.

**Fix:** Add `import math` and `from datetime import timedelta` at the top of the file.

---

## Recommended Improvements (Should Fix)

### R1. `constants.py` is unused by the library itself
**File:** `utils/constants.py`

The constants (e.g., `EARTH_RADIUS_KM`, `DEFAULT_MISS_DISTANCE_KM`) are defined but never imported by any module. `screening.py` hardcodes `MU = 398600.4418` and `RE = 6378.137` locally.

**Fix:** Import from `constants.py` or remove the file.

### R2. Screening memory usage for large catalogs
**File:** `core/screening.py:100-130`

The coarse search stores all detection windows in a dict. For a full 25,000-object catalog with many candidates, `potential_windows` could accumulate large state vectors in memory.

**Fix:** Process conjunctions incrementally or limit window storage. Consider yielding events as a generator.

### R3. `ConjunctionEvent` is mutated in dedup logic
**File:** `core/screening.py:147-152`

```python
existing.tca = tca
existing.miss_distance_km = min_dist
```

This mutates dataclass instances after creation. Should use a replacement pattern or make ConjunctionEvent non-frozen explicitly (it's not frozen, but mutation during iteration is fragile).

### R4. SpaceTrack client has no rate limiting
**File:** `data/spacetrack.py`

Space-Track enforces rate limits. The client has no retry logic, no backoff, and no rate tracking. `fetch_catalog()` for the full catalog could hit limits.

**Fix:** Add `time.sleep()` between requests, or use a rate limiter. At minimum, document the limitation.

### R5. CDM KVN parser is fragile with object section splitting
**File:** `data/cdm.py:89-106`

The parser tracks `current_obj` state while iterating lines, but the first pass already consumed all `key=value` pairs into a flat `data` dict. The second pass re-iterates the same lines with object context. This means header fields like `TCA` get into the flat dict on the first pass, but object fields also get into the flat dict (without object prefix). The object-specific second pass works because it only stores when `current_obj` is set.

This is correct but fragile — a CDM with a field name that appears in both header and object sections would collide in the flat `data` dict. Not a real-world issue (CCSDS field names are unique), but the design is confusing.

### R6. Risk module uses `datetime.now()` — not testable
**File:** `core/risk.py:55-58`

```python
now = datetime.now(timezone.utc)
```

This makes urgency calculations non-deterministic and hard to test. Tests work around it by computing TCA relative to "now", but this is fragile.

**Fix:** Accept `now` as an optional parameter (default `None` → `datetime.now(timezone.utc)`).

### R7. Formations module has O(n²) velocity-based detection
**File:** `core/formations.py:130-152`

The nested loop checks all unassigned pairs. For large catalogs this is O(n²). A KD-tree would make this O(n log n).

### R8. `propagation.py` imports `math` but never uses it
**File:** `core/propagation.py:5`

`import math` is unused.

---

## Nice-to-Haves

1. **KD-tree screening** — The `daily_screening.py` script apparently uses KD-tree. This approach should be in the library, not in a script. It would solve C1/C2 performance issues.
2. **Alfano closed-form Pc** — Foster numerical integration is slow for operational use. Alfano (2005) or Chan (2008) closed-form approximations would be 100-1000x faster.
3. **RTN-to-ECI covariance rotation** — CDM covariance is in RTN frame, but `compute_pc` expects ECI. There's no rotation utility. Users must do this themselves.
4. **CDM export** (`to_kvn`) — Currently raises `NotImplementedError`. Useful for testing and interop.
5. **Thread safety** — No global mutable state, so the library is inherently thread-safe. Good.
6. **GPU acceleration** — Given the Jetson target, CuPy-accelerated batch operations could be valuable for full-catalog screening.

---

## Module-by-Module Notes

### `core/tle.py`
- **Good:** Frozen dataclass, proper validation, handles 2-line and 3-line formats
- **Issue:** `__import__("math")` and `__import__("datetime")` inline calls (C6)
- **Issue:** `parse_tle` silently skips unrecognized lines (`i += 1`) — should this warn?
- **Note:** Checksum validation is not performed on TLE lines

### `core/propagation.py`
- **Good:** Clean separation of single vs batch propagation, proper error codes
- **Good:** `propagate_batch` correctly uses `SatrecArray` for C-level vectorization
- **Issue:** Unused `import math` (R8)
- **Edge case:** `propagate` raises `ValueError` on SGP4 error — good

### `core/screening.py`
- **Critical:** Performance issues (C1, C2)
- **Good:** Multi-stage algorithm (prefilter → coarse → refine) is architecturally sound
- **Good:** Deduplication of near-simultaneous detections
- **Issue:** `_refine_tca` initial_step_sec default is 1800 but called with `step_minutes * 30` which = 1800 for default 60min step — confusing parameterization
- **Issue:** Hardcoded MU/RE instead of using constants (R1)

### `core/probability.py`
- **Good:** B-plane projection is mathematically correct
- **Good:** Foster numerical integration handles singular covariance gracefully
- **Good:** Monte Carlo method projects to B-plane for consistency with Foster
- **Issue:** `dblquad` in polar coordinates is slow; for operational Pc, Alfano's series expansion would be better
- **Edge case:** Zero relative velocity handled with fallback to arbitrary plane — acceptable

### `core/risk.py`
- **Good:** Clear factor decomposition, human-readable recommendations
- **Good:** Floor rule for <0.5km approaches regardless of multipliers
- **Issue:** `datetime.now()` call makes testing fragile (R6)
- **Issue:** Exponential decay constant `k=0.15` is hardcoded — should be configurable or documented
- **Note:** Risk scoring is heuristic (not physics-based Pc). This is fine but should be documented clearly.

### `core/formations.py`
- **Good:** Comprehensive detection covering ISS, CSS, TanDEM-X, MEV, prefix-based, velocity-based, COSPAR-based
- **Issue:** Hardcoded formation databases will go stale (e.g., new dockings, new formations)
- **Issue:** O(n²) velocity detection (R7)
- **Issue:** COSPAR rideshare detection's close_pairs logic has a bug — it skips pairs where either index is already in another pair, but this could miss valid groupings. The `if i not in [idx for pair in close_pairs for idx in pair]` check is O(n²) per pair.
- **Note:** `Optional` import is unused (line 4: `from typing import Optional`)

### `data/cdm.py`
- **Good:** Handles both KVN and XML, covariance matrix construction is correct
- **Issue:** Naive datetimes (C5)
- **Issue:** XML parser's `find_text` helper is fragile with namespace handling — multiple fallback strategies
- **Note:** No validation that covariance matrix is positive semi-definite

### `data/spacetrack.py`
- **Good:** Session-based auth with re-auth on 401
- **Issue:** No rate limiting (R4)
- **Issue:** CDM splitting by `"CCSDS_CDM_VERS"` string is fragile — what if that string appears in a COMMENT?
- **Issue:** `fetch_cdms` silently swallows parse errors with `continue` — should log

### `api/client.py`
- **Fine for now** — placeholder with `NotImplementedError`. Clean design.
- Uses `TYPE_CHECKING` guard properly to avoid circular imports.

### `utils/constants.py`
- **Good:** Well-documented with units
- **Issue:** Not used by any library module (R1)

---

## Test Gap Analysis

### What's Well Tested
- TLE parsing (happy path + error cases) ✅
- Propagation (single, batch, empty, consistency) ✅
- Screening structure and filtering (prefilter, self-exclusion, sorting) ✅
- Probability (Foster, Monte Carlo, edge cases, method agreement) ✅
- Risk scoring (full matrix of scenarios) ✅
- Formations (all detection types, boundary conditions) ✅
- CDM parsing (KVN, XML, missing fields) ✅

### What's NOT Tested
1. **`api/client.py`** — No tests at all (it's a stub, but still)
2. **`utils/constants.py`** — No tests (just constants, acceptable)
3. **CDM `to_kvn()`** — No test for the `NotImplementedError` path
4. **SpaceTrack client methods** — Only `__init__` tested; no mocked HTTP tests for `fetch_tle`, `fetch_catalog`, `fetch_cdms`. This is a significant gap.
5. **Propagation with stale/decayed TLEs** — No test for TLEs propagated far beyond epoch validity
6. **Screening with empty catalog** — `screen(tle, [])` not tested
7. **Screening with single-object catalog** (only self) — implicitly tested via prefilter but not as integration test
8. **CDM roundtrip** — Parse → export → re-parse not tested (export not implemented)
9. **NaN/inf positions** from propagation failures flowing into screening
10. **Large catalog screening** — No test with >10 objects; performance not benchmarked
11. **Formation `detect_formations` with mismatched array lengths** — `ValueError` path not tested
12. **Risk `classify_events` with bad input** — No test for missing keys
13. **CDM XML with no namespace** — Only tested with namespace present

### Test Quality Notes
- Tests use real TLE data — good for confidence
- Probability tests verify physical monotonicity (closer → higher Pc) — excellent
- Screening tests are necessarily slow (actual SGP4 propagation) — consider marking slow tests
- No performance/benchmark tests
- No property-based testing (hypothesis)

---

## Specific Code Fixes

| Priority | File:Line | Issue | Fix |
|----------|-----------|-------|-----|
| **CRITICAL** | `screening.py:164-199` | Single-object propagate_batch in tight loop | Use `satrec.sgp4()` directly or batch both objects |
| **CRITICAL** | `screening.py:108-112` | Primary propagated alone per timestep | Combine with candidates in single batch |
| **CRITICAL** | All modules | No logging | Add `logging.getLogger(__name__)` |
| HIGH | `tle.py:77-84` | `__import__()` inline calls | Normal imports at top |
| HIGH | `cdm.py:173-180` | Naive datetimes | Add `tzinfo=timezone.utc` |
| HIGH | `__init__.py:1` | Missing future annotations | Add `from __future__ import annotations` |
| MEDIUM | `screening.py:13-14` | Hardcoded MU/RE | Import from `constants.py` |
| MEDIUM | `risk.py:55` | `datetime.now()` in logic | Accept `now` parameter |
| MEDIUM | `propagation.py:5` | Unused `import math` | Remove |
| MEDIUM | `formations.py:4` | Unused `from typing import Optional` | Remove |
| MEDIUM | `spacetrack.py:fetch_cdms` | Silent error swallowing | Add logging |
| LOW | `formations.py:173-178` | O(n²) close_pairs membership check | Use a set |
| LOW | `constants.py` | Unused by library | Wire up or document as user-facing only |

---

## Verdict

**Not ready for v0.1.0 release as-is.** The screening performance issues (C1, C2) mean it works for demos but will fail on real operational catalogs. The lack of logging (C3) is a non-starter for safety-critical software.

**Estimated effort to fix critical issues:** 2-3 days.  
**Estimated effort to fix all recommended improvements:** 1 week.

The foundation is solid. The architecture is clean, the math is correct, and the test coverage is good. Fix the performance and observability issues and this is a credible v0.1.0.
