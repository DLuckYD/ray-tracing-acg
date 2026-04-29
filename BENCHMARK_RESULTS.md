# Benchmark Results

## Overview

This file summarizes the benchmark results for the current Python ray tracer implementation after introducing **AABB (Axis-Aligned Bounding Boxes)**.

All measurements were performed on the same machine using the same codebase and the same benchmark scene for each comparison.

## Benchmark Setup

### Scene A — AABB Benchmark Scene

Features:
- many triangles
- several large foreground spheres
- no transparent materials in the benchmark focus
- designed to test object-level bounding box rejection
- resolution: **500 x 500**
- number of runs: **10**
- 
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
