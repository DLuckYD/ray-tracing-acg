from logic_scripts.geometry import Triangle
import numpy as np


def build_triangle_data(objects):
    v0x, v0y, v0z = [], [], []
    v1x, v1y, v1z = [], [], []
    v2x, v2y, v2z = [], [], []

    centroid_x, centroid_y, centroid_z = [], [], []
    normal_x, normal_y, normal_z = [], [], []

    color_r, color_g, color_b = [], [], []
    reflection = []
    transparency = []
    ior = []

    uv0_u, uv0_v = [], []
    uv1_u, uv1_v = [], []
    uv2_u, uv2_v = [], []
    has_uv = []

    material_name = []
    texture_path = []
    has_texture = []

    aabb_min_x, aabb_min_y, aabb_min_z = [], [], []
    aabb_max_x, aabb_max_y, aabb_max_z = [], [], []

    non_triangle_objects = []

    for obj in objects:
        if isinstance(obj, Triangle):
            v0x.append(obj.v0.x)
            v0y.append(obj.v0.y)
            v0z.append(obj.v0.z)

            v1x.append(obj.v1.x)
            v1y.append(obj.v1.y)
            v1z.append(obj.v1.z)

            v2x.append(obj.v2.x)
            v2y.append(obj.v2.y)
            v2z.append(obj.v2.z)

            centroid_x.append((obj.v0.x + obj.v1.x + obj.v2.x) / 3.0)
            centroid_y.append((obj.v0.y + obj.v1.y + obj.v2.y) / 3.0)
            centroid_z.append((obj.v0.z + obj.v1.z + obj.v2.z) / 3.0)

            edge1x = obj.v1.x - obj.v0.x
            edge1y = obj.v1.y - obj.v0.y
            edge1z = obj.v1.z - obj.v0.z

            edge2x = obj.v2.x - obj.v0.x
            edge2y = obj.v2.y - obj.v0.y
            edge2z = obj.v2.z - obj.v0.z

            nx = edge1y * edge2z - edge1z * edge2y
            ny = edge1z * edge2x - edge1x * edge2z
            nz = edge1x * edge2y - edge1y * edge2x

            length = (nx * nx + ny * ny + nz * nz) ** 0.5
            if length == 0.0:
                normal_x.append(0.0)
                normal_y.append(0.0)
                normal_z.append(0.0)
            else:
                inv_len = 1.0 / length
                normal_x.append(nx * inv_len)
                normal_y.append(ny * inv_len)
                normal_z.append(nz * inv_len)

            color_r.append(obj.color.x)
            color_g.append(obj.color.y)
            color_b.append(obj.color.z)

            reflection.append(obj.reflection)
            transparency.append(obj.transparency)
            ior.append(obj.ior)

            if obj.has_uv():
                uv0_u.append(obj.uv0[0])
                uv0_v.append(obj.uv0[1])

                uv1_u.append(obj.uv1[0])
                uv1_v.append(obj.uv1[1])

                uv2_u.append(obj.uv2[0])
                uv2_v.append(obj.uv2[1])

                has_uv.append(1)
            else:
                uv0_u.append(0.0)
                uv0_v.append(0.0)

                uv1_u.append(0.0)
                uv1_v.append(0.0)

                uv2_u.append(0.0)
                uv2_v.append(0.0)

                has_uv.append(0)

            material_name.append(obj.material_name if obj.material_name is not None else "")
            texture_path.append(obj.texture_path if obj.texture_path is not None else "")
            has_texture.append(1 if obj.texture_path else 0)

            tri_aabb = obj.get_aabb()
            aabb_min_x.append(tri_aabb.min_point.x)
            aabb_min_y.append(tri_aabb.min_point.y)
            aabb_min_z.append(tri_aabb.min_point.z)

            aabb_max_x.append(tri_aabb.max_point.x)
            aabb_max_y.append(tri_aabb.max_point.y)
            aabb_max_z.append(tri_aabb.max_point.z)
        else:
            non_triangle_objects.append(obj)

    return {
        "v0x": np.asarray(v0x, dtype=np.float64),
        "v0y": np.asarray(v0y, dtype=np.float64),
        "v0z": np.asarray(v0z, dtype=np.float64),

        "v1x": np.asarray(v1x, dtype=np.float64),
        "v1y": np.asarray(v1y, dtype=np.float64),
        "v1z": np.asarray(v1z, dtype=np.float64),

        "v2x": np.asarray(v2x, dtype=np.float64),
        "v2y": np.asarray(v2y, dtype=np.float64),
        "v2z": np.asarray(v2z, dtype=np.float64),

        "centroid_x": np.asarray(centroid_x, dtype=np.float64),
        "centroid_y": np.asarray(centroid_y, dtype=np.float64),
        "centroid_z": np.asarray(centroid_z, dtype=np.float64),

        "normal_x": np.asarray(normal_x, dtype=np.float64),
        "normal_y": np.asarray(normal_y, dtype=np.float64),
        "normal_z": np.asarray(normal_z, dtype=np.float64),

        "color_r": np.asarray(color_r, dtype=np.float64),
        "color_g": np.asarray(color_g, dtype=np.float64),
        "color_b": np.asarray(color_b, dtype=np.float64),

        "reflection": np.asarray(reflection, dtype=np.float64),
        "transparency": np.asarray(transparency, dtype=np.float64),
        "ior": np.asarray(ior, dtype=np.float64),

        "uv0_u": np.asarray(uv0_u, dtype=np.float64),
        "uv0_v": np.asarray(uv0_v, dtype=np.float64),
        "uv1_u": np.asarray(uv1_u, dtype=np.float64),
        "uv1_v": np.asarray(uv1_v, dtype=np.float64),
        "uv2_u": np.asarray(uv2_u, dtype=np.float64),
        "uv2_v": np.asarray(uv2_v, dtype=np.float64),
        "has_uv": np.asarray(has_uv, dtype=np.uint8),

        "material_name": np.asarray(material_name, dtype=object),
        "texture_path": np.asarray(texture_path, dtype=object),
        "has_texture": np.asarray(has_texture, dtype=np.uint8),

        "aabb_min_x": np.asarray(aabb_min_x, dtype=np.float64),
        "aabb_min_y": np.asarray(aabb_min_y, dtype=np.float64),
        "aabb_min_z": np.asarray(aabb_min_z, dtype=np.float64),

        "aabb_max_x": np.asarray(aabb_max_x, dtype=np.float64),
        "aabb_max_y": np.asarray(aabb_max_y, dtype=np.float64),
        "aabb_max_z": np.asarray(aabb_max_z, dtype=np.float64),

        "non_triangle_objects": non_triangle_objects,
    }