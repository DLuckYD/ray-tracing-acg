from math3d import Vec3
from geometry import Triangle


def transform_vertex(vertex, scale, position):
    return Vec3(
        vertex.x * scale + position.x,
        vertex.y * scale + position.y,
        vertex.z * scale + position.z
    )

def parse_face_vertex(token):
    return int(token.split('/')[0]) - 1

def load_obj_as_triangles(filepath, position, scale, color, reflection=0.0, transparency=0.0, ior=1.0):
    vertices = []
    triangles = []

    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            parts = line.split()

            # -----------------------------------------
            # Vertex line: v x y z
            # -----------------------------------------
            if parts[0] == "v":
                if len(parts) < 4:
                    continue

                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])

                vertices.append(Vec3(x, y, z))

            # -----------------------------------------
            # Face line: f a b c ...
            # -----------------------------------------
            elif parts[0] == "f":
                face_indices = []

                for token in parts[1:]:
                    try:
                        vertex_index = parse_face_vertex(token)
                        face_indices.append(vertex_index)
                    except:
                        continue

                # Ignore broken faces
                if len(face_indices) < 3:
                    continue

                # -------------------------------------
                # Triangle
                # -------------------------------------
                if len(face_indices) == 3:
                    i0, i1, i2 = face_indices

                    v0 = transform_vertex(vertices[i0], scale, position)
                    v1 = transform_vertex(vertices[i1], scale, position)
                    v2 = transform_vertex(vertices[i2], scale, position)

                    triangles.append(
                        Triangle(v0, v1, v2, color, reflection, transparency, ior)
                    )

                # -------------------------------------
                # Quad -> split into 2 triangles
                # -------------------------------------
                elif len(face_indices) == 4:
                    i0, i1, i2, i3 = face_indices

                    v0 = transform_vertex(vertices[i0], scale, position)
                    v1 = transform_vertex(vertices[i1], scale, position)
                    v2 = transform_vertex(vertices[i2], scale, position)
                    v3 = transform_vertex(vertices[i3], scale, position)

                    triangles.append(
                        Triangle(v0, v1, v2, color, reflection, transparency, ior)
                    )
                    triangles.append(
                        Triangle(v0, v2, v3, color, reflection, transparency, ior)
                    )

                # -------------------------------------
                # Polygon with more than 4 vertices
                # Fan triangulation
                # -------------------------------------
                else:
                    i0 = face_indices[0]

                    for k in range(1, len(face_indices) - 1):
                        i1 = face_indices[k]
                        i2 = face_indices[k + 1]

                        v0 = transform_vertex(vertices[i0], scale, position)
                        v1 = transform_vertex(vertices[i1], scale, position)
                        v2 = transform_vertex(vertices[i2], scale, position)

                        triangles.append(
                            Triangle(v0, v1, v2, color, reflection, transparency, ior)
                        )

    print(f"Loaded OBJ file: {filepath}")
    print(f"Vertices: {len(vertices)}")
    print(f"Triangles: {len(triangles)}")

    return triangles

def add_obj_to_scene(objects, filepath, position, scale, color, reflection=0.0, transparency=0.0, ior=1.0):
    mesh_triangles = load_obj_as_triangles(
        filepath=filepath,
        position=position,
        scale=scale,
        color=color,
        reflection=reflection,
        transparency=transparency,
        ior=ior
    )
    objects.extend(mesh_triangles)