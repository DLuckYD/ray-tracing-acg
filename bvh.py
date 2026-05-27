import config
from aabb import AABB, compute_objects_aabb, get_largest_axis, get_aabb_center


LEAF_SIZE = 8
NUM_BINS = 12


class BVHNode:
    def __init__(self, aabb, left=None, right=None, objects=None, is_leaf=False):
        self.aabb = aabb
        self.left = left
        self.right = right
        self.objects = objects
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
    else:
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

    return AABB(
        aabb1.min_point.__class__(min_x, min_y, min_z),
        aabb1.max_point.__class__(max_x, max_y, max_z)
    )


def compute_sah_split(objects, axis, num_bins=NUM_BINS):
    if len(objects) <= LEAF_SIZE:
        return None

    centroid_min, centroid_max = compute_centroid_bounds(objects)

    min_axis = centroid_min[axis]
    max_axis = centroid_max[axis]
    extent = max_axis - min_axis

    if extent <= 1e-9:
        return None

    bins = []
    for _ in range(num_bins):
        bins.append({
            "count": 0,
            "aabb": None,
        })

    # Put objects into bins
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

    # Prefix from left
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

    # Prefix from right
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

    # Split between i and i+1
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


def build_bvh(objects, leaf_size=LEAF_SIZE, num_bins=NUM_BINS):
    valid_objects = []
    for obj in objects:
        if obj.get_aabb() is not None:
            valid_objects.append(obj)

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

    # Fallback to median split if SAH failed
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

        # Safety fallback if one side is empty
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

    left_node = build_bvh(left_objects, leaf_size, num_bins)
    right_node = build_bvh(right_objects, leaf_size, num_bins)

    return BVHNode(
        aabb=node_aabb,
        left=left_node,
        right=right_node,
        objects=None,
        is_leaf=False
    )


def bvh_intersect(ray, node, best_t=None):
    if node is None:
        return None, None

    node_hit = node.aabb.intersect(ray)
    if node_hit is None:
        return None, None

    node_t_enter, node_t_exit = node_hit

    if best_t is not None and node_t_enter > best_t:
        return None, None

    if node.is_leaf:
        hit_object = None
        hit_t = best_t

        for obj in node.objects:
            t = obj.intersect(ray)
            if t is None:
                continue

            if hit_t is None or t < hit_t:
                hit_t = t
                hit_object = obj

        return hit_object, hit_t

    left_hit = None
    right_hit = None

    if node.left is not None:
        left_hit = node.left.aabb.intersect(ray)
    if node.right is not None:
        right_hit = node.right.aabb.intersect(ray)

    if left_hit is None and right_hit is None:
        return None, None

    if right_hit is None:
        return bvh_intersect(ray, node.left, best_t)

    if left_hit is None:
        return bvh_intersect(ray, node.right, best_t)

    if left_hit[0] <= right_hit[0]:
        first_node, second_node = node.left, node.right
    else:
        first_node, second_node = node.right, node.left

    first_obj, first_t = bvh_intersect(ray, first_node, best_t)

    if first_t is not None:
        best_t = first_t

    second_obj, second_t = bvh_intersect(ray, second_node, best_t)

    if first_t is not None and second_t is None:
        return first_obj, first_t
    if second_t is not None and first_t is None:
        return second_obj, second_t
    if first_t is not None and second_t is not None:
        if first_t <= second_t:
            return first_obj, first_t
        else:
            return second_obj, second_t

    return None, None


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


def bvh_shadow_blocked(shadow_ray, node, distance_to_light):
    if node is None:
        return False

    node_hit = node.aabb.intersect(shadow_ray)
    if node_hit is None:
        return False

    node_t_enter, _ = node_hit
    if node_t_enter > distance_to_light:
        return False

    if node.is_leaf:
        for obj in node.objects:
            t = obj.intersect(shadow_ray)
            if t is not None and t < distance_to_light:
                return True
        return False

    left_hit = node.left.aabb.intersect(shadow_ray) if node.left else None
    right_hit = node.right.aabb.intersect(shadow_ray) if node.right else None

    if left_hit is None and right_hit is None:
        return False

    if right_hit is None:
        return bvh_shadow_blocked(shadow_ray, node.left, distance_to_light)

    if left_hit is None:
        return bvh_shadow_blocked(shadow_ray, node.right, distance_to_light)

    if left_hit[0] <= right_hit[0]:
        first_node, second_node = node.left, node.right
    else:
        first_node, second_node = node.right, node.left

    if bvh_shadow_blocked(shadow_ray, first_node, distance_to_light):
        return True

    if bvh_shadow_blocked(shadow_ray, second_node, distance_to_light):
        return True

    return False