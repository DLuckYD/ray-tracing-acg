# Benchmark Results

## Overview

This file summarizes the benchmark results collected for the current Python ray tracer implementation.

All measurements were performed on the same machine using the same codebase and benchmark setup for each comparison.

## Benchmark Setup

### Scene A — Final complex scene
Features:
- many objects
- reflections
- refractions
- shadow rays
- floor plane
- recursive ray tracing

### Scene B — Simplified cache benchmark scene
Features:
- large opaque foreground spheres
- many small background spheres
- designed to increase primary-ray coherence
- used to test the effect of primary-ray hit caching

## Tested Optimization

A simple cache-based optimization was implemented for **primary rays**.

The idea was to:
- store the previously hit primary object
- test that object first for the next primary ray
- then continue with the full nearest-hit search over the remaining objects

## Results

### Scene A — Final complex scene

Without cache:
- **166.252 s**

With cache:
- **174.204 s**

Difference:
- cache version was **7.952 s slower**
- approximately **4.8% slower**

Interpretation:
- the cache did not improve performance on the complex scene
- the scene cost is dominated by secondary rays such as shadows, reflections, and refractions
- the extra Python-level cache logic outweighed the benefit

---

### Scene B — Simplified cache benchmark scene

Without cache:
- **2.375 s**

With cache:
- **2.349 s**

Difference:
- cache version was **0.026 s faster**
- approximately **1.1% faster**

Interpretation:
- the cache produced a small positive effect
- neighboring primary rays were coherent enough to benefit slightly
- however, the improvement remained very small

---

### Scene C — Repeated simplified benchmark

With cache:
- **1.982 s**

Without cache:
- **1.976 s**

Difference:
- cache version was **0.006 s slower**
- approximately **0.3% slower**

Interpretation:
- the result is effectively within the measurement noise range
- no stable or significant performance improvement was observed

## General Conclusion

The cache-based optimization was implemented correctly from a functional point of view, but in the current Python implementation it did not provide a stable or meaningful speedup.

Main observations:
- on the complex scene, the cache made performance worse
- on the simplified scene, the cache showed either a very small speedup or a result within noise range
- the optimization effect is limited because the cache only helps primary rays, while complex scenes spend a large amount of time on secondary rays
- Python overhead reduces the practical benefit of this simple strategy

## Next Step

The current results suggest that more advanced acceleration structures are more promising for future optimization work, for example:
- uniform grids
- spatial partitioning
- other scene acceleration methods discussed in later lectures
