import os
from PIL import Image

import config
from scenes import build_realistic_benchmark_scene, build_aabb_benchmark_scene
from bvh import build_bvh, split_bvh_objects
from parallel import benchmark_render_parallel_tiles
# если parallel пока не вынес:
# from renderer import benchmark_render_parallel

if __name__ == "__main__":
    print("Hello")

    available_cpus = os.cpu_count()
    print(f"Available logical CPU threads: {available_cpus}")

    objects, background_color, light_position = build_realistic_benchmark_scene()
    print(f"Current amount of objects: {len(objects)}")

    config.use_aabb = False
    config.use_bvh = True

    bvh_objects, config.non_bvh_objects = split_bvh_objects(objects)

    if config.use_bvh:
        config.bvh_root = build_bvh(bvh_objects)
    else:
        config.bvh_root = None

    num_workers = 8

    times, average_time = benchmark_render_parallel_tiles(
        runs=10,
        width=900,
        height=600,
        objects=objects,
        background_color=background_color,
        light_position=light_position,
        depth=0,
        max_depth=3,
        num_workers=num_workers,
        tile_size=16
    )

    im = Image.open("render.png")
    im.show("Render")