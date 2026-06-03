from concurrent.futures import ProcessPoolExecutor, as_completed
from PIL import Image
import time

import logic_scripts.config
from logic_scripts.math3d import Vec3
from logic_scripts.ray import Ray
from logic_scripts.renderer import trace_ray

config = logic_scripts.config

def init_worker(
    objects,
    background_color,
    light_position,
    depth,
    max_depth,
    use_aabb,
    use_bvh,
    bvh_root,
    non_bvh_objects,
    use_triangle_backend,
    triangle_data,
    triangle_bvh_root,
    screen_x_values,
    screen_y_values
):
    config.scene_objects = objects
    config.scene_background_color = background_color
    config.scene_light_position = light_position
    config.scene_depth = depth
    config.scene_max_depth = max_depth

    config.use_aabb = use_aabb
    config.use_bvh = use_bvh
    config.bvh_root = bvh_root
    config.non_bvh_objects = non_bvh_objects
    config.blocker_cache_object = None

    config.use_triangle_backend = use_triangle_backend
    config.triangle_data = triangle_data
    config.triangle_bvh_root = triangle_bvh_root

    config.screen_x_values = screen_x_values
    config.screen_y_values = screen_y_values


def split_tiles(width, height, tile_size):
    chunks = []

    for y_start in range(0, height, tile_size):
        y_end = min(y_start + tile_size, height)

        for x_start in range(0, width, tile_size):
            x_end = min(x_start + tile_size, width)
            chunks.append((x_start, x_end, y_start, y_end))

    return chunks


def build_screen_coordinate_arrays(width, height):
    aspect_ratio = width / height
    viewport_height = 2.0
    viewport_width = viewport_height * aspect_ratio

    screen_x_values = []
    for x in range(width):
        u = (x + 0.5) / width
        screen_x = (u - 0.5) * viewport_width
        screen_x_values.append(screen_x)

    screen_y_values = []
    for y in range(height):
        v = (y + 0.5) / height
        screen_y = (0.5 - v) * viewport_height
        screen_y_values.append(screen_y)

    return screen_x_values, screen_y_values


def render_tile_chunk(args):
    x_start, x_end, y_start, y_end = args

    config.blocker_cache_object = None

    camera_origin = Vec3(0, 0, 0)
    image_plane_z = -1

    screen_x_values = config.screen_x_values
    screen_y_values = config.screen_y_values

    tile_width = x_end - x_start
    tile_height = y_end - y_start

    tile_buffer = bytearray(tile_width * tile_height * 3)
    write_index = 0

    for y in range(y_start, y_end):
        screen_y = screen_y_values[y]

        for x in range(x_start, x_end):
            screen_x = screen_x_values[x]

            pixel_pos = Vec3(screen_x, screen_y, image_plane_z)
            direction = (pixel_pos - camera_origin).normalize()

            ray = Ray(camera_origin, direction)

            color = trace_ray(
                ray,
                config.scene_objects,
                config.scene_background_color,
                config.scene_light_position,
                config.scene_depth,
                config.scene_max_depth
            )

            r = int(max(0, min(255, color.x * 255)))
            g = int(max(0, min(255, color.y * 255)))
            b = int(max(0, min(255, color.z * 255)))

            tile_buffer[write_index] = r
            tile_buffer[write_index + 1] = g
            tile_buffer[write_index + 2] = b
            write_index += 3

    return x_start, y_start, tile_width, tile_height, bytes(tile_buffer)


def render_parallel_tiles(width, height, objects, background_color, light_position, depth, max_depth, num_workers, tile_size=16):
    image = Image.new("RGB", (width, height))
    chunks = split_tiles(width, height, tile_size)

    screen_x_values, screen_y_values = build_screen_coordinate_arrays(width, height)

    task_args = []
    for x_start, x_end, y_start, y_end in chunks:
        task_args.append((x_start, x_end, y_start, y_end))

    print(f"Using {num_workers} worker processes")
    print(f"Image divided into {len(chunks)} tiles of size {tile_size}")

    completed_chunks = 0

    with ProcessPoolExecutor(
        max_workers=num_workers,
        initializer=init_worker,
        initargs=(
                objects,
                background_color,
                light_position,
                depth,
                max_depth,
                config.use_aabb,
                config.use_bvh,
                config.bvh_root,
                config.non_bvh_objects,
                config.use_triangle_backend,
                config.triangle_data,
                config.triangle_bvh_root,
                screen_x_values,
                screen_y_values
        )
    ) as executor:
        futures = [executor.submit(render_tile_chunk, args) for args in task_args]

        for future in as_completed(futures):
            x_start, y_start, tile_width, tile_height, tile_bytes = future.result()

            tile_image = Image.frombytes("RGB", (tile_width, tile_height), tile_bytes)
            image.paste(tile_image, (x_start, y_start))

            completed_chunks += 1
            print(f"\rCompleted tiles: {completed_chunks} / {len(chunks)}", end="", flush=True)

    print()
    image.save("render.png")
    print("Parallel tile render finished: render.png")

    return image


def benchmark_render_parallel_tiles(runs, width, height, objects, background_color, light_position, depth, max_depth, num_workers, tile_size=16):
    times = []

    for i in range(runs):
        print(f"\nStarting parallel tile run {i + 1} / {runs}")

        start_time = time.perf_counter()
        render_parallel_tiles(
            width,
            height,
            objects,
            background_color,
            light_position,
            depth,
            max_depth,
            num_workers,
            tile_size
        )
        end_time = time.perf_counter()

        elapsed = end_time - start_time
        times.append(elapsed)

        print(f"Parallel tile run {i + 1} time: {elapsed:.3f} seconds")

    average_time = sum(times) / len(times)

    print("\nParallel tile benchmark finished.")
    print("All runs:")
    for i, t in enumerate(times, start=1):
        print(f"  Run {i}: {t:.3f} seconds")

    print(f"\nAverage parallel tile render time over {runs} runs: {average_time:.3f} seconds")

    return times, average_time