import logic_scripts.config
from logic_scripts.aabb import AABB, compute_objects_aabb, get_largest_axis, get_aabb_center
from logic_scripts.math3d import Vec3

config = logic_scripts.config


LEAF_SIZE = 8
NUM_BINS = 12


class BVHNode:
    def __init__(self, aabb, left=None, right=None, objects=None, is_leaf=False):
        self.aabb = aabb
        self.left = left
        self.right = right
        self.objects = objects if objects is not None else []
        self.is_leaf = is_leaf


def surface_area(aabb):
    sx = aabb.max_point.x - aabb.min_point.x
    sy = aabb.max_point.y - aabb.min_point.y
    sz = aabb.max_point.z - aabb.min_point.z
    return 2.0 * (sx * sy + sx * sz + sy * sz)


def get_axis_value(vec, axis):
    if axis == 0:
        return vec.x
    elif axis == 1:
        return vec.y
    return vec.z


def compute_centroid_bounds(objects):
    first_center = get_aabb_center(objects[0])

    min_x = first_center.x
    min_y = first_center.y
    min_z = first_center.z

    max_x = first_center.x
    max_y = first_center.y
    max_z = first_center.z

    for obj in objects[1:]:
        c = get_aabb_center(obj)

        min_x = min(min_x, c.x)
        min_y = min(min_y, c.y)
        min_z = min(min_z, c.z)

        max_x = max(max_x, c.x)
        max_y = max(max_y, c.y)
        max_z = max(max_z, c.z)

    return (min_x, min_y, min_z), (max_x, max_y, max_z)


def merge_two_aabbs(aabb1, aabb2):
    min_x = min(aabb1.min_point.x, aabb2.min_point.x)
    min_y = min(aabb1.min_point.y, aabb2.min_point.y)
    min_z = min(aabb1.min_point.z, aabb2.min_point.z)

    max_x = max(aabb1.max_point.x, aabb2.max_point.x)
    max_y = max(aabb1.max_point.y, aabb2.max_point.y)
    max_z = max(aabb1.max_point.z, aabb2.max_point.z)

    return AABB(Vec3(min_x, min_y, min_z), Vec3(max_x, max_y, max_z))


def compute_sah_split(objects, axis, num_bins=NUM_BINS):
    if len(objects) <= LEAF_SIZE:
        return None

    centroid_min, centroid_max = compute_centroid_bounds(objects)
    min_axis = centroid_min[axis]
    max_axis = centroid_max[axis]
    extent = max_axis - min_axis

    if extent <= 1e-9:
        return None

    bins = [{"count": 0, "aabb": None} for _ in range(num_bins)]

    for obj in objects:
        center = get_aabb_center(obj)
        center_value = get_axis_value(center, axis)

        normalized = (center_value - min_axis) / extent
        bin_index = int(normalized * num_bins)
        if bin_index == num_bins:
            bin_index = num_bins - 1

        bins[bin_index]["count"] += 1

        obj_aabb = obj.get_aabb()
        if bins[bin_index]["aabb"] is None:
            bins[bin_index]["aabb"] = obj_aabb
        else:
            bins[bin_index]["aabb"] = merge_two_aabbs(bins[bin_index]["aabb"], obj_aabb)

    left_count = [0] * num_bins
    left_aabb = [None] * num_bins

    running_count = 0
    running_aabb = None
    for i in range(num_bins):
        running_count += bins[i]["count"]
        left_count[i] = running_count

        if bins[i]["aabb"] is not None:
            if running_aabb is None:
                running_aabb = bins[i]["aabb"]
            else:
                running_aabb = merge_two_aabbs(running_aabb, bins[i]["aabb"])

        left_aabb[i] = running_aabb

    right_count = [0] * num_bins
    right_aabb = [None] * num_bins

    running_count = 0
    running_aabb = None
    for i in range(num_bins - 1, -1, -1):
        running_count += bins[i]["count"]
        right_count[i] = running_count

        if bins[i]["aabb"] is not None:
            if running_aabb is None:
                running_aabb = bins[i]["aabb"]
            else:
                running_aabb = merge_two_aabbs(running_aabb, bins[i]["aabb"])

        right_aabb[i] = running_aabb

    best_cost = None
    best_split_bin = None

    for i in range(num_bins - 1):
        count_left = left_count[i]
        count_right = right_count[i + 1]
        aabb_left = left_aabb[i]
        aabb_right = right_aabb[i + 1]

        if count_left == 0 or count_right == 0:
            continue
        if aabb_left is None or aabb_right is None:
            continue

        cost = surface_area(aabb_left) * count_left + surface_area(aabb_right) * count_right

        if best_cost is None or cost < best_cost:
            best_cost = cost
            best_split_bin = i

    if best_split_bin is None:
        return None

    split_position = min_axis + extent * ((best_split_bin + 1) / num_bins)
    return split_position


def partition_objects_by_split(objects, axis, split_position):
    left_objects = []
    right_objects = []

    for obj in objects:
        center = get_aabb_center(obj)
        center_value = get_axis_value(center, axis)

        if center_value < split_position:
            left_objects.append(obj)
        else:
            right_objects.append(obj)

    return left_objects, right_objects


def build_bvh_tree(objects, leaf_size=LEAF_SIZE, num_bins=NUM_BINS):
    valid_objects = [obj for obj in objects if obj.get_aabb() is not None]

    if len(valid_objects) == 0:
        return None

    node_aabb = compute_objects_aabb(valid_objects)

    if len(valid_objects) <= leaf_size:
        return BVHNode(
            aabb=node_aabb,
            left=None,
            right=None,
            objects=valid_objects,
            is_leaf=True
        )

    axis = get_largest_axis(node_aabb)
    split_position = compute_sah_split(valid_objects, axis, num_bins)

    if split_position is None:
        if axis == 0:
            valid_objects.sort(key=lambda obj: get_aabb_center(obj).x)
        elif axis == 1:
            valid_objects.sort(key=lambda obj: get_aabb_center(obj).y)
        else:
            valid_objects.sort(key=lambda obj: get_aabb_center(obj).z)

        mid = len(valid_objects) // 2
        left_objects = valid_objects[:mid]
        right_objects = valid_objects[mid:]
    else:
        left_objects, right_objects = partition_objects_by_split(valid_objects, axis, split_position)

        if len(left_objects) == 0 or len(right_objects) == 0:
            if axis == 0:
                valid_objects.sort(key=lambda obj: get_aabb_center(obj).x)
            elif axis == 1:
                valid_objects.sort(key=lambda obj: get_aabb_center(obj).y)
            else:
                valid_objects.sort(key=lambda obj: get_aabb_center(obj).z)

            mid = len(valid_objects) // 2
            left_objects = valid_objects[:mid]
            right_objects = valid_objects[mid:]

    left_node = build_bvh_tree(left_objects, leaf_size, num_bins)
    right_node = build_bvh_tree(right_objects, leaf_size, num_bins)

    return BVHNode(
        aabb=node_aabb,
        left=left_node,
        right=right_node,
        objects=None,
        is_leaf=False
    )


def flatten_bvh(root):
    if root is None:
        return {
            "nodes": [],
            "objects": [],
            "root_index": -1,
        }

    flat_nodes = []
    flat_objects = []

    def recurse(node):
        node_index = len(flat_nodes)
        flat_nodes.append(None)

        if node.is_leaf:
            start = len(flat_objects)
            count = len(node.objects)
            flat_objects.extend(node.objects)

            flat_nodes[node_index] = {
                "aabb": node.aabb,
                "left": -1,
                "right": -1,
                "start": start,
                "count": count,
                "is_leaf": True,
            }
            return node_index

        left_index = recurse(node.left)
        right_index = recurse(node.right)

        flat_nodes[node_index] = {
            "aabb": node.aabb,
            "left": left_index,
            "right": right_index,
            "start": -1,
            "count": 0,
            "is_leaf": False,
        }
        return node_index

    root_index = recurse(root)

    return {
        "nodes": flat_nodes,
        "objects": flat_objects,
        "root_index": root_index,
    }


def build_bvh(objects, leaf_size=LEAF_SIZE, num_bins=NUM_BINS):
    tree_root = build_bvh_tree(objects, leaf_size, num_bins)
    return flatten_bvh(tree_root)


def bvh_intersect(ray, flat_bvh, best_t=None):
    if flat_bvh is None:
        return None, None
    if flat_bvh["root_index"] == -1:
        return None, None

    nodes = flat_bvh["nodes"]
    objects = flat_bvh["objects"]

    stack = [flat_bvh["root_index"]]
    best_object = None
    current_best_t = best_t

    while stack:
        node_index = stack.pop()
        node = nodes[node_index]

        node_hit = node["aabb"].intersect(ray)
        if node_hit is None:
            continue

        node_t_enter, _ = node_hit
        if current_best_t is not None and node_t_enter > current_best_t:
            continue

        if node["is_leaf"]:
            start = node["start"]
            end = start + node["count"]

            for i in range(start, end):
                obj = objects[i]
                t = obj.intersect(ray)
                if t is None:
                    continue

                if current_best_t is None or t < current_best_t:
                    current_best_t = t
                    best_object = obj

            continue

        left_index = node["left"]
        right_index = node["right"]

        left_hit = nodes[left_index]["aabb"].intersect(ray) if left_index != -1 else None
        right_hit = nodes[right_index]["aabb"].intersect(ray) if right_index != -1 else None

        if left_hit is None and right_hit is None:
            continue

        if right_hit is None:
            stack.append(left_index)
            continue

        if left_hit is None:
            stack.append(right_index)
            continue

        if left_hit[0] <= right_hit[0]:
            near_index, far_index = left_index, right_index
            far_hit = right_hit
        else:
            near_index, far_index = right_index, left_index
            far_hit = left_hit

        if current_best_t is None or far_hit[0] <= current_best_t:
            stack.append(far_index)

        stack.append(near_index)

    return best_object, current_best_t


def split_bvh_objects(objects):
    bvh_objects = []
    non_bvh = []

    for obj in objects:
        if obj.get_aabb() is None:
            non_bvh.append(obj)
        else:
            bvh_objects.append(obj)

    return bvh_objects, non_bvh


def is_shadow_blocked(shadow_ray, objects, distance_to_light):
    if config.use_bvh:
        if bvh_shadow_blocked(shadow_ray, config.bvh_root, distance_to_light):
            return True

        for obj in config.non_bvh_objects:
            t = obj.intersect(shadow_ray)
            if t is not None and t < distance_to_light:
                return True

        return False

    if config.blocker_cache_object is not None:
        t = config.blocker_cache_object.intersect(shadow_ray)
        if t is not None and t < distance_to_light:
            return True

    for obj in objects:
        if obj is config.blocker_cache_object:
            continue

        t = obj.intersect(shadow_ray)
        if t is not None and t < distance_to_light:
            config.blocker_cache_object = obj
            return True

    return False


def bvh_shadow_blocked(shadow_ray, flat_bvh, distance_to_light):
    if flat_bvh is None:
        return False
    if flat_bvh["root_index"] == -1:
        return False

    nodes = flat_bvh["nodes"]
    objects = flat_bvh["objects"]

    stack = [flat_bvh["root_index"]]

    while stack:
        node_index = stack.pop()
        node = nodes[node_index]

        node_hit = node["aabb"].intersect(shadow_ray)
        if node_hit is None:
            continue

        node_t_enter, _ = node_hit
        if node_t_enter > distance_to_light:
            continue

        if node["is_leaf"]:
            start = node["start"]
            end = start + node["count"]

            for i in range(start, end):
                obj = objects[i]
                t = obj.intersect(shadow_ray)
                if t is not None and t < distance_to_light:
                    return True

            continue

        left_index = node["left"]
        right_index = node["right"]

        left_hit = nodes[left_index]["aabb"].intersect(shadow_ray) if left_index != -1 else None
        right_hit = nodes[right_index]["aabb"].intersect(shadow_ray) if right_index != -1 else None

        if left_hit is None and right_hit is None:
            continue

        if right_hit is None:
            stack.append(left_index)
            continue

        if left_hit is None:
            stack.append(right_index)
            continue

        if left_hit[0] <= right_hit[0]:
            near_index, far_index = left_index, right_index
        else:
            near_index, far_index = right_index, left_index

        stack.append(far_index)
        stack.append(near_index)

    return False