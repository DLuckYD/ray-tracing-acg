import os
from PIL import Image

import config
from scenes import build_showcase_scene_v3
from parallel import benchmark_render_parallel_tiles
from triangle_logic.triangle_data import build_triangle_data
from triangle_logic.triangle_bvh import build_triangle_bvh


if __name__ == "__main__":
    print("Hello")

    available_cpus = os.cpu_count()
    print(f"Available logical CPU threads: {available_cpus}")

    objects, background_color, light_position = build_showcase_scene_v3()
    print(f"Current amount of objects: {len(objects)}")

    config.use_triangle_backend = True
    config.triangle_data = build_triangle_data(objects)
    config.triangle_bvh_root = build_triangle_bvh(config.triangle_data)


    config.use_aabb = False
    config.use_bvh = False
    config.bvh_root = None
    config.non_bvh_objects = []

    num_workers = 10

    times, average_time = benchmark_render_parallel_tiles(
        runs=1,
        width=2200,
        height=1300,
        objects=objects,
        background_color=background_color,
        light_position=light_position,
        depth=0,
        max_depth=3,
        num_workers=num_workers,
        tile_size=24
    )

    im = Image.open("render.png")
    im.show("Render")