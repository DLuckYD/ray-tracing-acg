import os
import time
from PIL import Image

import logic_scripts.config
from logic_scripts.scenes import build_showcase_scene_v3, build_obj_test_scene, build_realistic_benchmark_scene
from logic_scripts.parallel import benchmark_render_parallel_tiles
from logic_scripts.benchmark_logger import reset_logs_dir, write_run_log, write_summary_log
from triangle_logic.triangle_data import build_triangle_data
from triangle_logic.triangle_bvh import build_triangle_bvh

config = logic_scripts.config


if __name__ == "__main__":
    print("Hello")

    available_cpus = os.cpu_count()
    print(f"Available logical CPU threads: {available_cpus}")

    scene_name = "build_obj_test_scene"
    config.backend_mode = "cpp"

    t_scene = time.perf_counter()
    objects, background_color, light_position = build_obj_test_scene()
    scene_build_time = time.perf_counter() - t_scene

    print(f"Current amount of objects: {len(objects)}")

    config.use_triangle_backend = True

    t_triangle_data = time.perf_counter()
    config.triangle_data = build_triangle_data(objects)
    triangle_data_build_time = time.perf_counter() - t_triangle_data

    t_bvh = time.perf_counter()
    config.triangle_bvh_root = build_triangle_bvh(config.triangle_data)
    triangle_bvh_build_time = time.perf_counter() - t_bvh

    config.use_aabb = False
    config.use_bvh = True
    config.bvh_root = None
    config.non_bvh_objects = []
####################################################################################
    num_workers = 10
    runs = 11
    width = 1920
    height = 1080
    max_depth = 0
    tile_size = 128
####################################################################################
    build_stage_timings = {
        "scene_build": scene_build_time,
        "triangle_data_build": triangle_data_build_time,
        "triangle_bvh_build": triangle_bvh_build_time,
    }

    reset_logs_dir()

    times, average_time, per_run_stage_timings = benchmark_render_parallel_tiles(
        runs=runs,
        width=width,
        height=height,
        objects=objects,
        background_color=background_color,
        light_position=light_position,
        depth=0,
        max_depth=max_depth,
        num_workers=num_workers,
        tile_size=tile_size
    )

    average_without_first = None
    if len(times) > 1:
        average_without_first = sum(times[1:]) / len(times[1:])

    best_time = min(times)
    worst_time = max(times)

    for run_index, (run_time, stage_timings) in enumerate(zip(times, per_run_stage_timings), start=1):
        merged_stage_timings = {}
        merged_stage_timings.update(build_stage_timings)
        merged_stage_timings.update(stage_timings)

        write_run_log(
            run_index=run_index,
            backend_mode=config.backend_mode,
            scene_name=scene_name,
            width=width,
            height=height,
            max_depth=max_depth,
            workers=num_workers,
            tile_size=tile_size,
            total_time=run_time,
            stage_timings=merged_stage_timings
        )

    write_summary_log(
        backend_mode=config.backend_mode,
        scene_name=scene_name,
        width=width,
        height=height,
        max_depth=max_depth,
        workers=num_workers,
        tile_size=tile_size,
        all_run_times=times,
        average_time=average_time,
        average_without_first=average_without_first,
        best_time=best_time,
        worst_time=worst_time,
        build_stage_timings=build_stage_timings
    )

    im = Image.open("render.png")
    im.show("Render")