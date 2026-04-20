# Ray Tracing in Python

<!-- PLACEHOLDER: Insert render image here -->
<!-- Example: ![Render](path/to/render.png) -->

## Overview

Educational ray tracer written from scratch in Python to understand the basic logic of Whitted-style ray tracing.

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
- PNG output with Pillow

## Scene

The current scene supports spheres, a plane as a floor, one point light source, and a background color.

## How it works

For each pixel, the renderer creates a ray from the camera through the image plane, finds the nearest object hit, computes local lighting, traces reflected rays recursively, and writes the final color to the image.

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

## Current limitations

- no refraction yet
- one light source
- no acceleration structures

## Render
<img width="100%" height="100%" alt="render2" src="https://github.com/user-attachments/assets/5ee7af5f-2efb-4bf8-a44c-7ee380c446ea" />

