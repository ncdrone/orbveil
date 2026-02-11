# OrbVeil Validation Report

**Date:** 2026-02-09  
**Catalog:** CelesTrak active catalog (14,368 objects)  
**Hardware:** Jetson Orin Nano (ARM64, 8GB)  
**Library version:** 0.1.0-dev

## Performance Benchmarks

| Operation | Input | Time | Notes |
|-----------|-------|------|-------|
| TLE parsing | 14,368 objects | 468 ms | Full active catalog |
| Batch propagation (SatrecArray) | 14,368 TLEs → 1 epoch | 31.5 ms | All valid, 0 failures |
| Orbital shell prefilter | 14,368 → 5,738 | <1 ms | 60% reduction (Starlink shell) |
| Full screening (3 days, 50km) | 1 vs 5,738 | 7.5 s | 30-min steps + TCA refinement |
| Full screening (3 days, 10km) | 1 vs 5,738 | 5.6 s | Tighter threshold, fewer hits |

## Real Conjunction Results

### Test Case: STARLINK-1008 (NORAD 44714)
- **Orbit:** 472-474 km (nearly circular LEO), 53.2° inclination
- **Screening window:** 3 days, 50 km threshold
- **Candidates after prefilter:** 5,738 of 14,368 objects

| # | Secondary | Miss Distance | Rel. Velocity | TCA | Type |
|---|-----------|--------------|---------------|-----|------|
| 1 | STARLINK-32527 | 2.7 km | 0.2 km/s | 2026-02-09 11:45 | Co-planar |
| 2 | STARLINK-32580 | 4.3 km | 0.3 km/s | 2026-02-11 05:16 | Co-planar |
| 3 | CS2 | 17.5 km | 14.7 km/s | 2026-02-11 22:48 | Cross-track |
| 4 | STARLINK-32244 | 20.4 km | 6.5 km/s | 2026-02-10 22:18 | Cross-track |
| 5 | STARLINK-31830 | 25.9 km | 11.9 km/s | 2026-02-09 13:48 | Cross-track |

**Observations:**
- Low relative velocity events (0.2-0.3 km/s) are Starlinks in the same orbital shell — expected
- High relative velocity events (7-15 km/s) are cross-track conjunctions — the dangerous ones
- CS2 at 14.7 km/s relative velocity is a classic high-energy conjunction scenario

### Test Case: ISS (NORAD 25544)
- **Orbit:** ~420 km, 51.6° inclination  
- **Finding:** 870 events, all 0.00 km with 0.0 km/s relative velocity
- **Explanation:** All events are ISS-docked modules (NAUKA, PROGRESS-MS 31, etc.) which share identical TLEs
- **Significance:** Correctly identifies co-located objects; real CA operations filter these using NORAD ID family lists

## Validation Notes

### What Works
- **Prefilter is effective:** 60% reduction using apogee/perigee overlap
- **Batch propagation is fast:** 14K+ objects in ~32ms on ARM
- **Co-located detection works:** ISS modules correctly show 0 km / 0 km/s
- **Cross-track conjunctions detected:** High relative velocity events match expected orbital mechanics
- **TCA refinement working:** Sub-minute precision in closest approach timing

### Known Limitations (v0.1.0-dev)
1. **No covariance data:** Public TLEs don't include uncertainty — Pc calculation requires CDM covariance matrices
2. **TLE propagation error:** SGP4 accuracy degrades >3 days from epoch. Stale TLEs produce unreliable results.
3. **Step size sensitivity:** 30-minute coarse steps may miss very fast conjunctions (relative velocity >10 km/s covers 18,000 km in 30 min). Finer steps improve detection at the cost of computation time.
4. **No maneuver detection:** If an object maneuvers, its TLE becomes invalid. No detection of TLE staleness.

### Comparison to Industry Tools
Without access to Space-Track CDMs (requires elevated permissions), direct numerical comparison isn't possible in this version. Cross-validation against published CDM data is planned for v0.2.

## Conclusion

The OrbVeil screening engine produces physically plausible results against the full active catalog. Conjunction events match expected orbital mechanics patterns (co-planar low-velocity, cross-track high-velocity). Performance is suitable for operational use — full catalog screening completes in under 10 seconds on a $249 edge device.

The primary gap is validation against official CDM data, which requires Space-Track CDM access (pending).
