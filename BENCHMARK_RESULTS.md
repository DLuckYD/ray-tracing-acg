# Benchmark Results

## Overview

This document summarizes the **current benchmark state** of the optimized Python ray tracer.

It focuses on the **current implementation**, not the full historical optimization path.  
The current renderer includes:

- optimized triangle-oriented BVH
- Numba-accelerated triangle intersection
- Numba-accelerated AABB traversal
- Numba-accelerated closest-hit BVH traversal
- Numba-accelerated shadow traversal
- tile-based multiprocessing
- OBJ-based benchmark scenes

This file is intended to describe the **present performance profile** of the renderer and to serve as the current benchmark baseline before the next development stage.

---

## Benchmark Environment

### Machine / Software

- **CPU:** AMD Ryzen 7 7800X3D ( 8 Cores And 16 Threads )
- **RAM:** G.Skill Trident Z5 32 GB 2 x 16 GB DDR5 (4800 MT/s)
- **Python version:** 3.12.3
- **Operating system:** Windows 11 Home 25H2
- **Numba version:** 0.65.1
- **Numpy version:** 2.4.6

### Shared Benchmark Settings

Unless otherwise noted, the current benchmark runs below use:

- **resolution:** `2000 × 1300`
- **max depth:** `3`
- **runs:** `11`
- **workers:** `10`
- **tile size:** `24`

### Benchmark Notes

- Averages below include all recorded runs.
- The first run may include extra warm-up overhead.
- Where useful, a short comparison with older pre-optimization timings is included.
- Image placeholders are left in the file so render previews can be inserted later.

---

## Scene 1 — Large OBJ Triangle Benchmark

### Scene Description

This scene is the main **triangle-heavy benchmark** of the current project.  
It is used to evaluate the optimized triangle BVH path on a large imported OBJ mesh.

### Scene Data

- **scene name:** `build_obj_test_scene()`
- **model file:** `casa.obj`
- **vertices:** `17158`
- **triangles:** `33817`
- **total renderable objects:** `33817`
- **contains non-triangle objects:** `No`

### Render Settings

```python
times, average_time = benchmark_render_parallel_tiles(
    runs=11,
    width=2000,
    height=1300,
    objects=objects,
    background_color=background_color,
    light_position=light_position,
    depth=0,
    max_depth=3,
    num_workers=10,
    tile_size=24
)
```

### Results

All runs:

- Run 1: `10.008 s`
- Run 2: `10.074 s`
- Run 3: `10.612 s`
- Run 4: `10.474 s`
- Run 5: `10.558 s`
- Run 6: `10.420 s`
- Run 7: `10.480 s`
- Run 8: `10.611 s`
- Run 9: `10.368 s`
- Run 10: `10.669 s`
- Run 11: `10.648 s`

Summary:

- **average runtime over all runs:** `10.448 s`
- **best run:** `10.008 s`
- **worst run:** `10.669 s`

### Comparison with Earlier Version

Older result mentioned for this scene:

- **older timing:** `314.539 s`
- **older settings:** `3000 × 3000`, max depth `3`, workers `10`

This older number was produced before the current optimized triangle-oriented version and is kept here only as a rough historical comparison point.

### Render Preview

<img width="2000" height="1300" alt="render_1" src="https://github.com/user-attachments/assets/ac4f66ca-d6db-4fc0-9d35-1777056866cd" />


### Notes

- This is the main benchmark scene for the optimized triangle BVH implementation.
- It represents the strongest current large-OBJ test case in the project.
- A separate worker/tile-size sweep for this scene is reserved below.

---

## Scene 2 — Showcase Scene

### Scene Description

This is the current **showcase / visual scene** used for more artistic rendering.  
It contains multiple imported models and a more decorative composition than the pure benchmark scene.

Scene composition includes:

- pedestal
- sword
- arch
- urn / brazier
- crystals
- repeated decorative trees
- reflective and transparent materials

### Scene Data

- **scene name:** `build_showcase_scene_v3()`
- **scene type:** `mixed OBJ showcase`
- **total renderable objects:** `20875`
- **contains multiple imported models:** `Yes`

Loaded model data from the run:

- `pedestal.obj` — 532 vertices / 668 triangles
- `greatSword.obj` — 261 vertices / 518 triangles
- `arch.obj` — 1215 vertices / 2424 triangles
- `stone_pedestal.obj` — 173 vertices / 275 triangles
- `NeoUrn.obj` — 1696 vertices / 1931 triangles
- `Brazier.obj` — 676 vertices / 1237 triangles
- `Crystals.obj` — 312 vertices / 520 triangles
- `crystal_1.obj` — 496 vertices / 526 triangles
- `tree.obj` — 563 vertices / 850 triangles

### Render Settings

```python
times, average_time = benchmark_render_parallel_tiles(
    runs=11,
    width=2000,
    height=1300,
    objects=objects,
    background_color=background_color,
    light_position=light_position,
    depth=0,
    max_depth=3,
    num_workers=10,
    tile_size=24
)
```

### Results

All runs:

- Run 1: `14.769 s`
- Run 2: `14.298 s`
- Run 3: `14.576 s`
- Run 4: `16.660 s`
- Run 5: `16.025 s`
- Run 6: `15.070 s`
- Run 7: `14.824 s`
- Run 8: `14.394 s`
- Run 9: `14.586 s`
- Run 10: `14.316 s`
- Run 11: `14.599 s`

Summary:

- **average runtime over all runs:** `14.920 s`
- **best run:** `14.298 s`
- **worst run:** `16.660 s`

### Comparison with Earlier Version

Older result mentioned for this scene:

- **older timing:** `391.229 s`

This older number comes from a previous state of the renderer and is kept here only as a rough historical comparison reference.

### Render Preview

<img width="2000" height="1300" alt="render_2" src="https://github.com/user-attachments/assets/f1f878f3-2809-4103-9e84-63cba33e5daa" />


### Notes

- This scene is visually richer than the pure triangle benchmark and is better suited for presentation renders.
- Runtime is less stable than the `casa.obj` benchmark scene, which is expected for a more complex mixed showcase composition.
- This scene is useful both as a benchmark and as a visual demonstration of the renderer.

---

## Scene 3 — Mixed Recursive Benchmark Scene

### Scene Description

This scene is a **mixed recursive ray tracing benchmark** with:
- one imported OBJ sword
- many spheres
- many triangles
- plane surface
- reflections
- refractions

It is useful because it is not purely an OBJ-heavy triangle benchmark.  
Instead, it shows how the renderer behaves in a more classical Whitted-style recursive scene.

### Scene Data

- **scene name:** `build_realistic_benchmark_scene()`
- **OBJ file:** `Sword.obj`
- **OBJ vertices:** `94`
- **OBJ triangles:** `184`
- **total renderable objects:** `287`
- **scene composition:** `mixed primitives + triangles + recursion-heavy shading`

### Render Settings

```python
times, average_time = benchmark_render_parallel_tiles(
    runs=11,
    width=2000,
    height=1300,
    objects=objects,
    background_color=background_color,
    light_position=light_position,
    depth=0,
    max_depth=3,
    num_workers=10,
    tile_size=24
)
```

### Results

All runs:

- Run 1: `60.340 s`
- Run 2: `67.841 s`
- Run 3: `68.032 s`
- Run 4: `67.706 s`
- Run 5: `67.723 s`
- Run 6: `67.858 s`
- Run 7: `68.069 s`
- Run 8: `67.701 s`
- Run 9: `67.831 s`
- Run 10: `67.968 s`
- Run 11: `67.616 s`

Summary:

- **average runtime over all runs:** `67.153 s`
- **best run:** `60.340 s`
- **worst run:** `68.069 s`

### Comparison with Earlier Version

Older benchmark memory for this scene:

- **older average result:** about `9.7 s`
- **older settings:** `900 × 600`, `14` workers

This older value belongs to a different renderer state and significantly lower resolution.  
The current result is therefore not a direct one-to-one comparison, but it still shows that the current renderer is now much more specialized for triangle-heavy OBJ workloads than for this older mixed recursive benchmark.

### Render Preview

<img width="2000" height="1300" alt="render_3" src="https://github.com/user-attachments/assets/3808d010-8d3e-4af2-a1fa-0247145926ce" />


### Notes

- This scene remains useful because it stresses recursion, shadows, reflections, and refractions more strongly than the triangle-only benchmark.
- It is a good reminder that the current optimization stage is strongly oriented toward triangle-heavy scenes.
- It should be kept as a secondary benchmark, not the main current baseline.

---

## Reserved Block — Worker / Tile Sweep on `casa.obj`

This section is reserved for later parameter tuning on the main OBJ benchmark scene.

### Planned Sweep

The following combinations can be tested later:

- worker count sweep
- tile size sweep
- worker count × tile size grid

### Worker Sweep Table

| Workers | Tile Size | Average Time (s) | Notes |
|---------|-----------|------------------|-------|
| [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |

### Tile Size Sweep Table

| Tile Size | Workers | Average Time (s) | Notes |
|-----------|---------|------------------|-------|
| [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |

### Practical Best Configuration

- **scene:** `casa.obj`
- **best worker count:** [PLACEHOLDER]
- **best tile size:** [PLACEHOLDER]
- **best measured average:** [PLACEHOLDER]

---

## Current Practical Conclusion

The current optimized renderer performs best on the large triangle-heavy OBJ benchmark scene.

The current practical baseline is:

- **primary benchmark scene:** `casa.obj`
- **resolution:** `2000 × 1300`
- **max depth:** `3`
- **workers:** `10`
- **tile size:** `24`
- **average runtime:** `10.448 s`

Main observations:

- the optimized renderer now performs strongest on triangle-heavy OBJ workloads
- the showcase scene remains a useful visual benchmark and still renders in a practical time range
- the mixed recursive benchmark scene is much heavier and highlights that the current optimization stage is specialized toward triangle BVH workloads more than toward the older mixed-scene benchmark style

---

## Next Step

The current benchmark stage establishes the optimized BVH-based version as the new baseline.

Planned next steps:

- add richer object transformations
- add texture support
- add profiling / stage timing analysis
- continue performance analysis on large scenes
- perform explicit worker/tile sweeps on the main OBJ scene
- move toward path tracing
