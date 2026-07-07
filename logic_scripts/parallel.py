from PIL import Image
import time
import numpy as np

import logic_scripts.config
from logic_scripts.math3d import Vec3
from logic_scripts.ray import Ray
from logic_scripts.renderer import trace_ray

config = logic_scripts.config

try:
    import rt_core
    CPP_BACKEND_AVAILABLE = True
except ImportError:
    rt_core = None
    CPP_BACKEND_AVAILABLE = False



def apply_optional_denoise(image):
    if not getattr(config, "enable_denoise", False):
        return image

    denoise_mode = getattr(config, "denoise_mode", "median")
    denoise_passes = int(getattr(config, "denoise_passes", 1))

    result = image.copy()

    if denoise_mode == "median":
        from PIL import ImageFilter
        for _ in range(max(1, denoise_passes)):
            result = result.filter(ImageFilter.MedianFilter(size=3))
        return result

    if denoise_mode == "gaussian":
        from PIL import ImageFilter
        radius = float(getattr(config, "denoise_radius", 1.0))
        return result.filter(ImageFilter.GaussianBlur(radius=radius))

    return result


def build_screen_coordinate_arrays(width, height):
    aspect_ratio = width / height
    viewport_height = 2.0
    viewport_width = viewport_height * aspect_ratio

    screen_x_values = np.empty(width, dtype=np.float64)
    for x in range(width):
        u = (x + 0.5) / width
        screen_x_values[x] = (u - 0.5) * viewport_width

    screen_y_values = np.empty(height, dtype=np.float64)
    for y in range(height):
        v = (y + 0.5) / height
        screen_y_values[y] = (0.5 - v) * viewport_height

    return screen_x_values, screen_y_values


def render_full_image_python(width, height, objects, background_color, light_position, depth, max_depth):
    image = Image.new("RGB", (width, height))
    camera_origin = Vec3(0, 0, 0)
    image_plane_z = -1

    screen_x_values, screen_y_values = build_screen_coordinate_arrays(width, height)

    tile_buffer = bytearray(width * height * 3)
    write_index = 0

    for y in range(height):
        screen_y = screen_y_values[y]

        for x in range(width):
            screen_x = screen_x_values[x]

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

            tile_buffer[write_index] = r
            tile_buffer[write_index + 1] = g
            tile_buffer[write_index + 2] = b
            write_index += 3

    image = Image.frombytes("RGB", (width, height), bytes(tile_buffer))
    image.save("render.png")
    return image


def render_parallel_tiles(width, height, objects, background_color, light_position, depth, max_depth, num_workers, tile_size=16):
    stage_timings = {}

    render_mode = getattr(config, "render_mode", "raytrace")
    samples_per_pixel = getattr(config, "samples_per_pixel", 1)
    max_bounces = getattr(config, "max_bounces", 2)
    use_russian_roulette = 1 if getattr(config, "use_russian_roulette", False) else 0
    rr_start_depth = getattr(config, "rr_start_depth", 2)

    t0 = time.perf_counter()
    screen_x_values, screen_y_values = build_screen_coordinate_arrays(width, height)
    stage_timings["build_screen_coordinate_arrays"] = time.perf_counter() - t0

    if config.backend_mode == "cpp" and config.use_triangle_backend and CPP_BACKEND_AVAILABLE:
        triangle_data = config.triangle_data
        triangle_bvh = config.triangle_bvh_root

        if render_mode == "pathtrace":
            t1 = time.perf_counter()

            image_bytes = rt_core.render_triangle_path_traced_image_cpp(
                width,
                height,
                samples_per_pixel,
                max_bounces,
                num_workers,
                use_russian_roulette,
                rr_start_depth,

                light_position.x,
                light_position.y,
                light_position.z,

                background_color.x,
                background_color.y,
                background_color.z,

                int(triangle_bvh["root_index"]),
                triangle_bvh["triangle_indices"],

                triangle_bvh["node_aabb_min_x"],
                triangle_bvh["node_aabb_min_y"],
                triangle_bvh["node_aabb_min_z"],
                triangle_bvh["node_aabb_max_x"],
                triangle_bvh["node_aabb_max_y"],
                triangle_bvh["node_aabb_max_z"],

                triangle_bvh["node_left"],
                triangle_bvh["node_right"],
                triangle_bvh["node_start"],
                triangle_bvh["node_count"],
                triangle_bvh["node_is_leaf"],

                triangle_data["v0x"], triangle_data["v0y"], triangle_data["v0z"],
                triangle_data["v1x"], triangle_data["v1y"], triangle_data["v1z"],
                triangle_data["v2x"], triangle_data["v2y"], triangle_data["v2z"],

                triangle_data["normal_x"],
                triangle_data["normal_y"],
                triangle_data["normal_z"],

                triangle_data["color_r"],
                triangle_data["color_g"],
                triangle_data["color_b"],

                triangle_data["reflection"],
                triangle_data["transparency"],
                triangle_data["ior"],

                screen_x_values,
                screen_y_values,
            )

            stage_timings["cpp_path_traced_full_image_render"] = time.perf_counter() - t1

        else:
            t1 = time.perf_counter()

            image_bytes = rt_core.render_triangle_image_cpp(
                width,
                height,
                max_depth,
                num_workers,

                light_position.x,
                light_position.y,
                light_position.z,

                background_color.x,
                background_color.y,
                background_color.z,

                int(triangle_bvh["root_index"]),
                triangle_bvh["triangle_indices"],

                triangle_bvh["node_aabb_min_x"],
                triangle_bvh["node_aabb_min_y"],
                triangle_bvh["node_aabb_min_z"],
                triangle_bvh["node_aabb_max_x"],
                triangle_bvh["node_aabb_max_y"],
                triangle_bvh["node_aabb_max_z"],

                triangle_bvh["node_left"],
                triangle_bvh["node_right"],
                triangle_bvh["node_start"],
                triangle_bvh["node_count"],
                triangle_bvh["node_is_leaf"],

                triangle_data["v0x"], triangle_data["v0y"], triangle_data["v0z"],
                triangle_data["v1x"], triangle_data["v1y"], triangle_data["v1z"],
                triangle_data["v2x"], triangle_data["v2y"], triangle_data["v2z"],

                triangle_data["normal_x"],
                triangle_data["normal_y"],
                triangle_data["normal_z"],

                triangle_data["color_r"],
                triangle_data["color_g"],
                triangle_data["color_b"],

                triangle_data["reflection"],
                triangle_data["transparency"],
                triangle_data["ior"],

                screen_x_values,
                screen_y_values,
            )

            stage_timings["cpp_full_image_render"] = time.perf_counter() - t1

        t2 = time.perf_counter()
        image = Image.frombytes("RGB", (width, height), image_bytes)
        stage_timings["image_from_bytes"] = time.perf_counter() - t2

        if getattr(config, "enable_denoise", False):
            t_denoise = time.perf_counter()
            image.save("render_raw.png")
            image = apply_optional_denoise(image)
            stage_timings["image_denoise"] = time.perf_counter() - t_denoise

        t3 = time.perf_counter()
        image.save("render.png")
        stage_timings["image_save"] = time.perf_counter() - t3

        stage_timings["render_parallel_tiles_total"] = sum(stage_timings.values())

        if render_mode == "pathtrace":
            print("Full C++ path traced image render finished: render.png")
        else:
            print("Full C++ ray traced image render finished: render.png")

        return image, stage_timings

    # fallback path
    t1 = time.perf_counter()
    image = render_full_image_python(
        width,
        height,
        objects,
        background_color,
        light_position,
        depth,
        max_depth
    )
    stage_timings["python_full_image_render"] = time.perf_counter() - t1

    stage_timings["render_parallel_tiles_total"] = (
        stage_timings["build_screen_coordinate_arrays"]
        + stage_timings["python_full_image_render"]
    )

    print("Python full image render finished: render.png")
    return image, stage_timings


def benchmark_render_parallel_tiles(runs, width, height, objects, background_color, light_position, depth, max_depth, num_workers, tile_size=16):
    times = []
    per_run_stage_timings = []

    for i in range(runs):
        print(f"\nStarting parallel tile run {i + 1} / {runs}")

        start_time = time.perf_counter()
        _, stage_timings = render_parallel_tiles(
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

        stage_timings["benchmark_run_total"] = elapsed
        per_run_stage_timings.append(stage_timings)

        print(f"Parallel tile run {i + 1} time: {elapsed:.3f} seconds")

    average_time = sum(times) / len(times)

    print("\nParallel tile benchmark finished.")
    print("All runs:")
    for i, t in enumerate(times, start=1):
        print(f"  Run {i}: {t:.3f} seconds")

    print(f"\nAverage parallel tile render time over {runs} runs: {average_time:.3f} seconds")

    return times, average_time, per_run_stage_timings