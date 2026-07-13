from pathlib import Path
from logic_scripts.math3d import Vec3
from logic_scripts.geometry import Triangle


def transform_vertex(vertex, scale, position):
    return Vec3(
        vertex.x * scale + position.x,
        vertex.y * scale + position.y,
        vertex.z * scale + position.z
    )


def parse_face_vertex(token):
    parts = token.split("/")

    vertex_index = int(parts[0]) - 1 if parts and parts[0] else None
    uv_index = None

    if len(parts) > 1 and parts[1]:
        uv_index = int(parts[1]) - 1

    return vertex_index, uv_index


def resolve_models_dir():
    return Path(__file__).resolve().parent.parent / "models"


def clamp01(value):
    return max(0.0, min(1.0, value))


def parse_mtl_float(parts, default_value=0.0):
    try:
        return float(parts[1])
    except Exception:
        return default_value


def parse_mtl_vec3(parts, default_value=None):
    if default_value is None:
        default_value = Vec3(0.8, 0.8, 0.8)

    try:
        return Vec3(float(parts[1]), float(parts[2]), float(parts[3]))
    except Exception:
        return default_value


def compute_reflection_from_mtl(material_data):
    ks = material_data.get("Ks")
    ns = material_data.get("Ns", 0.0)
    illum = material_data.get("illum", 2)

    ks_strength = 0.0
    if ks is not None:
        ks_strength = (ks.x + ks.y + ks.z) / 3.0

    # Base estimate from specular color + shininess
    reflection = ks_strength * 0.35

    # Boost for higher specular exponent
    reflection += min(ns / 1000.0, 1.0) * 0.25

    # illum 3+ often means reflective/specular workflow
    if illum >= 3:
        reflection += 0.15

    return clamp01(reflection)


def load_mtl_file(mtl_path: Path):
    materials = {}

    if not mtl_path.exists():
        print(f"MTL file not found: {mtl_path}")
        return materials

    current_material = None

    with open(mtl_path, "r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split()
            keyword = parts[0]

            if keyword == "newmtl" and len(parts) >= 2:
                current_material = parts[1]
                materials[current_material] = {
                    "Kd": None,
                    "Ks": None,
                    "Ns": 0.0,
                    "Ni": 1.0,
                    "d": 1.0,
                    "illum": 2,
                    "map_Kd": None,
                }

            elif current_material is None:
                continue

            elif keyword == "Kd" and len(parts) >= 4:
                materials[current_material]["Kd"] = parse_mtl_vec3(parts)

            elif keyword == "Ks" and len(parts) >= 4:
                materials[current_material]["Ks"] = parse_mtl_vec3(parts, Vec3(0.0, 0.0, 0.0))

            elif keyword == "Ns" and len(parts) >= 2:
                materials[current_material]["Ns"] = parse_mtl_float(parts, 0.0)

            elif keyword == "Ni" and len(parts) >= 2:
                materials[current_material]["Ni"] = parse_mtl_float(parts, 1.0)

            elif keyword == "d" and len(parts) >= 2:
                materials[current_material]["d"] = parse_mtl_float(parts, 1.0)

            elif keyword == "Tr" and len(parts) >= 2:
                # Some exporters use Tr instead of d; Tr is inverse opacity in many cases
                tr = parse_mtl_float(parts, 0.0)
                materials[current_material]["d"] = 1.0 - tr

            elif keyword == "illum" and len(parts) >= 2:
                try:
                    materials[current_material]["illum"] = int(parts[1])
                except Exception:
                    materials[current_material]["illum"] = 2

            elif keyword == "map_Kd" and len(parts) >= 2:
                texture_rel_path = " ".join(parts[1:])
                texture_abs_path = (mtl_path.parent / texture_rel_path).resolve()
                materials[current_material]["map_Kd"] = str(texture_abs_path)

    return materials


def resolve_material_parameters(
    material_data,
    color,
    reflection,
    transparency,
    ior,
    use_mtl_color,
    use_mtl_material_properties,
):
    # Color
    material_kd = material_data.get("Kd")
    if color is not None:
        final_color = color
    elif use_mtl_color and material_kd is not None:
        final_color = material_kd
    else:
        final_color = Vec3(0.8, 0.8, 0.8)

    # Reflection / transparency / ior
    final_reflection = reflection
    final_transparency = transparency
    final_ior = ior

    if use_mtl_material_properties:
        if reflection is None:
            final_reflection = compute_reflection_from_mtl(material_data)

        if transparency is None:
            opacity = material_data.get("d", 1.0)
            final_transparency = clamp01(1.0 - opacity)

        if ior is None:
            final_ior = max(1.0, material_data.get("Ni", 1.0))

    if final_reflection is None:
        final_reflection = 0.0
    if final_transparency is None:
        final_transparency = 0.0
    if final_ior is None:
        final_ior = 1.0

    final_reflection = clamp01(final_reflection)
    final_transparency = clamp01(final_transparency)
    final_ior = max(1.0, final_ior)

    return final_color, final_reflection, final_transparency, final_ior


def build_triangle_from_indices(
    vertices,
    uvs,
    face_triplet,
    scale,
    position,
    final_color,
    final_reflection,
    final_transparency,
    final_ior,
    current_material_name,
    texture_path,
):
    (i0, uv0_idx), (i1, uv1_idx), (i2, uv2_idx) = face_triplet

    v0 = transform_vertex(vertices[i0], scale, position)
    v1 = transform_vertex(vertices[i1], scale, position)
    v2 = transform_vertex(vertices[i2], scale, position)

    uv0 = uvs[uv0_idx] if uv0_idx is not None and 0 <= uv0_idx < len(uvs) else None
    uv1 = uvs[uv1_idx] if uv1_idx is not None and 0 <= uv1_idx < len(uvs) else None
    uv2 = uvs[uv2_idx] if uv2_idx is not None and 0 <= uv2_idx < len(uvs) else None

    return Triangle(
        v0,
        v1,
        v2,
        final_color,
        final_reflection,
        final_transparency,
        final_ior,
        uv0=uv0,
        uv1=uv1,
        uv2=uv2,
        material_name=current_material_name,
        texture_path=texture_path,
    )


def load_obj_as_triangles(
    filepath,
    position,
    scale,
    color=None,
    reflection=None,
    transparency=None,
    ior=None,
    use_mtl_color=True,
    use_mtl_material_properties=True,
):
    models_dir = resolve_models_dir()
    full_path = (models_dir / filepath).resolve()

    vertices = []
    uvs = []
    triangles = []

    materials = {}
    current_material_name = None

    with open(full_path, "r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split()
            keyword = parts[0]

            # mtllib file.mtl
            if keyword == "mtllib" and len(parts) >= 2:
                mtl_rel_path = " ".join(parts[1:])
                mtl_full_path = (full_path.parent / mtl_rel_path).resolve()
                materials.update(load_mtl_file(mtl_full_path))

            # usemtl material_name
            elif keyword == "usemtl" and len(parts) >= 2:
                current_material_name = parts[1]

            # v x y z
            elif keyword == "v":
                if len(parts) < 4:
                    continue

                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])

                vertices.append(Vec3(x, y, z))

            # vt u v
            elif keyword == "vt":
                if len(parts) < 3:
                    continue

                try:
                    u = float(parts[1])
                    v = float(parts[2])
                    uvs.append((u, v))
                except ValueError:
                    continue

            # f ...
            elif keyword == "f":
                face_data = []

                for token in parts[1:]:
                    try:
                        vertex_index, uv_index = parse_face_vertex(token)
                        if vertex_index is not None:
                            face_data.append((vertex_index, uv_index))
                    except Exception:
                        continue

                if len(face_data) < 3:
                    continue

                material_data = materials.get(current_material_name, {})
                texture_path = material_data.get("map_Kd")

                final_color, final_reflection, final_transparency, final_ior = resolve_material_parameters(
                    material_data=material_data,
                    color=color,
                    reflection=reflection,
                    transparency=transparency,
                    ior=ior,
                    use_mtl_color=use_mtl_color,
                    use_mtl_material_properties=use_mtl_material_properties,
                )

                if len(face_data) == 3:
                    triangles.append(
                        build_triangle_from_indices(
                            vertices,
                            uvs,
                            [face_data[0], face_data[1], face_data[2]],
                            scale,
                            position,
                            final_color,
                            final_reflection,
                            final_transparency,
                            final_ior,
                            current_material_name,
                            texture_path,
                        )
                    )

                elif len(face_data) == 4:
                    triangles.append(
                        build_triangle_from_indices(
                            vertices,
                            uvs,
                            [face_data[0], face_data[1], face_data[2]],
                            scale,
                            position,
                            final_color,
                            final_reflection,
                            final_transparency,
                            final_ior,
                            current_material_name,
                            texture_path,
                        )
                    )
                    triangles.append(
                        build_triangle_from_indices(
                            vertices,
                            uvs,
                            [face_data[0], face_data[2], face_data[3]],
                            scale,
                            position,
                            final_color,
                            final_reflection,
                            final_transparency,
                            final_ior,
                            current_material_name,
                            texture_path,
                        )
                    )

                else:
                    for k in range(1, len(face_data) - 1):
                        triangles.append(
                            build_triangle_from_indices(
                                vertices,
                                uvs,
                                [face_data[0], face_data[k], face_data[k + 1]],
                                scale,
                                position,
                                final_color,
                                final_reflection,
                                final_transparency,
                                final_ior,
                                current_material_name,
                                texture_path,
                            )
                        )

    used_materials = sorted({tri.material_name for tri in triangles if tri.material_name})
    textured_triangles = sum(1 for tri in triangles if tri.texture_path is not None)
    uv_triangles = sum(1 for tri in triangles if tri.has_uv())

    avg_reflection = 0.0
    avg_transparency = 0.0
    if triangles:
        avg_reflection = sum(tri.reflection for tri in triangles) / len(triangles)
        avg_transparency = sum(tri.transparency for tri in triangles) / len(triangles)

    print(f"Loaded OBJ file: {filepath}")
    print(f"Vertices: {len(vertices)}")
    print(f"UVs: {len(uvs)}")
    print(f"Triangles: {len(triangles)}")
    print(f"Used materials: {len(used_materials)}")
    print(f"Triangles with UV: {uv_triangles}")
    print(f"Triangles with texture path: {textured_triangles}")
    print(f"Average reflection: {avg_reflection:.4f}")
    print(f"Average transparency: {avg_transparency:.4f}")

    return triangles


def add_obj_to_scene(
    objects,
    filepath,
    position,
    scale,
    color=None,
    reflection=None,
    transparency=None,
    ior=None,
    use_mtl_color=True,
    use_mtl_material_properties=True,
):
    mesh_triangles = load_obj_as_triangles(
        filepath=filepath,
        position=position,
        scale=scale,
        color=color,
        reflection=reflection,
        transparency=transparency,
        ior=ior,
        use_mtl_color=use_mtl_color,
        use_mtl_material_properties=use_mtl_material_properties,
    )
    objects.extend(mesh_triangles)