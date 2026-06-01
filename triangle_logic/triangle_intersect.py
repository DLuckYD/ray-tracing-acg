import numpy as np
from numba import njit


@njit(cache=True, fastmath=True)
def intersect_triangle_kernel(
    ox, oy, oz,
    dx, dy, dz,
    v0x_arr, v0y_arr, v0z_arr,
    v1x_arr, v1y_arr, v1z_arr,
    v2x_arr, v2y_arr, v2z_arr,
    triangle_index
):
    epsilon = 0.000001

    v0x = v0x_arr[triangle_index]
    v0y = v0y_arr[triangle_index]
    v0z = v0z_arr[triangle_index]

    v1x = v1x_arr[triangle_index]
    v1y = v1y_arr[triangle_index]
    v1z = v1z_arr[triangle_index]

    v2x = v2x_arr[triangle_index]
    v2y = v2y_arr[triangle_index]
    v2z = v2z_arr[triangle_index]

    edge1x = v1x - v0x
    edge1y = v1y - v0y
    edge1z = v1z - v0z

    edge2x = v2x - v0x
    edge2y = v2y - v0y
    edge2z = v2z - v0z

    pvec_x = dy * edge2z - dz * edge2y
    pvec_y = dz * edge2x - dx * edge2z
    pvec_z = dx * edge2y - dy * edge2x

    det = edge1x * pvec_x + edge1y * pvec_y + edge1z * pvec_z

    if -epsilon < det < epsilon:
        return -1.0

    inv_det = 1.0 / det

    tvec_x = ox - v0x
    tvec_y = oy - v0y
    tvec_z = oz - v0z

    u = (tvec_x * pvec_x + tvec_y * pvec_y + tvec_z * pvec_z) * inv_det
    if u < 0.0 or u > 1.0:
        return -1.0

    qvec_x = tvec_y * edge1z - tvec_z * edge1y
    qvec_y = tvec_z * edge1x - tvec_x * edge1z
    qvec_z = tvec_x * edge1y - tvec_y * edge1x

    v = (dx * qvec_x + dy * qvec_y + dz * qvec_z) * inv_det
    if v < 0.0 or (u + v) > 1.0:
        return -1.0

    t = (edge2x * qvec_x + edge2y * qvec_y + edge2z * qvec_z) * inv_det

    if t > epsilon:
        return t

    return -1.0


def intersect_triangle_by_index(ray, triangle_data, triangle_index):
    ox = ray.origin.x
    oy = ray.origin.y
    oz = ray.origin.z

    dx = ray.direction.x
    dy = ray.direction.y
    dz = ray.direction.z

    t = intersect_triangle_kernel(
        ox, oy, oz,
        dx, dy, dz,
        triangle_data["v0x"], triangle_data["v0y"], triangle_data["v0z"],
        triangle_data["v1x"], triangle_data["v1y"], triangle_data["v1z"],
        triangle_data["v2x"], triangle_data["v2y"], triangle_data["v2z"],
        triangle_index
    )

    if t < 0.0:
        return None
    return t