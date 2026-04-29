# Ray Tracing in Python

<!-- PLACEHOLDER: Insert render image here -->
<!-- Example: ![Render](path/to/render.png) -->

## Overview

Educational ray tracer written from scratch in Python to understand the core logic of Whitted-style ray tracing.

## Current Features

- custom `Vec3` math
- rays with origin and direction
- sphere intersection
- plane intersection
- nearest-hit search
- simple pinhole camera
- diffuse + ambient lighting
- shadow rays
- recursive reflections
- recursive refractions
- PNG output with Pillow
- benchmark scene generation
- initial cache-based optimization for primary rays

## Scene

The current project supports spheres, a plane as a floor, one point light source, configurable materials, and benchmark scenes with many objects.

## How it works

For each pixel, the renderer creates a ray from the camera through the image plane, finds the nearest object hit, computes local lighting, traces reflected and refracted rays recursively, and writes the final color to the image.

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

The project also includes benchmark scenes and timing measurements using Python's `time.perf_counter()`.

### Tested cache-based optimization

An initial optimization was implemented by caching the previously hit primary object and testing it first for the next primary ray.

### Results summary

**Scene A — Final complex scene**
- many objects, reflections, refractions, shadows, floor plane
- without cache: **166.252 s**
- with cache: **174.204 s**
- result: cache version was about **4.8% slower**

**Scene B — Simplified cache benchmark scene**
- large opaque foreground spheres and many small background spheres
- without cache: **2.375 s**
- with cache: **2.349 s**
- result: cache version was about **1.1% faster**

**Scene C — Repeated simplified benchmark**
- with cache: **1.982 s**
- without cache: **1.976 s**
- result: difference was about **0.3%**, effectively within measurement noise

Full benchmark details: see [Benchmark Results](./BENCHMARK_RESULTS.md).

### Conclusion

The cache-based optimization was implemented correctly, but in the current Python implementation it did not provide a stable or significant speedup. On complex scenes dominated by shadow, reflection, and refraction rays, the additional Python overhead outweighed the benefit. On simplified primary-ray-heavy scenes, the cache showed either a very small improvement or a result within the noise range.

This suggests that more advanced acceleration structures, such as uniform grids or other spatial partitioning methods, are more promising next steps.

## Current limitations

- only one light source
- no anti-aliasing
- no acceleration structures yet
- no mesh loading
- optimization effect is limited in Python for the current cache approach

## Render
<img width="1000" height="1000" alt="refactor_1" src="https://github.com/user-attachments/assets/1512a32b-b338-439d-a25c-a5eb9cb46d1f" />
