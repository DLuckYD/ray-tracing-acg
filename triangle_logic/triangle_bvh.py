import numpy as np
from numba import njit
import logic_scripts.config as config
from triangle_logic.triangle_intersect import intersect_triangle_kernel

try:
    import rt_core
    CPP_BACKEND_AVAILABLE = True
except ImportError:
    rt_core = None
    CPP_BACKEND_AVAILABLE = False


TRIANGLE_LEAF_SIZE = 8
TRIANGLE_NUM_BINS = 12


def merge_two_aabbs(aabb1, aabb2):
    return (
        min(aabb1[0], aabb2[0]),
        min(aabb1[1], aabb2[1]),
        min(aabb1[2], aabb2[2]),
        max(aabb1[3], aabb2[3]),
        max(aabb1[4], aabb2[4]),
        max(aabb1[5], aabb2[5]),
    )


def surface_area(aabb):
    sx = aabb[3] - aabb[0]
    sy = aabb[4] - aabb[1]
    sz = aabb[5] - aabb[2]
    return 2.0 * (sx * sy + sx * sz + sy * sz)


def compute_triangle_node_aabb(triangle_data, triangle_indices):
    aabb_min_x = triangle_data["aabb_min_x"]
    aabb_min_y = triangle_data["aabb_min_y"]
    aabb_min_z = triangle_data["aabb_min_z"]
    aabb_max_x = triangle_data["aabb_max_x"]
    aabb_max_y = triangle_data["aabb_max_y"]
    aabb_max_z = triangle_data["aabb_max_z"]

    first_idx = triangle_indices[0]
    result = (
        aabb_min_x[first_idx],
        aabb_min_y[first_idx],
        aabb_min_z[first_idx],
        aabb_max_x[first_idx],
        aabb_max_y[first_idx],
        aabb_max_z[first_idx],
    )

    for idx in triangle_indices[1:]:
        tri_aabb = (
            aabb_min_x[idx],
            aabb_min_y[idx],
            aabb_min_z[idx],
            aabb_max_x[idx],
            aabb_max_y[idx],
            aabb_max_z[idx],
        )
        result = merge_two_aabbs(result, tri_aabb)

    return result


def triangle_centroid(triangle_data, triangle_index):
    cx = triangle_data["centroid_x"]
    cy = triangle_data["centroid_y"]
    cz = triangle_data["centroid_z"]
    return cx[triangle_index], cy[triangle_index], cz[triangle_index]


def compute_centroid_bounds(triangle_data, triangle_indices):
    cx = triangle_data["centroid_x"]
    cy = triangle_data["centroid_y"]
    cz = triangle_data["centroid_z"]

    first_idx = triangle_indices[0]
    min_x = max_x = cx[first_idx]
    min_y = max_y = cy[first_idx]
    min_z = max_z = cz[first_idx]

    for idx in triangle_indices[1:]:
        x = cx[idx]
        y = cy[idx]
        z = cz[idx]

        min_x = min(min_x, x)
        min_y = min(min_y, y)
        min_z = min(min_z, z)

        max_x = max(max_x, x)
        max_y = max(max_y, y)
        max_z = max(max_z, z)

    return (min_x, min_y, min_z), (max_x, max_y, max_z)


def get_largest_axis_from_aabb(aabb):
    sx = aabb[3] - aabb[0]
    sy = aabb[4] - aabb[1]
    sz = aabb[5] - aabb[2]

    if sx >= sy and sx >= sz:
        return 0
    elif sy >= sx and sy >= sz:
        return 1
    else:
        return 2


def compute_sah_split(triangle_data, triangle_indices, axis, num_bins=TRIANGLE_NUM_BINS):
    if len(triangle_indices) <= TRIANGLE_LEAF_SIZE:
        return None

    centroid_min, centroid_max = compute_centroid_bounds(triangle_data, triangle_indices)

    min_axis = centroid_min[axis]
    max_axis = centroid_max[axis]
    extent = max_axis - min_axis

    if extent <= 1e-9:
        return None

    aabb_min_x = triangle_data["aabb_min_x"]
    aabb_min_y = triangle_data["aabb_min_y"]
    aabb_min_z = triangle_data["aabb_min_z"]
    aabb_max_x = triangle_data["aabb_max_x"]
    aabb_max_y = triangle_data["aabb_max_y"]
    aabb_max_z = triangle_data["aabb_max_z"]

    cx = triangle_data["centroid_x"]
    cy = triangle_data["centroid_y"]
    cz = triangle_data["centroid_z"]

    bins_count = [0] * num_bins
    bins_aabb = [None] * num_bins

    for idx in triangle_indices:
        if axis == 0:
            center_value = cx[idx]
        elif axis == 1:
            center_value = cy[idx]
        else:
            center_value = cz[idx]

        normalized = (center_value - min_axis) / extent
        bin_index = int(normalized * num_bins)
        if bin_index == num_bins:
            bin_index = num_bins - 1

        bins_count[bin_index] += 1

        tri_aabb = (
            aabb_min_x[idx],
            aabb_min_y[idx],
            aabb_min_z[idx],
            aabb_max_x[idx],
            aabb_max_y[idx],
            aabb_max_z[idx],
        )

        if bins_aabb[bin_index] is None:
            bins_aabb[bin_index] = tri_aabb
        else:
            bins_aabb[bin_index] = merge_two_aabbs(bins_aabb[bin_index], tri_aabb)

    left_count = [0] * num_bins
    left_aabb = [None] * num_bins

    running_count = 0
    running_aabb = None
    for i in range(num_bins):
        running_count += bins_count[i]
        left_count[i] = running_count

        if bins_aabb[i] is not None:
            if running_aabb is None:
                running_aabb = bins_aabb[i]
            else:
                running_aabb = merge_two_aabbs(running_aabb, bins_aabb[i])

        left_aabb[i] = running_aabb

    right_count = [0] * num_bins
    right_aabb = [None] * num_bins

    running_count = 0
    running_aabb = None
    for i in range(num_bins - 1, -1, -1):
        running_count += bins_count[i]
        right_count[i] = running_count

        if bins_aabb[i] is not None:
            if running_aabb is None:
                running_aabb = bins_aabb[i]
            else:
                running_aabb = merge_two_aabbs(running_aabb, bins_aabb[i])

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


def partition_triangle_indices(triangle_data, triangle_indices, axis, split_position):
    cx = triangle_data["centroid_x"]
    cy = triangle_data["centroid_y"]
    cz = triangle_data["centroid_z"]

    left_indices = []
    right_indices = []

    for idx in triangle_indices:
        if axis == 0:
            value = cx[idx]
        elif axis == 1:
            value = cy[idx]
        else:
            value = cz[idx]

        if value < split_position:
            left_indices.append(idx)
        else:
            right_indices.append(idx)

    return left_indices, right_indices


def build_triangle_bvh(triangle_data, leaf_size=TRIANGLE_LEAF_SIZE, num_bins=TRIANGLE_NUM_BINS):
    triangle_indices = list(range(len(triangle_data["v0x"])))
    triangle_bvh = _build_triangle_bvh_recursive(triangle_data, triangle_indices, leaf_size, num_bins)

    triangle_bvh["node_aabb_min_x"] = np.asarray(triangle_bvh["node_aabb_min_x"], dtype=np.float64)
    triangle_bvh["node_aabb_min_y"] = np.asarray(triangle_bvh["node_aabb_min_y"], dtype=np.float64)
    triangle_bvh["node_aabb_min_z"] = np.asarray(triangle_bvh["node_aabb_min_z"], dtype=np.float64)
    triangle_bvh["node_aabb_max_x"] = np.asarray(triangle_bvh["node_aabb_max_x"], dtype=np.float64)
    triangle_bvh["node_aabb_max_y"] = np.asarray(triangle_bvh["node_aabb_max_y"], dtype=np.float64)
    triangle_bvh["node_aabb_max_z"] = np.asarray(triangle_bvh["node_aabb_max_z"], dtype=np.float64)

    triangle_bvh["node_left"] = np.asarray(triangle_bvh["node_left"], dtype=np.int32)
    triangle_bvh["node_right"] = np.asarray(triangle_bvh["node_right"], dtype=np.int32)
    triangle_bvh["node_start"] = np.asarray(triangle_bvh["node_start"], dtype=np.int32)
    triangle_bvh["node_count"] = np.asarray(triangle_bvh["node_count"], dtype=np.int32)
    triangle_bvh["node_is_leaf"] = np.asarray(triangle_bvh["node_is_leaf"], dtype=np.uint8)

    triangle_bvh["triangle_indices"] = np.asarray(triangle_bvh["triangle_indices"], dtype=np.int32)

    return triangle_bvh


def _build_triangle_bvh_recursive(triangle_data, triangle_indices, leaf_size, num_bins):
    if len(triangle_indices) == 0:
        return {
            "root_index": -1,
            "triangle_indices": [],
            "node_aabb_min_x": [],
            "node_aabb_min_y": [],
            "node_aabb_min_z": [],
            "node_aabb_max_x": [],
            "node_aabb_max_y": [],
            "node_aabb_max_z": [],
            "node_left": [],
            "node_right": [],
            "node_start": [],
            "node_count": [],
            "node_is_leaf": [],
        }

    class TempNode:
        def __init__(self, aabb, left=None, right=None, tri_indices=None, is_leaf=False):
            self.aabb = aabb
            self.left = left
            self.right = right
            self.tri_indices = tri_indices if tri_indices is not None else []
            self.is_leaf = is_leaf

    def build(indices):
        node_aabb = compute_triangle_node_aabb(triangle_data, indices)

        if len(indices) <= leaf_size:
            return TempNode(node_aabb, tri_indices=indices, is_leaf=True)

        axis = get_largest_axis_from_aabb(node_aabb)
        split_position = compute_sah_split(triangle_data, indices, axis, num_bins)

        if split_position is None:
            cx = triangle_data["centroid_x"]
            cy = triangle_data["centroid_y"]
            cz = triangle_data["centroid_z"]

            if axis == 0:
                indices.sort(key=lambda idx: cx[idx])
            elif axis == 1:
                indices.sort(key=lambda idx: cy[idx])
            else:
                indices.sort(key=lambda idx: cz[idx])

            mid = len(indices) // 2
            left_indices = indices[:mid]
            right_indices = indices[mid:]
        else:
            left_indices, right_indices = partition_triangle_indices(triangle_data, indices, axis, split_position)

            if len(left_indices) == 0 or len(right_indices) == 0:
                cx = triangle_data["centroid_x"]
                cy = triangle_data["centroid_y"]
                cz = triangle_data["centroid_z"]

                if axis == 0:
                    indices.sort(key=lambda idx: cx[idx])
                elif axis == 1:
                    indices.sort(key=lambda idx: cy[idx])
                else:
                    indices.sort(key=lambda idx: cz[idx])

                mid = len(indices) // 2
                left_indices = indices[:mid]
                right_indices = indices[mid:]

        left_node = build(left_indices)
        right_node = build(right_indices)

        return TempNode(node_aabb, left=left_node, right=right_node, is_leaf=False)

    root = build(triangle_indices)

    flat_triangle_indices = []

    node_aabb_min_x = []
    node_aabb_min_y = []
    node_aabb_min_z = []
    node_aabb_max_x = []
    node_aabb_max_y = []
    node_aabb_max_z = []

    node_left = []
    node_right = []
    node_start = []
    node_count = []
    node_is_leaf = []

    def flatten(node):
        node_index = len(node_left)

        node_aabb_min_x.append(0.0)
        node_aabb_min_y.append(0.0)
        node_aabb_min_z.append(0.0)
        node_aabb_max_x.append(0.0)
        node_aabb_max_y.append(0.0)
        node_aabb_max_z.append(0.0)

        node_left.append(-1)
        node_right.append(-1)
        node_start.append(-1)
        node_count.append(0)
        node_is_leaf.append(0)

        min_x, min_y, min_z, max_x, max_y, max_z = node.aabb
        node_aabb_min_x[node_index] = min_x
        node_aabb_min_y[node_index] = min_y
        node_aabb_min_z[node_index] = min_z
        node_aabb_max_x[node_index] = max_x
        node_aabb_max_y[node_index] = max_y
        node_aabb_max_z[node_index] = max_z

        if node.is_leaf:
            start = len(flat_triangle_indices)
            count = len(node.tri_indices)
            flat_triangle_indices.extend(node.tri_indices)

            node_start[node_index] = start
            node_count[node_index] = count
            node_is_leaf[node_index] = 1
            return node_index

        left_index = flatten(node.left)
        right_index = flatten(node.right)

        node_left[node_index] = left_index
        node_right[node_index] = right_index
        node_is_leaf[node_index] = 0

        return node_index

    root_index = flatten(root)

    return {
        "root_index": root_index,
        "triangle_indices": flat_triangle_indices,
        "node_aabb_min_x": node_aabb_min_x,
        "node_aabb_min_y": node_aabb_min_y,
        "node_aabb_min_z": node_aabb_min_z,
        "node_aabb_max_x": node_aabb_max_x,
        "node_aabb_max_y": node_aabb_max_y,
        "node_aabb_max_z": node_aabb_max_z,
        "node_left": node_left,
        "node_right": node_right,
        "node_start": node_start,
        "node_count": node_count,
        "node_is_leaf": node_is_leaf,
    }


@njit(cache=True, fastmath=True)
def intersect_aabb_kernel(
    ox, oy, oz,
    dx, dy, dz,
    min_x, min_y, min_z,
    max_x, max_y, max_z
):
    epsilon = 0.000001

    if abs(dx) < epsilon:
        if ox < min_x or ox > max_x:
            return 0, 0.0, 0.0
        tx_min = -1.0e30
        tx_max = 1.0e30
    else:
        tx1 = (min_x - ox) / dx
        tx2 = (max_x - ox) / dx
        tx_min = tx1 if tx1 < tx2 else tx2
        tx_max = tx2 if tx1 < tx2 else tx1

    if abs(dy) < epsilon:
        if oy < min_y or oy > max_y:
            return 0, 0.0, 0.0
        ty_min = -1.0e30
        ty_max = 1.0e30
    else:
        ty1 = (min_y - oy) / dy
        ty2 = (max_y - oy) / dy
        ty_min = ty1 if ty1 < ty2 else ty2
        ty_max = ty2 if ty1 < ty2 else ty1

    if abs(dz) < epsilon:
        if oz < min_z or oz > max_z:
            return 0, 0.0, 0.0
        tz_min = -1.0e30
        tz_max = 1.0e30
    else:
        tz1 = (min_z - oz) / dz
        tz2 = (max_z - oz) / dz
        tz_min = tz1 if tz1 < tz2 else tz2
        tz_max = tz2 if tz1 < tz2 else tz1

    t_enter = tx_min
    if ty_min > t_enter:
        t_enter = ty_min
    if tz_min > t_enter:
        t_enter = tz_min

    t_exit = tx_max
    if ty_max < t_exit:
        t_exit = ty_max
    if tz_max < t_exit:
        t_exit = tz_max

    if t_enter > t_exit:
        return 0, 0.0, 0.0
    if t_exit < 0.0:
        return 0, 0.0, 0.0

    return 1, t_enter, t_exit


@njit(cache=True, fastmath=True)
def triangle_bvh_intersect_kernel(
    ox, oy, oz,
    dx, dy, dz,
    root_index,
    flat_triangle_indices,
    node_aabb_min_x,
    node_aabb_min_y,
    node_aabb_min_z,
    node_aabb_max_x,
    node_aabb_max_y,
    node_aabb_max_z,
    node_left,
    node_right,
    node_start,
    node_count,
    node_is_leaf,
    v0x, v0y, v0z,
    v1x, v1y, v1z,
    v2x, v2y, v2z
):
    if root_index == -1:
        return -1, -1.0

    stack = np.empty(len(node_left), dtype=np.int32)
    stack_size = 1
    stack[0] = root_index

    best_triangle_index = -1
    best_t = -1.0

    while stack_size > 0:
        stack_size -= 1
        node_index = stack[stack_size]

        hit, node_t_enter, _ = intersect_aabb_kernel(
            ox, oy, oz, dx, dy, dz,
            node_aabb_min_x[node_index],
            node_aabb_min_y[node_index],
            node_aabb_min_z[node_index],
            node_aabb_max_x[node_index],
            node_aabb_max_y[node_index],
            node_aabb_max_z[node_index]
        )

        if hit == 0:
            continue

        if best_t > 0.0 and node_t_enter > best_t:
            continue

        if node_is_leaf[node_index] == 1:
            start = node_start[node_index]
            end = start + node_count[node_index]

            for i in range(start, end):
                triangle_index = flat_triangle_indices[i]

                t = intersect_triangle_kernel(
                    ox, oy, oz, dx, dy, dz,
                    v0x, v0y, v0z,
                    v1x, v1y, v1z,
                    v2x, v2y, v2z,
                    triangle_index
                )

                if t > 0.0:
                    if best_t < 0.0 or t < best_t:
                        best_t = t
                        best_triangle_index = triangle_index

            continue

        left_index = node_left[node_index]
        right_index = node_right[node_index]

        left_hit = 0
        left_t_enter = 0.0
        right_hit = 0
        right_t_enter = 0.0

        if left_index != -1:
            left_hit, left_t_enter, _ = intersect_aabb_kernel(
                ox, oy, oz, dx, dy, dz,
                node_aabb_min_x[left_index],
                node_aabb_min_y[left_index],
                node_aabb_min_z[left_index],
                node_aabb_max_x[left_index],
                node_aabb_max_y[left_index],
                node_aabb_max_z[left_index]
            )

        if right_index != -1:
            right_hit, right_t_enter, _ = intersect_aabb_kernel(
                ox, oy, oz, dx, dy, dz,
                node_aabb_min_x[right_index],
                node_aabb_min_y[right_index],
                node_aabb_min_z[right_index],
                node_aabb_max_x[right_index],
                node_aabb_max_y[right_index],
                node_aabb_max_z[right_index]
            )

        if left_hit == 0 and right_hit == 0:
            continue

        if right_hit == 0:
            stack[stack_size] = left_index
            stack_size += 1
            continue

        if left_hit == 0:
            stack[stack_size] = right_index
            stack_size += 1
            continue

        if left_t_enter <= right_t_enter:
            near_index = left_index
            far_index = right_index
            far_t_enter = right_t_enter
        else:
            near_index = right_index
            far_index = left_index
            far_t_enter = left_t_enter

        if best_t < 0.0 or far_t_enter <= best_t:
            stack[stack_size] = far_index
            stack_size += 1

        stack[stack_size] = near_index
        stack_size += 1

    return best_triangle_index, best_t


@njit(cache=True, fastmath=True)
def triangle_bvh_shadow_blocked_kernel(
    ox, oy, oz,
    dx, dy, dz,
    max_distance,
    root_index,
    flat_triangle_indices,
    node_aabb_min_x,
    node_aabb_min_y,
    node_aabb_min_z,
    node_aabb_max_x,
    node_aabb_max_y,
    node_aabb_max_z,
    node_left,
    node_right,
    node_start,
    node_count,
    node_is_leaf,
    v0x, v0y, v0z,
    v1x, v1y, v1z,
    v2x, v2y, v2z
):
    if root_index == -1:
        return 0

    stack = np.empty(len(node_left), dtype=np.int32)
    stack_size = 1
    stack[0] = root_index

    while stack_size > 0:
        stack_size -= 1
        node_index = stack[stack_size]

        hit, node_t_enter, _ = intersect_aabb_kernel(
            ox, oy, oz, dx, dy, dz,
            node_aabb_min_x[node_index],
            node_aabb_min_y[node_index],
            node_aabb_min_z[node_index],
            node_aabb_max_x[node_index],
            node_aabb_max_y[node_index],
            node_aabb_max_z[node_index]
        )

        if hit == 0:
            continue

        if node_t_enter > max_distance:
            continue

        if node_is_leaf[node_index] == 1:
            start = node_start[node_index]
            end = start + node_count[node_index]

            for i in range(start, end):
                triangle_index = flat_triangle_indices[i]

                t = intersect_triangle_kernel(
                    ox, oy, oz, dx, dy, dz,
                    v0x, v0y, v0z,
                    v1x, v1y, v1z,
                    v2x, v2y, v2z,
                    triangle_index
                )

                if t > 0.0 and t < max_distance:
                    return 1

            continue

        left_index = node_left[node_index]
        right_index = node_right[node_index]

        left_hit = 0
        left_t_enter = 0.0
        right_hit = 0
        right_t_enter = 0.0

        if left_index != -1:
            left_hit, left_t_enter, _ = intersect_aabb_kernel(
                ox, oy, oz, dx, dy, dz,
                node_aabb_min_x[left_index],
                node_aabb_min_y[left_index],
                node_aabb_min_z[left_index],
                node_aabb_max_x[left_index],
                node_aabb_max_y[left_index],
                node_aabb_max_z[left_index]
            )

        if right_index != -1:
            right_hit, right_t_enter, _ = intersect_aabb_kernel(
                ox, oy, oz, dx, dy, dz,
                node_aabb_min_x[right_index],
                node_aabb_min_y[right_index],
                node_aabb_min_z[right_index],
                node_aabb_max_x[right_index],
                node_aabb_max_y[right_index],
                node_aabb_max_z[right_index]
            )

        if left_hit == 0 and right_hit == 0:
            continue

        if right_hit == 0:
            stack[stack_size] = left_index
            stack_size += 1
            continue

        if left_hit == 0:
            stack[stack_size] = right_index
            stack_size += 1
            continue

        if left_t_enter <= right_t_enter:
            near_index = left_index
            far_index = right_index
        else:
            near_index = right_index
            far_index = left_index

        stack[stack_size] = far_index
        stack_size += 1
        stack[stack_size] = near_index
        stack_size += 1

    return 0


def triangle_bvh_intersect_numba(ray, triangle_bvh, triangle_data):
    if triangle_bvh is None or triangle_bvh["root_index"] == -1:
        return None, None

    ox = ray.origin.x
    oy = ray.origin.y
    oz = ray.origin.z

    dx = ray.direction.x
    dy = ray.direction.y
    dz = ray.direction.z

    triangle_index, t = triangle_bvh_intersect_kernel(
        ox, oy, oz,
        dx, dy, dz,
        triangle_bvh["root_index"],
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
    )

    if triangle_index < 0 or t < 0.0:
        return None, None

    return int(triangle_index), float(t)


def triangle_bvh_intersect_cpp(ray, triangle_bvh, triangle_data):
    if not CPP_BACKEND_AVAILABLE:
        return None, None

    if triangle_bvh is None or triangle_bvh["root_index"] == -1:
        return None, None

    ox = ray.origin.x
    oy = ray.origin.y
    oz = ray.origin.z

    dx = ray.direction.x
    dy = ray.direction.y
    dz = ray.direction.z

    triangle_index, t = rt_core.triangle_bvh_intersect_cpp(
        ox, oy, oz,
        dx, dy, dz,
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
    )

    if triangle_index < 0 or t < 0.0:
        return None, None

    return int(triangle_index), float(t)


def triangle_bvh_shadow_blocked_numba(ray, max_distance, triangle_bvh, triangle_data):
    if triangle_bvh is None or triangle_bvh["root_index"] == -1:
        return False

    ox = ray.origin.x
    oy = ray.origin.y
    oz = ray.origin.z

    dx = ray.direction.x
    dy = ray.direction.y
    dz = ray.direction.z

    result = triangle_bvh_shadow_blocked_kernel(
        ox, oy, oz,
        dx, dy, dz,
        max_distance,
        triangle_bvh["root_index"],
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
    )

    return result == 1


def triangle_bvh_shadow_blocked_cpp(ray, max_distance, triangle_bvh, triangle_data):
    if not CPP_BACKEND_AVAILABLE:
        return False

    if triangle_bvh is None or triangle_bvh["root_index"] == -1:
        return False

    ox = ray.origin.x
    oy = ray.origin.y
    oz = ray.origin.z

    dx = ray.direction.x
    dy = ray.direction.y
    dz = ray.direction.z

    return rt_core.triangle_bvh_shadow_blocked_cpp(
        ox, oy, oz,
        dx, dy, dz,
        max_distance,
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
    )


def triangle_bvh_intersect(ray, triangle_bvh, triangle_data):
    if config.backend_mode == "cpp" and CPP_BACKEND_AVAILABLE:
        return triangle_bvh_intersect_cpp(ray, triangle_bvh, triangle_data)
    return triangle_bvh_intersect_numba(ray, triangle_bvh, triangle_data)


def triangle_bvh_shadow_blocked(ray, max_distance, triangle_bvh, triangle_data):
    if config.backend_mode == "cpp" and CPP_BACKEND_AVAILABLE:
        return triangle_bvh_shadow_blocked_cpp(ray, max_distance, triangle_bvh, triangle_data)
    return triangle_bvh_shadow_blocked_numba(ray, max_distance, triangle_bvh, triangle_data)