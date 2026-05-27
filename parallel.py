from concurrent.futures import ProcessPoolExecutor, as_completed
from PIL import Image

import config
import time
from math3d import Vec3
from ray import Ray
from renderer import trace_ray


def split_rows(height, num_workers):
    chunks = []
    rows_per_worker = height // num_workers
    remainder = height % num_workers

    y_start = 0

    for i in range(num_workers):
        extra = 1 if i < remainder else 0
        y_end = y_start + rows_per_worker + extra
        chunks.append((y_start, y_end))
        y_start = y_end

    return chunks

def split_rows_fixed_chunk_size(height, chunk_height):
    chunks = []
    y_start = 0

    while y_start < height:
        y_end = min(y_start + chunk_height, height)
        chunks.append((y_start, y_end))
        y_start = y_end

    return chunks

def render_chunk(args):

    (
        y_start,
        y_end,
        width,
        height,
        objects,
        background_color,
        light_position,
        depth,
        max_depth,
        chunk_use_aabb,
        chunk_use_bvh,
        chunk_bvh_root,
        chunk_non_bvh_objects
    ) = args

    config.use_aabb = chunk_use_aabb
    config.use_bvh = chunk_use_bvh
    config.bvh_root = chunk_bvh_root
    config.non_bvh_objects = chunk_non_bvh_objects
    config.blocker_cache_object = None

    camera_origin = Vec3(0, 0, 0)
    image_plane_z = -1
    aspect_ratio = width / height
    viewport_height = 2.0
    viewport_width = viewport_height * aspect_ratio

    rows_data = []

    for y in range(y_start, y_end):
        row_pixels = []

        for x in range(width):
            u = (x + 0.5) / width
            v = (y + 0.5) / height

            screen_x = (u - 0.5) * viewport_width
            screen_y = (0.5 - v) * viewport_height

            pixel_pos = Vec3(screen_x, screen_y, image_plane_z)
            direction = (pixel_pos - camera_origin).normalize()

            ray = Ray(camera_origin, direction)
            color = trace_ray(
                ray,
                objects,
                background_color,
                light_position,
                depth,
                max_depth
            )

            r = int(max(0, min(255, color.x * 255)))
            g = int(max(0, min(255, color.y * 255)))
            b = int(max(0, min(255, color.z * 255)))

            row_pixels.append((r, g, b))

        rows_data.append((y, row_pixels))

    return rows_data




def render_parallel(width, height, objects, background_color, light_position, depth, max_depth, num_workers):
    image = Image.new("RGB", (width, height))

    # chunks = split_rows(height, num_workers)
    chunks = split_rows_fixed_chunk_size(height, 5)

    task_args = []
    for y_start, y_end in chunks:
        task_args.append((
            y_start,
            y_end,
            width,
            height,
            objects,
            background_color,
            light_position,
            depth,
            max_depth,
            config.use_aabb,
            config.use_bvh,
            config.bvh_root,
            config.non_bvh_objects
        ))

    print(f"Using {num_workers} worker processes")
    print(f"Image divided into {len(chunks)} chunks")

    completed_chunks = 0

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(render_chunk, args) for args in task_args]

        for future in as_completed(futures):
            rows_data = future.result()

            for y, row_pixels in rows_data:
                if y < 0 or y >= height:
                    print(f"BAD Y INDEX: y={y}, height={height}")
                    continue

                if len(row_pixels) != width:
                    print(f"BAD ROW LENGTH: len(row_pixels)={len(row_pixels)}, width={width}")

                for x, pixel in enumerate(row_pixels):
                    if x < 0 or x >= width:
                        print(f"BAD X INDEX: x={x}, width={width}, y={y}")
                        continue

                    image.putpixel((x, y), pixel)

            completed_chunks += 1
            print(f"\rCompleted chunks: {completed_chunks} / {len(chunks)}", end="", flush=True)

    print()
    image.save("render.png")
    print("Parallel render finished: render.png")

    return image

def benchmark_render_parallel(runs, width, height, objects, background_color, light_position, depth, max_depth, num_workers):
    times = []

    for i in range(runs):
        print(f"\nStarting parallel run {i + 1} / {runs}")

        start_time = time.perf_counter()
        render_parallel(
            width,
            height,
            objects,
            background_color,
            light_position,
            depth,
            max_depth,
            num_workers
        )
        end_time = time.perf_counter()

        elapsed = end_time - start_time
        times.append(elapsed)

        print(f"Parallel run {i + 1} time: {elapsed:.3f} seconds")

    average_time = sum(times) / len(times)

    print("\nParallel benchmark finished.")
    print("All runs:")
    for i, t in enumerate(times, start=1):
        print(f"  Run {i}: {t:.3f} seconds")

    print(f"\nAverage parallel render time over {runs} runs: {average_time:.3f} seconds")

    return times, average_time