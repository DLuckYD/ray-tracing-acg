# Ray Tracing in Python

<!-- PLACEHOLDER: Insert render image here -->
<!-- Example: ![Render](path/to/render.png) -->

## Overview

Educational ray tracer written from scratch in Python to explore the core ideas of Whitted-style ray tracing and basic acceleration structures.

The project started as a simple sphere-based ray tracer and was gradually extended with reflections, refractions, triangles, object-level AABB acceleration, and a BVH-based traversal mode.

## Current Features

- custom `Vec3` math
- rays with origin and direction
- sphere intersection
- plane intersection
- triangle intersection
- nearest-hit search
- simple pinhole camera
- diffuse + ambient lighting
- shadow rays
- recursive reflections
- recursive refractions
- PNG output with Pillow
- benchmark scene generation
- blocker cache for shadow-ray obstruction tests
- precomputed AABB for objects
- BVH-based acceleration structure

## Scene Support

The current implementation supports:

- spheres
- triangles
- an infinite plane used as a floor
- reflective materials
- transparent / refractive materials
- benchmark scenes for both synthetic and more realistic tests

## How It Works

For each pixel, the renderer creates a primary ray from the camera through the virtual image plane.

For the closest hit point, the ray tracer computes:

- local diffuse and ambient lighting
- shadow visibility using shadow rays
- recursive reflection rays
- recursive refraction rays

The final color is built by combining local shading, reflected contribution, and refracted contribution.

## Acceleration Structures

The project currently includes multiple intersection modes:

- **Brute Force**  
  Every ray tests all objects directly.

- **AABB**  
  Each object provides a precomputed axis-aligned bounding box.  
  The ray first tests the bounding box before performing the exact intersection.

- **BVH**  
  Objects with finite AABBs are grouped into a bounding volume hierarchy.  
  Rays first traverse the hierarchy and only test exact intersections inside relevant leaf nodes.

These modes can be benchmarked and compared directly.

## Run

Install Pillow:

```bash
pip install pillow
```

Run the project:

```bash
python main.py
```

Output:

```text
render.png
```

## Benchmarking

The project includes benchmark scenes and timing measurements using Python's `time.perf_counter()`.

The benchmark results are documented separately in:

[Benchmark Results](./BENCHMARK_RESULTS.md)

## Current Benchmark Summary

Recent benchmarks show the following progression:

- **Brute Force** provides the baseline but scales poorly
- **AABB** gives a measurable speedup by rejecting some objects before exact intersection tests
- **BVH** provides the strongest improvement by rejecting entire groups of objects at once

This makes BVH the current best-performing acceleration method in the project.

## Current Limitations

- only one light source
- no anti-aliasing
- no mesh loading from external files
- no texture mapping
- no Fresnel-based material model yet
- infinite plane is not included inside BVH
- Python implementation limits absolute performance compared to lower-level languages

## Next Steps

Planned continuation of the project:

- improve lighting setup
- investigate kd-tree acceleration
- compare BVH and kd-tree performance
- explore more advanced spatial structures
- later extend the renderer with more complex geometry

## Render

<img width="2000" height="3000" alt="render" src="https://github.com/user-attachments/assets/52e3aaf1-6b53-45fd-b976-4301da81d8f0" />
