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

    denoise_mode = getattr(config, "denoise_mode", "bilateral")
    denoise_passes = int(getattr(config, "denoise_passes", 1))

    # ------------------------------------------------------------
    # 1. Median
    # ------------------------------------------------------------
    if denoise_mode == "median":
        from PIL import ImageFilter

        result = image.copy()

        kernel = int(getattr(config, "denoise_kernel", 3))
        if kernel % 2 == 0:
            kernel += 1

        kernel = max(3, min(kernel, 7))

        for _ in range(max(1, denoise_passes)):
            result = result.filter(
                ImageFilter.MedianFilter(size=kernel)
            )

        return result

    # ------------------------------------------------------------
    # 2. Gaussian
    # ------------------------------------------------------------
    if denoise_mode == "gaussian":
        from PIL import ImageFilter

        result = image.copy()

        radius = float(
            getattr(config, "denoise_radius", 0.5)
        )

        for _ in range(max(1, denoise_passes)):
            result = result.filter(
                ImageFilter.GaussianBlur(radius=radius)
            )

        return result

    # ------------------------------------------------------------
    # 3. Bilateral
    #
    # Good general-purpose denoiser for path tracing:
    # smooths noise while preserving edges.
    # ------------------------------------------------------------
    if denoise_mode == "bilateral":
        import cv2

        src = np.asarray(image, dtype=np.uint8)

        # PIL = RGB
        # OpenCV usually works in BGR
        result = cv2.cvtColor(src, cv2.COLOR_RGB2BGR)

        diameter = int(
            getattr(config, "denoise_diameter", 5)
        )

        sigma_color = float(
            getattr(config, "denoise_sigma_color", 35.0)
        )

        sigma_space = float(
            getattr(config, "denoise_sigma_space", 5.0)
        )

        diameter = max(3, diameter)

        if diameter % 2 == 0:
            diameter += 1

        for _ in range(max(1, denoise_passes)):
            result = cv2.bilateralFilter(
                result,
                d=diameter,
                sigmaColor=sigma_color,
                sigmaSpace=sigma_space
            )

        result = cv2.cvtColor(
            result,
            cv2.COLOR_BGR2RGB
        )

        return Image.fromarray(result)

    # ------------------------------------------------------------
    # 4. Adaptive outlier removal
    #
    # Detects pixels strongly differing from their neighbourhood
    # and replaces only those pixels with the local median.
    #
    # Good for isolated bright/dark Monte Carlo fireflies.
    # ------------------------------------------------------------
    if denoise_mode == "adaptive":
        import cv2

        src = np.asarray(
            image,
            dtype=np.float32
        )

        kernel = int(
            getattr(config, "denoise_kernel", 3)
        )

        if kernel % 2 == 0:
            kernel += 1

        kernel = max(3, min(kernel, 7))

        threshold = float(
            getattr(config, "denoise_threshold", 35.0)
        )

        result = src.copy()

        for _ in range(max(1, denoise_passes)):

            # Median reference image
            median = cv2.medianBlur(
                np.clip(result, 0, 255).astype(np.uint8),
                kernel
            ).astype(np.float32)

            # Difference from local median
            diff = np.linalg.norm(
                result - median,
                axis=2
            )

            # Only replace obvious outliers
            mask = diff > threshold

            result[mask] = median[mask]

        return Image.fromarray(
            np.clip(result, 0, 255).astype(np.uint8)
        )

    # ------------------------------------------------------------
    # 5. Hybrid
    #
    # Recommended mode:
    #
    # adaptive outlier removal
    # +
    # bilateral smoothing
    #
    # Removes fireflies first, then smooths remaining Monte Carlo
    # noise while preserving edges.
    # ------------------------------------------------------------
    if denoise_mode == "hybrid":
        import cv2

        src = np.asarray(
            image,
            dtype=np.float32
        )

        kernel = int(
            getattr(config, "denoise_kernel", 3)
        )

        if kernel % 2 == 0:
            kernel += 1

        kernel = max(3, min(kernel, 7))

        threshold = float(
            getattr(config, "denoise_threshold", 30.0)
        )

        diameter = int(
            getattr(config, "denoise_diameter", 5)
        )

        if diameter % 2 == 0:
            diameter += 1

        sigma_color = float(
            getattr(config, "denoise_sigma_color", 30.0)
        )

        sigma_space = float(
            getattr(config, "denoise_sigma_space", 5.0)
        )

        result = src.copy()

        for _ in range(max(1, denoise_passes)):

            # ----------------------------------------
            # Step 1:
            # remove isolated noisy outliers/fireflies
            # ----------------------------------------
            median = cv2.medianBlur(
                np.clip(result, 0, 255).astype(np.uint8),
                kernel
            ).astype(np.float32)

            diff = np.linalg.norm(
                result - median,
                axis=2
            )

            mask = diff > threshold

            result[mask] = median[mask]

            # ----------------------------------------
            # Step 2:
            # edge-preserving smoothing
            # ----------------------------------------
            tmp = np.clip(
                result,
                0,
                255
            ).astype(np.uint8)

            tmp = cv2.bilateralFilter(
                tmp,
                d=diameter,
                sigmaColor=sigma_color,
                sigmaSpace=sigma_space
            )

            result = tmp.astype(np.float32)

        return Image.fromarray(
            np.clip(result, 0, 255).astype(np.uint8)
        )

    print(
        f"Unknown denoise mode '{denoise_mode}'. "
        f"Returning original image."
    )

    return image


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


def build_texture_payload(triangle_data):
    texture_paths = triangle_data.get("texture_path")
    has_texture = triangle_data.get("has_texture")

    if texture_paths is None or has_texture is None or len(texture_paths) == 0:
        return {
            "texture_ids_per_triangle": np.empty(0, dtype=np.int32),
            "texture_widths": np.empty(0, dtype=np.int32),
            "texture_heights": np.empty(0, dtype=np.int32),
            "texture_offsets": np.empty(0, dtype=np.int32),
            "texture_pixels": np.empty(0, dtype=np.uint8),
            "texture_count": 0,
        }

    triangle_count = len(texture_paths)
    texture_ids_per_triangle = np.full(triangle_count, -1, dtype=np.int32)

    unique_texture_to_id = {}
    texture_widths = []
    texture_heights = []
    texture_offsets = []
    texture_bytes = bytearray()

    for tri_index in range(triangle_count):
        if int(has_texture[tri_index]) == 0:
            continue

        path = texture_paths[tri_index]
        if not path:
            continue

        if path not in unique_texture_to_id:
            image = Image.open(path).convert("RGB")
            image_np = np.asarray(image, dtype=np.uint8)

            tex_id = len(texture_widths)
            unique_texture_to_id[path] = tex_id

            texture_widths.append(int(image.width))
            texture_heights.append(int(image.height))
            texture_offsets.append(len(texture_bytes))

            texture_bytes.extend(image_np.tobytes())

        texture_ids_per_triangle[tri_index] = unique_texture_to_id[path]

    if len(texture_widths) == 0:
        return {
            "texture_ids_per_triangle": texture_ids_per_triangle,
            "texture_widths": np.empty(0, dtype=np.int32),
            "texture_heights": np.empty(0, dtype=np.int32),
            "texture_offsets": np.empty(0, dtype=np.int32),
            "texture_pixels": np.empty(0, dtype=np.uint8),
            "texture_count": 0,
        }

    return {
        "texture_ids_per_triangle": texture_ids_per_triangle,
        "texture_widths": np.asarray(texture_widths, dtype=np.int32),
        "texture_heights": np.asarray(texture_heights, dtype=np.int32),
        "texture_offsets": np.asarray(texture_offsets, dtype=np.int32),
        "texture_pixels": np.frombuffer(bytes(texture_bytes), dtype=np.uint8),
        "texture_count": len(texture_widths),
    }


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

        t_tex = time.perf_counter()
        texture_payload = getattr(config, "texture_payload", None)
        if texture_payload is None:
            texture_payload = build_texture_payload(triangle_data)
            config.texture_payload = texture_payload
        stage_timings["build_texture_payload"] = time.perf_counter() - t_tex

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

                triangle_data["uv0_u"],
                triangle_data["uv0_v"],
                triangle_data["uv1_u"],
                triangle_data["uv1_v"],
                triangle_data["uv2_u"],
                triangle_data["uv2_v"],
                triangle_data["has_uv"],

                texture_payload["texture_ids_per_triangle"],
                texture_payload["texture_widths"],
                texture_payload["texture_heights"],
                texture_payload["texture_offsets"],
                texture_payload["texture_pixels"],

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

                triangle_data["uv0_u"],
                triangle_data["uv0_v"],
                triangle_data["uv1_u"],
                triangle_data["uv1_v"],
                triangle_data["uv2_u"],
                triangle_data["uv2_v"],
                triangle_data["has_uv"],

                texture_payload["texture_ids_per_triangle"],
                texture_payload["texture_widths"],
                texture_payload["texture_heights"],
                texture_payload["texture_offsets"],
                texture_payload["texture_pixels"],

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