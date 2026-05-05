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
<img width="500" height="500" alt="render" src="https://github.com/user-attachments/assets/05601796-70c3-48e9-bc1d-cdf83b3f2e40" />

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
- resolution: **200 x 300**
- number of runs: **10**

<img width="200" height="300" alt="render" src="https://github.com/user-attachments/assets/6b225b2e-144f-47b0-997b-c8b963b0113f" />

## Tested Methods

Three intersection search strategies were compared:

- **Brute Force**  
  Every ray tests all objects directly.

- **AABB**  
  Each object provides a precomputed axis-aligned bounding box.  
  The ray first tests the AABB and only then performs the exact object intersection.

- **BVH**  
  Objects with finite AABBs are grouped into a bounding volume hierarchy.  
  Rays first traverse the hierarchy and only test exact object intersections inside relevant leaf nodes.

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
