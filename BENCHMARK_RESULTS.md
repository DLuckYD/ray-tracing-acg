# Benchmark Results

## Overview

This file summarizes the benchmark results collected for the current Python ray tracer implementation.

The project has gone through several optimization stages:
- cache-based experiments
- object-level AABB acceleration
- BVH acceleration
- parallel rendering with Python multiprocessing
- OBJ-based benchmark scenes

All measurements were performed on the same machine using the same codebase and benchmark setup for each comparison.

---

# New Benchmark Block — Parallel Rendering on OBJ Scene

## Overview

This section summarizes a new benchmark series focused on **parallel rendering performance** on an OBJ-based test scene.

The goal of this benchmark was to evaluate how the current multiprocessing-based renderer scales with different numbers of worker processes.

## Benchmark Setup

### Scene P — OBJ Parallel Benchmark Scene

Features:
- OBJ mesh loaded into the scene
- reflective and transparent objects
- spheres, triangles, and floor plane
- BVH enabled
- realistic recursive ray tracing workload

OBJ scene data:
- loaded OBJ file: **models/Sword.obj**
- OBJ vertices: **94**
- OBJ triangles: **184**
- total scene objects: **287**

### Benchmark Conditions

The following benchmark configuration was used:

```python
times, average_time = benchmark_render_parallel(
    runs=10,
    width=900,
    height=600,
    objects=objects,
    background_color=background_color,
    light_position=light_position,
    depth=0,
    max_depth=3,
    num_workers=num_workers
)
```

Additional rendering setup:
- parallel renderer
- chunk-based image splitting
- total chunks: **120**
- benchmark runs per worker configuration: **10**

## Model Reference

Placeholder for model source link:

- **OBJ model link:** `[PLACEHOLDER: insert model source link here]`

## Results

### Parallel Rendering Performance by Worker Count

| Worker Processes | Average Time (s) |
|------------------|------------------|
| 1                | **74.145**       |
| 2                | **36.837**       |
| 4                | **20.108**       |
| 8                | **11.869**       |
| 14               | **9.796**        |

## Speedup Relative to 1 Worker

### 2 Workers vs 1 Worker
- improvement: **37.308 s faster**
- approximately **50.3% faster**

### 4 Workers vs 1 Worker
- improvement: **54.037 s faster**
- approximately **72.9% faster**

### 8 Workers vs 1 Worker
- improvement: **62.276 s faster**
- approximately **84.0% faster**

### 14 Workers vs 1 Worker
- improvement: **64.349 s faster**
- approximately **86.8% faster**

## Interpretation

The new benchmark shows a strong positive scaling trend for the current multiprocessing-based renderer.

Main observations:
- moving from **1** to **2** worker processes nearly halves the render time
- **4 workers** already provide a major speedup over the single-process baseline
- **8 workers** continue to improve performance significantly
- **14 workers** provide the best result in the current benchmark setup
- the scaling is strong, but not perfectly linear, which is expected due to multiprocessing overhead, task scheduling overhead, and result collection costs

These results confirm that:
- the current chunk-based multiprocessing approach is effective
- the renderer benefits strongly from CPU parallelization
- the OBJ-based scene is complex enough to show meaningful scaling behavior

## Current Conclusion for Parallel Rendering

Parallel rendering is now one of the strongest practical optimizations in the project.

Compared to the single-process baseline, the renderer achieves:
- a **substantial reduction in render time**
- strong utilization of available logical CPU threads
- a clear performance benefit on realistic OBJ-based scenes

This makes multiprocessing an important optimization layer alongside:
- AABB
- BVH
- future load balancing improvements

## Placeholder — Render of One Very Complex Model

This section is reserved for a future benchmark and showcase render using a much more complex OBJ model.

Planned content:
- model name
- vertex count
- triangle count
- render settings
- benchmark results
- final render image

Template:

### Scene H — High-Complexity OBJ Model

Model information:
- model name: **[PLACEHOLDER]**
- vertices: **[PLACEHOLDER]**
- triangles: **[PLACEHOLDER]**
- source link: **[PLACEHOLDER]**

Render settings:
- width: **[PLACEHOLDER]**
- height: **[PLACEHOLDER]**
- max depth: **[PLACEHOLDER]**
- worker processes: **[PLACEHOLDER]**

Benchmark result:
- average render time: **[PLACEHOLDER]**

Render preview:
- **[PLACEHOLDER: insert image or link here]**

---

## Benchmark Setup

### Scene A — AABB Benchmark Scene

Features:
- many triangles
- several large foreground spheres
- no transparent materials in the benchmark focus
- designed to test object-level bounding box rejection
- resolution: **500 x 500**
- number of runs: **10**

![aabb_test.png](aabb_test.png)

## Tested Optimization

An **AABB-based acceleration step** was added to the ray-object search.

The idea is:
- each object provides its own bounding box
- the ray first tests the AABB
- only if the AABB is hit, the exact object intersection is computed

This reduces unnecessary exact intersection tests, especially for triangles and objects outside the main ray path.

## Results

### Scene A — AABB Benchmark Scene

Without AABB:
- **39.851 s**

With AABB:
- **31.788 s**

Difference:
- AABB version was **8.063 s faster**
- approximately **20.2% faster**

## Interpretation

The AABB optimization produced a clear performance improvement in the current benchmark scene.

Main observations:
- the ray tracer became significantly faster once AABBs were precomputed and reused
- the key implementation detail was to compute each object's AABB only once and return the stored box instead of rebuilding it during every intersection query
- triangle-heavy scenes benefit more from AABB than sphere-dominated scenes
- object-level rejection is already strong enough to produce a visible speedup in Python

## General Conclusion

AABB is the first acceleration method in the project that showed a **clear and stable improvement**.

Compared to the earlier cache-based optimization, AABB is much more effective because it reduces the number of expensive exact intersection tests instead of only trying to guess a good first candidate.

The current result suggests that the next logical steps are:
- hierarchical bounding volumes (HBV / BVH-like structures)
- spatial partitioning structures
- kd-trees or related acceleration trees

## Next Step

Planned continuation:
- keep AABB as the new baseline optimization
- experiment with hierarchical bounding volumes
- then investigate tree-based acceleration structures such as kd-trees

---

## Extended Benchmark Comparison

After the initial AABB benchmark, an additional comparison was performed on a more realistic scene containing reflective objects, transparent objects, spheres, triangles, and a floor plane.

### Scene B — Realistic Benchmark Scene

Features:
- reflective spheres
- transparent spheres
- multiple triangles
- floor plane
- more realistic spatial distribution of objects
- recursive ray tracing enabled
- resolution: **300 x 300**
- number of runs: **10**

## Tested Methods

Three intersection search strategies were compared:

- **Brute Force**  
  Every ray tests all objects directly.

- **AABB**  
  Each object provides a precomputed axis-aligned bounding box.  
  The ray first tests the AABB and only then performs the exact object intersection.

- **BVH**  
  Objects with finite AABBs are grouped into a bounding volume hierarchy.  
  Rays first traverse the hierarchy and only test exact intersections inside relevant leaf nodes.

## Results

### BVH

Average render time:
- **15.929 s**

### AABB

Average render time:
- **31.422 s**

### Brute Force

Average render time:
- **34.940 s**

## Direct Comparison

### AABB vs Brute Force

Difference:
- AABB was **3.518 s faster**
- approximately **10.1% faster**

### BVH vs AABB

Difference:
- BVH was **15.493 s faster**
- approximately **49.3% faster**

### BVH vs Brute Force

Difference:
- BVH was **19.011 s faster**
- approximately **54.4% faster**

## Interpretation

The new benchmark shows a clear hierarchy of effectiveness:

- **Brute Force** is the slowest approach because every ray tests all objects directly.
- **AABB** improves performance by rejecting some objects before exact intersection tests, but on this realistic scene the gain remains moderate.
- **BVH** provides the strongest result because it rejects entire groups of objects at once and drastically reduces the number of exact intersection tests.

This confirms that:

- object-level AABB is useful as a first optimization step,
- but hierarchical grouping of objects is significantly more powerful,
- especially in scenes with many objects distributed across different depths and heights.

## Updated General Conclusion

The benchmark progression now shows a clear development path:

1. **Brute Force** provides the baseline but scales poorly.
2. **AABB** gives a measurable improvement and serves as a necessary foundation.
3. **BVH** produces a major speedup and is the first hierarchical acceleration structure in the project to show strong performance gains.

These results support the next planned step of the project:
- keep **BVH** as the current strongest acceleration baseline,
- continue investigating more advanced structures,
- and later compare them with **kd-trees** or other spatial partitioning methods.

---

## Previous Cache-Based Benchmark Setup

### Scene C — Final complex scene
Features:
- many objects
- reflections
- refractions
- shadow rays
- floor plane
- recursive ray tracing

### Scene D — Simplified cache benchmark scene
Features:
- large opaque foreground spheres
- many small background spheres
- designed to increase primary-ray coherence
- used to test the effect of primary-ray hit caching

## Tested Cache-Based Optimization

A simple cache-based optimization was implemented for **primary rays**.

The idea was to:
- store the previously hit primary object
- test that object first for the next primary ray
- then continue with the full nearest-hit search over the remaining objects

## Cache Benchmark Results

### Scene C — Final complex scene

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

### Scene D — Simplified cache benchmark scene

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

### Scene E — Repeated simplified benchmark

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

## Cache Benchmark Conclusion

The cache-based optimization was implemented correctly from a functional point of view, but in the current Python implementation it did not provide a stable or meaningful speedup.

Main observations:
- on the complex scene, the cache made performance worse
- on the simplified scene, the cache showed either a very small speedup or a result within noise range
- the optimization effect is limited because the cache only helps primary rays, while complex scenes spend a large amount of time on secondary rays
- Python overhead reduces the practical benefit of this simple strategy
