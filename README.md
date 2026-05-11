# Ray Tracing in Python

<img width="2000" height="1500" alt="bvh" src="https://github.com/user-attachments/assets/e8c8daaa-495a-4105-890f-24cbffeedc99" />

## Overview

Educational ray tracer written from scratch in Python to study the core ideas of Whitted-style ray tracing and the effect of different acceleration techniques.

The project started as a simple sphere-based renderer and was gradually extended with reflections, refractions, triangles, precomputed AABBs, BVH traversal, OBJ mesh loading, and experimental parallel rendering.

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
- precomputed AABB for finite objects
- BVH-based acceleration structure
- OBJ mesh loading by converting faces into `Triangle` objects
- support for synthetic, realistic, and OBJ-based test scenes
- experimental parallel rendering with Python multiprocessing
- configurable worker process count
- chunk-based image splitting for parallel benchmark tests

## Scene Support

The current implementation supports:

- spheres
- triangles
- OBJ meshes converted into triangle lists
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
  Each finite object provides a precomputed axis-aligned bounding box.  
  The ray first tests the bounding box before performing the exact intersection.

- **BVH**  
  Objects with finite AABBs are grouped into a bounding volume hierarchy.  
  Rays first traverse the hierarchy and only test exact intersections inside relevant leaf nodes.

These modes can be benchmarked and compared directly.

## Parallel Rendering

The renderer also includes an experimental CPU parallel rendering mode based on Python multiprocessing.

Current parallel rendering setup:

- the image can be divided into row-based chunks
- chunks can be distributed across multiple worker processes
- the number of worker processes can be configured manually
- different chunking strategies can be tested for benchmarking and load balancing

This mode is used to explore practical CPU parallelization and to compare different scheduling strategies on the same ray-tracing core.

## OBJ Mesh Loading

The renderer can also import external `.obj` models.

Current approach:

- vertices are read from the OBJ file
- polygon faces are triangulated when needed
- all imported geometry is converted into the existing `Triangle` representation
- imported meshes automatically work with the current AABB and BVH pipeline

This makes it possible to place low-poly and medium-poly meshes directly into benchmark or showcase scenes.

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

- only one light source in the current stable version
- no anti-aliasing
- no texture mapping yet
- no Fresnel-based material model yet
- infinite plane is still handled outside BVH
- imported OBJ materials are not parsed yet; meshes currently use manually assigned material parameters
- parallel rendering is still experimental and under active testing
- Python implementation limits absolute performance compared to lower-level languages

## Next Steps

Planned continuation of the project:

- improve lighting setup
- extend benchmarking with newer test scenes
- investigate kd-tree acceleration
- compare BVH and kd-tree performance
- explore more advanced spatial structures
- continue improving parallel rendering and load balancing
- compare static and dynamic chunk scheduling
- later extend mesh support with material parsing

## Render

<img width="2000" height="3000" alt="render" src="https://github.com/user-attachments/assets/52e3aaf1-6b53-45fd-b976-4301da81d8f0" />
