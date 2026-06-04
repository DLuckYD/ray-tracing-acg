# config.py

use_aabb = True
use_bvh = True
bvh_root = None
non_bvh_objects = []
blocker_cache_object = None

# worker-local render state
scene_objects = None
scene_background_color = None
scene_light_position = None
scene_depth = 0
scene_max_depth = 0

# triangle backend
use_triangle_backend = False
triangle_data = None
triangle_bvh_root = None

# backend mode
# possible values:
# "numba" -> current Python + Numba pipeline
# "cpp"   -> future C++ traversal pipeline
backend_mode = "cpp"