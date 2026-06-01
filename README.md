# Ray Tracing in Python — Optimized Triangle BVH Version

## Overview

Educational ray tracer written from scratch in Python to study the core ideas of Whitted-style ray tracing and the practical impact of acceleration structures and performance-oriented refactoring.

The project started as a compact object-oriented renderer with spheres, planes, triangles, recursive reflections/refractions, and a classic BVH pipeline.  
In the current version, the renderer has been significantly reworked into a more modular and performance-oriented system focused on triangle-heavy scenes and imported OBJ geometry.

The current implementation now includes:

- a dedicated triangle data backend
- a triangle-specific BVH pipeline
- Numba-accelerated traversal and intersection kernels
- optimized shadow traversal
- tile-based parallel rendering
- OBJ benchmark scenes used for performance testing

This version represents the second major stage of the project, where the main goal was not only to render correctly, but also to study how much performance can be improved through structural refactoring and specialized acceleration logic.

---

## What Was Reworked in This Version

Compared to the earlier version of the project, the following changes were introduced:

- the project was split into separate modules instead of keeping the renderer in one monolithic file
- triangle-heavy scenes were moved to a dedicated scalar triangle backend
- triangle geometry is now preprocessed into numeric arrays instead of relying only on object-based triangle traversal
- a dedicated triangle BVH was introduced for OBJ-heavy scenes
- the hottest traversal and intersection parts were rewritten with Numba
- shadow rays for triangle scenes now use the optimized triangle BVH path
- triangle normals and centroids are precomputed during scene preparation
- the renderer now uses faster shading branches for simple opaque surfaces
- parallel rendering was redesigned around tile-based work distribution
- rendered tiles are returned as compact byte buffers instead of per-pixel Python tuples
- image-plane coordinates are precomputed for worker processes
- benchmark mode was cleaned up for triangle-only OBJ tests

---

## Current Features

### Core Rendering

- custom `Vec3` math
- `Ray` structure with origin and direction
- sphere intersection
- plane intersection
- triangle intersection
- nearest-hit search
- simple pinhole camera
- ambient + diffuse lighting
- shadow rays
- recursive reflections
- recursive refractions
- PNG output with Pillow

### Geometry and Scene Support

- spheres
- triangles
- OBJ meshes converted into triangle lists
- infinite plane surfaces
- reflective materials
- transparent / refractive materials
- benchmark scenes for synthetic and OBJ-based tests

### Acceleration and Performance

- precomputed AABB bounds
- classic BVH support
- triangle-specific BVH backend
- precomputed triangle normals
- precomputed triangle centroids
- Numba-accelerated triangle intersection
- Numba-accelerated AABB intersection
- Numba-accelerated triangle BVH closest-hit traversal
- Numba-accelerated triangle BVH shadow traversal
- tile-based multiprocessing renderer
- configurable worker count
- configurable tile size for benchmarks

---

## Current Rendering Pipeline

For each pixel, the renderer creates a primary ray from the camera through the virtual image plane.

For the closest visible hit point, the renderer computes:

- local ambient + diffuse contribution
- shadow visibility
- recursive reflection if the material is reflective
- recursive refraction if the material is transparent

The final color is built by combining local shading, reflection, and refraction according to the material parameters.

In triangle-heavy OBJ scenes, the renderer uses the dedicated triangle backend and the optimized triangle BVH instead of the older generic object traversal path.

---

## Acceleration Structure Used in the Current Final Version

The main acceleration structure of the current optimized version is a **triangle-oriented BVH**.

### Current optimized BVH pipeline includes:

- preprocessed triangle vertex arrays
- precomputed triangle AABBs
- precomputed triangle centroids
- flat BVH node layout
- closest-hit traversal optimized for triangle scenes
- shadow-block traversal optimized for triangle scenes
- Numba JIT acceleration for the hottest kernels

This version is designed specifically to study how far a Python-based ray tracer can be pushed before moving to the next stage of rendering experiments.

---

## Parallel Rendering

The renderer supports CPU parallel rendering through Python multiprocessing.

### Current parallel mode:

- the image is divided into square tiles
- tiles are distributed across worker processes
- each worker renders its own tile independently
- screen-space coordinates are precomputed
- tiles are returned as compact RGB byte buffers
- the final image is assembled by pasting rendered tiles back into the output image

This made the parallel version significantly cleaner and lighter than the earlier row/chunk-based approach.

---

## OBJ Mesh Loading

External `.obj` files can be loaded and converted into triangle geometry.

### Current approach:

- vertices are read from the OBJ file
- polygon faces are triangulated when necessary
- all imported geometry is converted into `Triangle` objects
- triangles are then transformed into triangle data arrays for the optimized backend
- imported meshes can be used in benchmark scenes and showcase scenes

This allows the renderer to test more realistic geometry instead of only synthetic primitive scenes.

---

## Current Project State

The current version should be understood as an **optimized Whitted-style ray tracing stage**.

The project already includes:

- a stable triangle BVH path
- triangle-oriented optimization
- Numba-accelerated hot kernels
- optimized shadow traversal
- parallel tile rendering
- OBJ-based benchmark support

This version is the main base for the next development stage.

---

## Benchmarking

The project includes benchmark scenes and timing measurements using `time.perf_counter()`.

The benchmark results are documented separately in:

[Benchmark Results](./BENCHMARK_RESULTS.md)

In the current optimization stage, the renderer was improved step by step through:

- moving from a generic object-based pipeline to a triangle-oriented backend
- simplifying data layout
- specializing the BVH for triangle scenes
- accelerating hot paths with Numba
- improving shadow traversal
- improving parallel tile rendering
- reducing Python-side overhead in shading and image assembly

---

## Run

Install the required packages:

```bash
pip install pillow numba numpy
```

Run the project:

```bash
python main.py
```

Output:

```text
render.png
```

---

## Current Limitations

The current version is already much stronger than the earlier implementation, but several limitations still remain:

- only a single main light source is used in the current stable version
- there is no texture mapping yet
- object transforms are still limited; imported geometry is currently repositioned and scaled, but not fully rotated through a general transform system
- imported OBJ materials are not parsed automatically yet
- there is no dedicated profiling subsystem yet for measuring how much time is spent in each rendering stage
- the project is still CPU-based and does not yet use GPU rendering
- Python still limits absolute performance compared to lower-level implementations

---

## Planned Next Steps

The next stage of the project is no longer only about basic ray tracing correctness, but about extending the renderer into a more advanced rendering framework.

### Planned improvements:

- add richer object transformation support, including object rotation
- add texture support for imported objects
- add a profiling / timing analysis system to measure where time is spent during rendering
- continue studying the relative cost of traversal, shading, shadow tests, and parallel overhead
- compare the current BVH approach with other spatial acceleration structures
- move toward path tracing as the next major rendering stage

The long-term direction is to evolve the project from an optimized Whitted-style ray tracer into a more advanced physically motivated renderer.

---

## Summary

This version represents the second major final stage of the ray tracing project.

It is no longer just a simple educational ray tracer with reflections and BVH.  
It is now a more structured and performance-aware renderer with:

- triangle-oriented data preparation
- optimized BVH traversal
- Numba-accelerated hot kernels
- optimized shadow handling
- tile-based multiprocessing
- OBJ-based triangle benchmarks

This version serves as the performance-oriented base for the next experimental stage: profiling, richer object interaction, texture support, and path tracing.
