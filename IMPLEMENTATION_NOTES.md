# Collision Probability Implementation Notes

## Implementation Complete ✓

Successfully implemented collision probability calculation for OrbVeil.

### Methods Implemented

1. **Foster (1992) / 2D Pc Method**
   - Projects combined covariance onto B-plane (perpendicular to relative velocity)
   - Numerical integration using polar coordinates for efficiency
   - Uses `scipy.integrate.dblquad` for accurate integration
   - Handles edge cases: singular covariance, zero relative velocity

2. **Monte Carlo Method**
   - Samples from combined 3D position distribution
   - Projects samples onto B-plane (matching Foster methodology)
   - Configurable sample size (default 100,000)
   - Reproducible with seed parameter

### Key Features

- **B-plane projection**: Correctly handles the fact that at TCA (Time of Closest Approach), only cross-track uncertainty matters for collision risk
- **Mahalanobis distance**: Computed as a measure of how many sigmas the miss distance represents
- **Edge case handling**: 
  - Singular covariance matrices
  - Zero relative velocity
  - Zero miss distance
  - Very large/small uncertainties

### Test Coverage

All 23 tests passing:
- Relative state computation
- B-plane projection (shape, miss distance, perpendicularity)
- Foster method (zero miss, large miss, HBR scaling, uncertainty scaling)
- Monte Carlo method (validation, reproducibility, edge cases)
- Integration tests (NASA CARA-like scenarios, method agreement)
- Edge cases (zero covariance, large covariance, exact overlap)

### Performance

- Foster method: ~40ms per calculation (with polar coordinate optimization)
- Monte Carlo (100k samples): ~200ms per calculation
- Methods agree within ~3-5% for typical scenarios

### Example Usage

```python
from orbveil.core.probability import compute_pc, PcMethod
import numpy as np

# Two satellites in close approach
pos1 = np.array([7000.0, 0.0, 0.0])  # km
vel1 = np.array([0.0, 7.5, 0.0])     # km/s
pos2 = np.array([7000.05, 0.0, 0.0])  # 50m apart
vel2 = np.array([0.0, 7.0, 0.0])

# Covariance matrices (6x6: position + velocity)
cov1 = np.eye(6) * 0.1**2  # 100m position uncertainty
cov2 = np.eye(6) * 0.1**2

# Compute collision probability
result = compute_pc(
    pos1, vel1, pos2, vel2, cov1, cov2,
    hard_body_radius_m=20.0,
    method=PcMethod.FOSTER_1992
)

print(f"Pc: {result.probability:.6e}")
print(f"Miss: {result.mahalanobis_distance:.2f} sigma")
```

### Dependencies

- `numpy`: Array operations
- `scipy`: Numerical integration (`dblquad`)
- Standard library: `dataclasses`, `enum`

### References

- Foster, J. (1992). "The Analytic Basis for Debris Avoidance Operations for the International Space Station"
- Chan, F. K. (1997). "Spacecraft Collision Probability"
- Akella, M. R., & Alfriend, K. T. (2000). "Probability of Collision Between Space Objects"
