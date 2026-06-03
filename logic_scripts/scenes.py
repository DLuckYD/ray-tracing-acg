from logic_scripts.math3d import Vec3
from logic_scripts.geometry import Sphere, Plane, Triangle
from logic_scripts.obj_loader import add_obj_to_scene

def build_final_scene():
    # Main light source
    light_position = Vec3(-14, 12, 6)

    # Background color
    background_color = Vec3(0.05, 0.08, 0.14)

    # Scene object container
    objects = []

    # =========================================================
    # Main hero objects
    # =========================================================

    # Main central glass sphere
    objects.append(
        Sphere(Vec3(0.0, 0.8, -6.0), 1.5, Vec3(0.92, 0.95, 1.0), 0.08, 0.82, 1.5)
    )

    # Two reflective metallic spheres near the camera
    objects.append(
        Sphere(Vec3(-1.8, -0.4, -4.8), 0.7, Vec3(0.9, 0.9, 0.95), 0.75, 0.0, 1.0)
    )
    objects.append(
        Sphere(Vec3(1.8, -0.35, -5.0), 0.7, Vec3(0.9, 0.9, 0.95), 0.75, 0.0, 1.0)
    )

    # =========================================================
    # Large colored spheres around the center
    # =========================================================

    objects.append(
        Sphere(Vec3(-3.8, 0.7, -8.0), 1.15, Vec3(1.0, 0.15, 0.15), 0.18, 0.0, 1.0)
    )
    objects.append(
        Sphere(Vec3(3.9, 0.6, -8.2), 1.15, Vec3(0.15, 1.0, 0.2), 0.18, 0.0, 1.0)
    )
    objects.append(
        Sphere(Vec3(0.0, -0.1, -9.5), 1.25, Vec3(0.2, 0.45, 1.0), 0.22, 0.0, 1.0)
    )

    # =========================================================
    # Medium ring of spheres
    # =========================================================

    ring_data = [
        (-5.8, 1.2, -10.0, 0.75, Vec3(1.0, 0.95, 0.1), 0.12),
        (-4.5, -0.2, -9.2, 0.65, Vec3(1.0, 0.55, 0.05), 0.10),
        (-2.8, -1.0, -8.4, 0.60, Vec3(0.05, 0.95, 0.95), 0.10),
        (-0.8, -1.25, -8.0, 0.55, Vec3(0.85, 0.2, 1.0), 0.12),
        (1.2, -1.2, -8.0, 0.55, Vec3(1.0, 0.4, 0.8), 0.12),
        (3.0, -0.95, -8.5, 0.60, Vec3(0.0, 0.75, 1.0), 0.10),
        (4.8, -0.15, -9.3, 0.65, Vec3(0.65, 1.0, 0.1), 0.10),
        (6.2, 1.15, -10.2, 0.75, Vec3(1.0, 0.1, 0.95), 0.12),
    ]

    for x, y, z, r, color, refl in ring_data:
        objects.append(Sphere(Vec3(x, y, z), r, color, refl, 0.0, 1.0))

    # =========================================================
    # Small scattered spheres in the lower middle depth
    # =========================================================

    extra_colors = [
        Vec3(1.0, 0.2, 0.2),
        Vec3(0.2, 1.0, 0.2),
        Vec3(0.2, 0.5, 1.0),
        Vec3(1.0, 0.9, 0.2),
        Vec3(1.0, 0.2, 0.9),
        Vec3(0.2, 1.0, 1.0),
    ]

    scatter_positions = [
        (-6.5, -1.25, -8.0), (-5.8, -1.15, -8.8), (-5.0, -1.05, -9.6),
        (-4.2, -1.2, -10.4), (-3.4, -1.1, -11.2), (-2.6, -1.0, -12.0),
        (2.6, -1.0, -12.0), (3.4, -1.1, -11.2), (4.2, -1.2, -10.4),
        (5.0, -1.05, -9.6), (5.8, -1.15, -8.8), (6.5, -1.25, -8.0),
    ]

    for i, (x, y, z) in enumerate(scatter_positions):
        color = extra_colors[i % len(extra_colors)]
        objects.append(
            Sphere(Vec3(x, y, z), 0.22, color, 0.08, 0.0, 1.0)
        )

    # =========================================================
    # Front row of small spheres
    # =========================================================

    front_data = [
        (-4.5, -1.15, -6.6, 0.45, Vec3(1.0, 0.9, 0.2), 0.10),
        (-3.2, -1.25, -6.2, 0.42, Vec3(0.2, 1.0, 1.0), 0.10),
        (-1.9, -1.3, -6.0, 0.40, Vec3(1.0, 0.3, 0.3), 0.10),
        (-0.6, -1.32, -5.9, 0.38, Vec3(0.3, 0.8, 1.0), 0.10),
        (0.7, -1.3, -6.0, 0.40, Vec3(0.6, 1.0, 0.2), 0.10),
        (2.0, -1.26, -6.2, 0.42, Vec3(1.0, 0.5, 0.1), 0.10),
        (3.3, -1.18, -6.6, 0.45, Vec3(1.0, 0.2, 0.8), 0.10),
    ]

    for x, y, z, r, color, refl in front_data:
        objects.append(Sphere(Vec3(x, y, z), r, color, refl, 0.0, 1.0))

    # =========================================================
    # Additional transparent accent spheres
    # =========================================================

    objects.append(
        Sphere(Vec3(-2.2, 0.15, -5.9), 0.55, Vec3(0.85, 0.95, 1.0), 0.05, 0.75, 1.45)
    )
    objects.append(
        Sphere(Vec3(2.4, 0.1, -6.1), 0.55, Vec3(0.85, 0.95, 1.0), 0.05, 0.75, 1.45)
    )

    # =========================================================
    # Back row of spheres for depth and reflections
    # =========================================================

    back_data = [
        (-7.5, 1.4, -12.0, 0.85, Vec3(0.9, 0.2, 0.2), 0.14),
        (-5.2, 1.9, -12.8, 0.90, Vec3(0.2, 0.9, 0.3), 0.14),
        (-2.8, 2.2, -13.2, 0.95, Vec3(0.2, 0.5, 1.0), 0.16),
        (0.0, 2.35, -13.6, 1.00, Vec3(0.95, 0.9, 0.2), 0.16),
        (2.8, 2.2, -13.2, 0.95, Vec3(1.0, 0.25, 0.9), 0.16),
        (5.2, 1.9, -12.8, 0.90, Vec3(0.3, 1.0, 1.0), 0.14),
        (7.5, 1.4, -12.0, 0.85, Vec3(1.0, 0.55, 0.15), 0.14),
    ]

    for x, y, z, r, color, refl in back_data:
        objects.append(Sphere(Vec3(x, y, z), r, color, refl, 0.0, 1.0))

    # =========================================================
    # Triangles: large background accents
    # =========================================================

    # Large warm triangle behind the left side
    objects.append(
        Triangle(
            Vec3(-6.8, -1.2, -11.5),
            Vec3(-3.2, 2.8, -11.8),
            Vec3(-1.8, -1.4, -10.8),
            Vec3(1.0, 0.55, 0.15),
            reflection=0.08,
            transparency=0.0,
            ior=1.0
        )
    )

    # Large cool triangle behind the right side
    objects.append(
        Triangle(
            Vec3(2.2, -1.3, -11.0),
            Vec3(4.8, 2.7, -12.0),
            Vec3(7.2, -1.1, -11.6),
            Vec3(0.15, 0.7, 1.0),
            reflection=0.08,
            transparency=0.0,
            ior=1.0
        )
    )

    # Central decorative triangle in the far background
    objects.append(
        Triangle(
            Vec3(-1.2, 0.0, -13.8),
            Vec3(1.4, 0.2, -13.6),
            Vec3(0.1, 3.2, -14.2),
            Vec3(0.95, 0.3, 0.85),
            reflection=0.10,
            transparency=0.0,
            ior=1.0
        )
    )

    # =========================================================
    # Small foreground triangle accents
    # =========================================================

    # Left foreground triangle
    objects.append(
        Triangle(
            Vec3(-3.4, -1.45, -5.4),
            Vec3(-2.6, -0.55, -5.6),
            Vec3(-1.9, -1.45, -5.8),
            Vec3(1.0, 0.95, 0.2),
            reflection=0.12,
            transparency=0.0,
            ior=1.0
        )
    )

    # Right foreground triangle
    objects.append(
        Triangle(
            Vec3(2.0, -1.45, -5.6),
            Vec3(2.8, -0.45, -5.7),
            Vec3(3.7, -1.45, -5.5),
            Vec3(0.2, 1.0, 0.95),
            reflection=0.12,
            transparency=0.0,
            ior=1.0
        )
    )

    # Small central triangle below the glass sphere
    objects.append(
        Triangle(
            Vec3(-0.7, -1.35, -5.1),
            Vec3(0.0, -0.35, -5.2),
            Vec3(0.8, -1.35, -5.0),
            Vec3(1.0, 0.35, 0.25),
            reflection=0.15,
            transparency=0.0,
            ior=1.0
        )
    )

    # =========================================================
    # Floor plane
    # =========================================================

    objects.append(
        Plane(Vec3(0, -1.7, 0), Vec3(0, 1, 0), Vec3(0.78, 0.78, 0.82), 0.22)
    )

    return objects, background_color, light_position

    return objects, background_color, light_position
def build_cache_benchmark_scene():
    light_position = Vec3(-8, 8, 4)
    background_color = Vec3(0.05, 0.07, 0.1)

    objects = []

    # Large foreground spheres to maximize ray coherence
    objects.append(Sphere(Vec3(-2.8, 0.0, -7.0), 2.2, Vec3(1.0, 0.2, 0.2), 0.0, 0.0, 1.0))
    objects.append(Sphere(Vec3(0.0, 0.0, -7.5), 2.4, Vec3(0.2, 1.0, 0.2), 0.0, 0.0, 1.0))
    objects.append(Sphere(Vec3(2.8, 0.0, -7.0), 2.2, Vec3(0.2, 0.4, 1.0), 0.0, 0.0, 1.0))

    # Many small background spheres to make full search expensive
    small_colors = [
        Vec3(1.0, 0.9, 0.2),
        Vec3(1.0, 0.4, 0.2),
        Vec3(0.2, 1.0, 1.0),
        Vec3(1.0, 0.2, 0.9),
        Vec3(0.8, 1.0, 0.2),
        Vec3(0.4, 0.8, 1.0),
    ]

    positions = []
    for row in range(5):
        for col in range(10):
            x = -9 + col * 2.0
            y = 3.5 - row * 1.4
            z = -14 - row * 0.8
            positions.append((x, y, z))

    for i, (x, y, z) in enumerate(positions):
        color = small_colors[i % len(small_colors)]
        objects.append(Sphere(Vec3(x, y, z), 0.45, color, 0.0, 0.0, 1.0))

    return objects, background_color, light_position
def build_aabb_benchmark_scene():
    # Strong directional light
    light_position = Vec3(-10, 9, 4)

    # Dark blue background
    background_color = Vec3(0.04, 0.06, 0.10)

    objects = []

    # =========================================================
    # Large foreground spheres
    # These create coherent primary hits in the center.
    # =========================================================
    objects.append(
        Sphere(Vec3(-2.4, 0.2, -7.5), 1.5, Vec3(1.0, 0.2, 0.2), 0.0, 0.0, 1.0)
    )
    objects.append(
        Sphere(Vec3(0.0, 0.0, -8.0), 1.7, Vec3(0.2, 1.0, 0.25), 0.0, 0.0, 1.0)
    )
    objects.append(
        Sphere(Vec3(2.6, 0.15, -7.6), 1.45, Vec3(0.2, 0.45, 1.0), 0.0, 0.0, 1.0)
    )

    # =========================================================
    # Triangle wall in the far background
    # AABB should help here, because many rays will reject many triangles.
    # =========================================================
    triangle_colors = [
        Vec3(1.0, 0.85, 0.15),
        Vec3(1.0, 0.45, 0.20),
        Vec3(0.2, 1.0, 0.9),
        Vec3(0.9, 0.2, 1.0),
        Vec3(0.3, 0.9, 0.25),
        Vec3(0.2, 0.55, 1.0),
    ]

    # Grid of triangles in depth
    idx = 0
    for row in range(6):
        for col in range(10):
            base_x = -10.0 + col * 2.0
            base_y = 3.5 - row * 1.2
            base_z = -14.0 - row * 0.6

            color = triangle_colors[idx % len(triangle_colors)]
            idx += 1

            # Upright triangle
            objects.append(
                Triangle(
                    Vec3(base_x - 0.7, base_y - 0.6, base_z),
                    Vec3(base_x + 0.7, base_y - 0.5, base_z - 0.1),
                    Vec3(base_x,       base_y + 0.9, base_z + 0.1),
                    color,
                    reflection=0.0,
                    transparency=0.0,
                    ior=1.0
                )
            )

    # =========================================================
    # Side triangle groups
    # These are intentionally placed far on the left/right,
    # so many central rays should reject them via AABB.
    # =========================================================
    for i in range(12):
        z = -9.0 - i * 0.8

        # Left side
        objects.append(
            Triangle(
                Vec3(-11.5, -1.4, z),
                Vec3(-9.8,  0.2, z - 0.2),
                Vec3(-10.6, 1.8, z + 0.1),
                Vec3(1.0, 0.8, 0.15),
                reflection=0.0,
                transparency=0.0,
                ior=1.0
            )
        )

        # Right side
        objects.append(
            Triangle(
                Vec3(11.5, -1.3, z),
                Vec3(9.7,   0.1, z - 0.2),
                Vec3(10.5,  1.7, z + 0.2),
                Vec3(0.2, 0.85, 1.0),
                reflection=0.0,
                transparency=0.0,
                ior=1.0
            )
        )

    # =========================================================
    # Small triangle band near the lower background
    # This increases the object count significantly.
    # =========================================================
    for i in range(20):
        x = -9.5 + i * 1.0
        z = -11.0 - (i % 4) * 0.5
        color = triangle_colors[i % len(triangle_colors)]

        objects.append(
            Triangle(
                Vec3(x - 0.35, -1.8, z),
                Vec3(x + 0.35, -1.8, z),
                Vec3(x,        -0.9, z + 0.1),
                color,
                reflection=0.0,
                transparency=0.0,
                ior=1.0
            )
        )

    return objects, background_color, light_position
def build_realistic_benchmark_scene():
    # Main light source
    light_position = Vec3(-16, 14, 8)

    # Dark bluish background
    background_color = Vec3(0.035, 0.05, 0.085)

    objects = []

    # =========================================================
    # Foreground / hero objects
    # =========================================================

    # Central glass sphere
    objects.append(
        Sphere(
            Vec3(0.0, 0.6, -6.2),
            1.45,
            Vec3(0.92, 0.95, 1.0),
            reflection=0.08,
            transparency=0.82,
            ior=1.5
        )
    )

    # Reflective metal spheres in the front
    objects.append(
        Sphere(
            Vec3(-2.2, -0.35, -4.9),
            0.72,
            Vec3(0.9, 0.9, 0.95),
            reflection=0.78,
            transparency=0.0,
            ior=1.0
        )
    )
    objects.append(
        Sphere(
            Vec3(2.3, -0.3, -5.0),
            0.72,
            Vec3(0.9, 0.9, 0.95),
            reflection=0.78,
            transparency=0.0,
            ior=1.0
        )
    )

    # Two colored matte spheres around the center
    objects.append(
        Sphere(
            Vec3(-4.3, 0.5, -8.3),
            1.15,
            Vec3(1.0, 0.18, 0.18),
            reflection=0.12,
            transparency=0.0,
            ior=1.0
        )
    )
    objects.append(
        Sphere(
            Vec3(4.2, 0.55, -8.4),
            1.15,
            Vec3(0.18, 1.0, 0.24),
            reflection=0.12,
            transparency=0.0,
            ior=1.0
        )
    )

    # Deep blue sphere behind the glass
    objects.append(
        Sphere(
            Vec3(0.0, -0.05, -9.7),
            1.28,
            Vec3(0.2, 0.45, 1.0),
            reflection=0.18,
            transparency=0.0,
            ior=1.0
        )
    )

    # =========================================================
    # Additional glass accent spheres
    # =========================================================

    objects.append(
        Sphere(
            Vec3(-2.5, 0.0, -6.2),
            0.55,
            Vec3(0.85, 0.95, 1.0),
            reflection=0.05,
            transparency=0.75,
            ior=1.45
        )
    )
    objects.append(
        Sphere(
            Vec3(2.6, 0.05, -6.3),
            0.55,
            Vec3(0.85, 0.95, 1.0),
            reflection=0.05,
            transparency=0.75,
            ior=1.45
        )
    )

    # =========================================================
    # Mid-depth ring of spheres
    # =========================================================

    ring_data = [
        (-6.2, 1.0, -10.4, 0.72, Vec3(1.0, 0.95, 0.12), 0.10),
        (-4.8, -0.2, -9.7, 0.62, Vec3(1.0, 0.55, 0.06), 0.10),
        (-3.0, -1.0, -8.8, 0.58, Vec3(0.08, 0.95, 0.95), 0.10),
        (-1.0, -1.25, -8.4, 0.56, Vec3(0.85, 0.2, 1.0), 0.12),
        (1.0, -1.2, -8.4, 0.56, Vec3(1.0, 0.38, 0.82), 0.12),
        (3.1, -0.95, -8.9, 0.60, Vec3(0.0, 0.75, 1.0), 0.10),
        (4.9, -0.15, -9.8, 0.64, Vec3(0.65, 1.0, 0.15), 0.10),
        (6.4, 1.0, -10.6, 0.74, Vec3(1.0, 0.12, 0.95), 0.12),
    ]

    for x, y, z, r, color, refl in ring_data:
        objects.append(
            Sphere(Vec3(x, y, z), r, color, refl, 0.0, 1.0)
        )

    # =========================================================
    # Front row of small spheres
    # =========================================================

    front_data = [
        (-4.8, -1.35, -6.8, 0.42, Vec3(1.0, 0.88, 0.18), 0.08),
        (-3.5, -1.42, -6.4, 0.40, Vec3(0.2, 1.0, 1.0), 0.08),
        (-2.1, -1.45, -6.1, 0.38, Vec3(1.0, 0.32, 0.32), 0.08),
        (-0.7, -1.48, -5.95, 0.36, Vec3(0.3, 0.82, 1.0), 0.08),
        (0.8, -1.45, -6.0, 0.38, Vec3(0.6, 1.0, 0.2), 0.08),
        (2.2, -1.4, -6.3, 0.40, Vec3(1.0, 0.52, 0.12), 0.08),
        (3.6, -1.32, -6.8, 0.43, Vec3(1.0, 0.22, 0.82), 0.08),
    ]

    for x, y, z, r, color, refl in front_data:
        objects.append(
            Sphere(Vec3(x, y, z), r, color, refl, 0.0, 1.0)
        )

    # =========================================================
    # Background spheres
    # =========================================================

    back_data = [
        (-8.0, 1.5, -12.5, 0.82, Vec3(0.9, 0.2, 0.2), 0.12),
        (-5.6, 2.0, -13.2, 0.88, Vec3(0.2, 0.9, 0.3), 0.12),
        (-3.0, 2.3, -13.8, 0.93, Vec3(0.2, 0.5, 1.0), 0.14),
        (0.0, 2.45, -14.3, 0.98, Vec3(0.95, 0.9, 0.22), 0.14),
        (3.0, 2.3, -13.8, 0.93, Vec3(1.0, 0.25, 0.9), 0.14),
        (5.6, 2.0, -13.2, 0.88, Vec3(0.3, 1.0, 1.0), 0.12),
        (8.0, 1.5, -12.5, 0.82, Vec3(1.0, 0.55, 0.15), 0.12),
    ]

    for x, y, z, r, color, refl in back_data:
        objects.append(
            Sphere(Vec3(x, y, z), r, color, refl, 0.0, 1.0)
        )

    # =========================================================
    # Large background triangles
    # =========================================================

    objects.append(
        Triangle(
            Vec3(-7.2, -1.4, -12.0),
            Vec3(-3.4, 3.0, -12.2),
            Vec3(-1.8, -1.5, -11.3),
            Vec3(1.0, 0.55, 0.15),
            reflection=0.05,
            transparency=0.0,
            ior=1.0
        )
    )

    objects.append(
        Triangle(
            Vec3(2.0, -1.4, -11.5),
            Vec3(5.0, 2.9, -12.4),
            Vec3(7.6, -1.2, -11.9),
            Vec3(0.15, 0.7, 1.0),
            reflection=0.05,
            transparency=0.0,
            ior=1.0
        )
    )

    objects.append(
        Triangle(
            Vec3(-1.5, 0.0, -14.4),
            Vec3(1.5, 0.2, -14.0),
            Vec3(0.1, 3.5, -14.8),
            Vec3(0.95, 0.28, 0.85),
            reflection=0.08,
            transparency=0.0,
            ior=1.0
        )
    )

    # =========================================================
    # Foreground triangle accents
    # =========================================================

    objects.append(
        Triangle(
            Vec3(-3.8, -1.55, -5.6),
            Vec3(-2.8, -0.45, -5.8),
            Vec3(-1.9, -1.55, -6.0),
            Vec3(1.0, 0.95, 0.2),
            reflection=0.10,
            transparency=0.0,
            ior=1.0
        )
    )

    objects.append(
        Triangle(
            Vec3(1.9, -1.55, -5.8),
            Vec3(2.8, -0.4, -5.9),
            Vec3(3.9, -1.55, -5.7),
            Vec3(0.2, 1.0, 0.95),
            reflection=0.10,
            transparency=0.0,
            ior=1.0
        )
    )

    objects.append(
        Triangle(
            Vec3(-0.8, -1.45, -5.2),
            Vec3(0.0, -0.25, -5.3),
            Vec3(0.9, -1.45, -5.1),
            Vec3(1.0, 0.35, 0.25),
            reflection=0.12,
            transparency=0.0,
            ior=1.0
        )
    )

    # =========================================================
    # Side triangle fields for more realistic complexity
    # =========================================================

    side_colors = [
        Vec3(1.0, 0.85, 0.15),
        Vec3(1.0, 0.45, 0.20),
        Vec3(0.2, 1.0, 0.9),
        Vec3(0.9, 0.2, 1.0),
        Vec3(0.3, 0.9, 0.25),
        Vec3(0.2, 0.55, 1.0),
    ]

    idx = 0
    for i in range(18):
        z = -9.5 - i * 0.8
        color = side_colors[idx % len(side_colors)]
        idx += 1

        # Left side triangles
        objects.append(
            Triangle(
                Vec3(-14.5, -1.8, z),
                Vec3(-12.0,  0.5, z - 0.2),
                Vec3(-13.2,  2.3, z + 0.15),
                color,
                reflection=0.0,
                transparency=0.0,
                ior=1.0
            )
        )

        color = side_colors[idx % len(side_colors)]
        idx += 1

        # Right side triangles
        objects.append(
            Triangle(
                Vec3(14.5, -1.7, z),
                Vec3(12.0,  0.4, z - 0.2),
                Vec3(13.2,  2.2, z + 0.15),
                color,
                reflection=0.0,
                transparency=0.0,
                ior=1.0
            )
        )

    # =========================================================
    # Lower scattered spheres
    # =========================================================

    scatter_colors = [
        Vec3(1.0, 0.2, 0.2),
        Vec3(0.2, 1.0, 0.2),
        Vec3(0.2, 0.5, 1.0),
        Vec3(1.0, 0.9, 0.2),
        Vec3(1.0, 0.2, 0.9),
        Vec3(0.2, 1.0, 1.0),
    ]

    for i in range(24):
        x = -11.0 + i * 0.95
        y = -1.6 + (i % 5) * 0.18
        z = -10.8 - (i % 6) * 0.45
        color = scatter_colors[i % len(scatter_colors)]

        objects.append(
            Sphere(Vec3(x, y, z), 0.23, color, 0.04, 0.0, 1.0)
        )

    # =========================================================
    # Floor plane
    # =========================================================

    objects.append(
        Plane(
            Vec3(0, -2.0, 0),
            Vec3(0, 1, 0),
            Vec3(0.76, 0.76, 0.80),
            reflection=0.18,
            transparency=0.0,
            ior=1.0
        )
    )

    return objects, background_color, light_position

def build_realistic_benchmark_scene():
    # Main light source
    light_position = Vec3(0, 7, 8)

    # Dark bluish background
    background_color = Vec3(0.3, 0.5, 0.3)

    objects = []



    # =========================================================
    # Foreground / hero objects
    # =========================================================

    add_obj_to_scene(
        objects=objects,
        filepath="Sword.obj",
        position=Vec3(0.0, -0.8, -10.0),
        scale=0.5,
        color=Vec3(0.7, 0., 0.7),
        reflection=0.2,
        transparency=0.0,
        ior=1.0
    )

    # Central glass sphere
    objects.append(
        Sphere(
            Vec3(0.0, -2, -6.2),
            0.7,
            Vec3(0.92, 0.95, 1.0),
            reflection=0.08,
            transparency=0.82,
            ior=1.5
        )
    )

    # Reflective metal spheres in the front
    objects.append(
        Sphere(
            Vec3(-2.5, -0.45, -4.8),
            0.75,
            Vec3(0.9, 0.9, 0.95),
            reflection=0.78,
            transparency=0.0,
            ior=1.0
        )
    )
    objects.append(
        Sphere(
            Vec3(2.6, -0.35, -5.0),
            0.72,
            Vec3(0.9, 0.9, 0.95),
            reflection=0.78,
            transparency=0.0,
            ior=1.0
        )
    )

    # Elevated colored side spheres
    objects.append(
        Sphere(
            Vec3(-4.8, 1.4, -8.6),
            1.05,
            Vec3(1.0, 0.18, 0.18),
            reflection=0.12,
            transparency=0.0,
            ior=1.0
        )
    )
    objects.append(
        Sphere(
            Vec3(4.7, 1.2, -8.7),
            1.05,
            Vec3(0.18, 1.0, 0.24),
            reflection=0.12,
            transparency=0.0,
            ior=1.0
        )
    )

    # Deep blue spheres behind the sword
    objects.append(
        Sphere(
            Vec3(-7.0, 10, -17),
            4,
            Vec3(0.2, 0.45, 1.0),
            reflection=0.3,
            transparency=0.0,
            ior=1.0
        )
    )

    objects.append(
        Sphere(
            Vec3(7.0, 10, -17),
            4,
            Vec3(0.2, 0.45, 1.0),
            reflection=0.3,
            transparency=0.0,
            ior=1.0
        )
    )

    # =========================================================
    # Floating transparent accent spheres
    # =========================================================

    objects.append(
        Sphere(
            Vec3(-2.9, 1.8, -6.8),
            0.48,
            Vec3(0.85, 0.95, 1.0),
            reflection=0.05,
            transparency=0.75,
            ior=1.45
        )
    )
    objects.append(
        Sphere(
            Vec3(2.9, 1.6, -6.9),
            0.48,
            Vec3(0.85, 0.95, 1.0),
            reflection=0.05,
            transparency=0.75,
            ior=1.45
        )
    )

    # Lower glass accents
    objects.append(
        Sphere(
            Vec3(-2.3, -0.15, -6.3),
            0.55,
            Vec3(0.85, 0.95, 1.0),
            reflection=0.05,
            transparency=0.75,
            ior=1.45
        )
    )
    objects.append(
        Sphere(
            Vec3(2.4, 0.05, -6.4),
            0.55,
            Vec3(0.85, 0.95, 1.0),
            reflection=0.05,
            transparency=0.75,
            ior=1.45
        )
    )

    # =========================================================
    # Mid-depth spheres with more vertical variation
    # =========================================================

    ring_data = [
        (-6.8, 2.0, -10.8, 0.70, Vec3(1.0, 0.95, 0.12), 0.10),
        (-5.2, 0.5, -9.8, 0.62, Vec3(1.0, 0.55, 0.06), 0.10),
        (-3.4, -1.0, -8.9, 0.58, Vec3(0.08, 0.95, 0.95), 0.10),
        (-1.2, -1.55, -8.3, 0.56, Vec3(0.85, 0.2, 1.0), 0.12),
        (1.2, -1.35, -8.4, 0.56, Vec3(1.0, 0.38, 0.82), 0.12),
        (3.4, -0.7, -9.1, 0.60, Vec3(0.0, 0.75, 1.0), 0.10),
        (5.2, 0.8, -10.0, 0.64, Vec3(0.65, 1.0, 0.15), 0.10),
        (6.8, 2.1, -10.9, 0.72, Vec3(1.0, 0.12, 0.95), 0.12),
    ]

    for x, y, z, r, color, refl in ring_data:
        objects.append(
            Sphere(Vec3(x, y, z), r, color, refl, 0.0, 1.0)
        )

    # =========================================================
    # Front row of small spheres, now less flat
    # =========================================================

    front_data = [
        (-5.2, -1.55, -6.9, 0.42, Vec3(1.0, 0.88, 0.18), 0.08),
        (-3.8, -1.25, -6.3, 0.40, Vec3(0.2, 1.0, 1.0), 0.08),
        (-2.3, -1.6, -6.0, 0.38, Vec3(1.0, 0.32, 0.32), 0.08),
        (-0.8, -1.35, -5.85, 0.36, Vec3(0.3, 0.82, 1.0), 0.08),
        (0.9, -1.5, -6.0, 0.38, Vec3(0.6, 1.0, 0.2), 0.08),
        (2.5, -1.2, -6.25, 0.40, Vec3(1.0, 0.52, 0.12), 0.08),
        (4.2, -1.45, -6.9, 0.43, Vec3(1.0, 0.22, 0.82), 0.08),
    ]

    for x, y, z, r, color, refl in front_data:
        objects.append(
            Sphere(Vec3(x, y, z), r, color, refl, 0.0, 1.0)
        )

    # =========================================================
    # Elevated background spheres
    # =========================================================

    back_data = [
        (-8.5, 2.8, -12.8, 0.82, Vec3(0.9, 0.2, 0.2), 0.12),
        (-6.0, 3.6, -13.6, 0.88, Vec3(0.2, 0.9, 0.3), 0.12),
        (-3.2, 4.1, -14.2, 0.93, Vec3(0.2, 0.5, 1.0), 0.14),
        (0.0, 4.4, -14.8, 1.00, Vec3(0.95, 0.9, 0.22), 0.14),
        (3.2, 4.0, -14.1, 0.93, Vec3(1.0, 0.25, 0.9), 0.14),
        (6.0, 3.5, -13.6, 0.88, Vec3(0.3, 1.0, 1.0), 0.12),
        (8.5, 2.7, -12.8, 0.82, Vec3(1.0, 0.55, 0.15), 0.12),
    ]

    for x, y, z, r, color, refl in back_data:
        objects.append(
            Sphere(Vec3(x, y, z), r, color, refl, 0.0, 1.0)
        )

    # =========================================================
    # Large background triangles with more vertical shape
    # =========================================================

    objects.append(
        Triangle(
            Vec3(-8.2, -1.6, -12.4),
            Vec3(-4.1, 4.3, -12.5),
            Vec3(-1.9, -0.8, -11.4),
            Vec3(1.0, 0.55, 0.15),
            reflection=0.05,
            transparency=0.0,
            ior=1.0
        )
    )

    objects.append(
        Triangle(
            Vec3(1.8, -1.3, -11.8),
            Vec3(5.4, 4.0, -12.8),
            Vec3(8.3, -0.9, -12.1),
            Vec3(0.15, 0.7, 1.0),
            reflection=0.05,
            transparency=0.0,
            ior=1.0
        )
    )

    objects.append(
        Triangle(
            Vec3(-1.8, 0.4, -14.8),
            Vec3(1.8, 0.5, -14.2),
            Vec3(0.1, 5.2, -15.2),
            Vec3(0.95, 0.28, 0.85),
            reflection=0.08,
            transparency=0.0,
            ior=1.0
        )
    )

    # =========================================================
    # Foreground triangle accents
    # =========================================================

    objects.append(
        Triangle(
            Vec3(-4.0, -1.75, -5.8),
            Vec3(-2.9, -0.25, -5.9),
            Vec3(-1.8, -1.65, -6.1),
            Vec3(1.0, 0.95, 0.2),
            reflection=0.10,
            transparency=0.0,
            ior=1.0
        )
    )

    objects.append(
        Triangle(
            Vec3(1.8, -1.75, -5.9),
            Vec3(2.9, -0.2, -6.0),
            Vec3(4.1, -1.7, -5.8),
            Vec3(0.2, 1.0, 0.95),
            reflection=0.10,
            transparency=0.0,
            ior=1.0
        )
    )

    objects.append(
        Triangle(
            Vec3(-0.9, -1.6, -4.2),
            Vec3(0.0, -3, -4.3),
            Vec3(1.0, -1.55, -4.1),
            Vec3(1.0, 0.35, 0.25),
            reflection=0.12,
            transparency=0.0,
            ior=1.0
        )
    )

    # =========================================================
    # Side triangle fields with more height variation
    # =========================================================

    side_colors = [
        Vec3(1.0, 0.85, 0.15),
        Vec3(1.0, 0.45, 0.20),
        Vec3(0.2, 1.0, 0.9),
        Vec3(0.9, 0.2, 1.0),
        Vec3(0.3, 0.9, 0.25),
        Vec3(0.2, 0.55, 1.0),
    ]

    idx = 0
    for i in range(18):
        z = -9.5 - i * 0.8
        y_shift = (i % 4) * 0.7 - 1.0
        color = side_colors[idx % len(side_colors)]
        idx += 1

        # Left side triangles
        objects.append(
            Triangle(
                Vec3(-14.5, -2.0 + y_shift, z),
                Vec3(-12.0,  0.6 + y_shift, z - 0.2),
                Vec3(-13.0,  3.1 + y_shift, z + 0.15),
                color,
                reflection=0.0,
                transparency=0.0,
                ior=1.0
            )
        )

        color = side_colors[idx % len(side_colors)]
        idx += 1

        # Right side triangles
        objects.append(
            Triangle(
                Vec3(14.5, -1.9 + y_shift, z),
                Vec3(12.0,  0.5 + y_shift, z - 0.2),
                Vec3(13.0,  3.0 + y_shift, z + 0.15),
                color,
                reflection=0.0,
                transparency=0.0,
                ior=1.0
            )
        )

    # =========================================================
    # Lower scattered spheres, now more layered in height
    # =========================================================

    scatter_colors = [
        Vec3(1.0, 0.2, 0.2),
        Vec3(0.2, 1.0, 0.2),
        Vec3(0.2, 0.5, 1.0),
        Vec3(1.0, 0.9, 0.2),
        Vec3(1.0, 0.2, 0.9),
        Vec3(0.2, 1.0, 1.0),
    ]

    for i in range(24):
        x = -11.0 + i * 0.95
        y = -2.0 + (i % 6) * 0.35
        z = -10.8 - (i % 6) * 0.45
        color = scatter_colors[i % len(scatter_colors)]

        objects.append(
            Sphere(Vec3(x, y, z), 0.23, color, 0.04, 0.0, 1.0)
        )

    # =========================================================
    # Extra floating background accents
    # =========================================================

    objects.append(
        Sphere(
            Vec3(-6.5, 4.6, -11.5),
            0.42,
            Vec3(1.0, 0.85, 0.2),
            reflection=0.15,
            transparency=0.0,
            ior=1.0
        )
    )
    objects.append(
        Sphere(
            Vec3(6.2, 4.4, -11.7),
            0.42,
            Vec3(0.2, 0.9, 1.0),
            reflection=0.15,
            transparency=0.0,
            ior=1.0
        )
    )
    objects.append(
        Sphere(
            Vec3(0.0, 5.4, -12.8),
            0.36,
            Vec3(0.95, 0.35, 0.9),
            reflection=0.18,
            transparency=0.0,
            ior=1.0
        )
    )

    # =========================================================
    # Floor plane
    # =========================================================

    objects.append(
        Plane(
            Vec3(0, -4, 0),
            Vec3(0, 1, 0),
            Vec3(0.76, 0.76, 0.80),
            reflection=0.18,
            transparency=0.0,
            ior=1.0
        )
    )

    return objects, background_color, light_position
def build_aabb_benchmark_scene():
    # Strong directional light
    light_position = Vec3(-10, 9, 4)

    # Dark blue background
    background_color = Vec3(0.04, 0.06, 0.10)

    objects = []

    # =========================================================
    # Large foreground spheres
    # These create coherent primary hits in the center.
    # =========================================================
    objects.append(
        Sphere(Vec3(-2.4, 0.2, -7.5), 1.5, Vec3(1.0, 0.2, 0.2), 0.0, 0.0, 1.0)
    )
    objects.append(
        Sphere(Vec3(0.0, 0.0, -8.0), 1.7, Vec3(0.2, 1.0, 0.25), 0.0, 0.0, 1.0)
    )
    objects.append(
        Sphere(Vec3(2.6, 0.15, -7.6), 1.45, Vec3(0.2, 0.45, 1.0), 0.0, 0.0, 1.0)
    )

    # =========================================================
    # Triangle wall in the far background
    # AABB should help here, because many rays will reject many triangles.
    # =========================================================
    triangle_colors = [
        Vec3(1.0, 0.85, 0.15),
        Vec3(1.0, 0.45, 0.20),
        Vec3(0.2, 1.0, 0.9),
        Vec3(0.9, 0.2, 1.0),
        Vec3(0.3, 0.9, 0.25),
        Vec3(0.2, 0.55, 1.0),
    ]

    # Grid of triangles in depth
    idx = 0
    for row in range(6):
        for col in range(10):
            base_x = -10.0 + col * 2.0
            base_y = 3.5 - row * 1.2
            base_z = -14.0 - row * 0.6

            color = triangle_colors[idx % len(triangle_colors)]
            idx += 1

            # Upright triangle
            objects.append(
                Triangle(
                    Vec3(base_x - 0.7, base_y - 0.6, base_z),
                    Vec3(base_x + 0.7, base_y - 0.5, base_z - 0.1),
                    Vec3(base_x,       base_y + 0.9, base_z + 0.1),
                    color,
                    reflection=0.0,
                    transparency=0.0,
                    ior=1.0
                )
            )

    # =========================================================
    # Side triangle groups
    # These are intentionally placed far on the left/right,
    # so many central rays should reject them via AABB.
    # =========================================================
    for i in range(12):
        z = -9.0 - i * 0.8

        # Left side
        objects.append(
            Triangle(
                Vec3(-11.5, -1.4, z),
                Vec3(-9.8,  0.2, z - 0.2),
                Vec3(-10.6, 1.8, z + 0.1),
                Vec3(1.0, 0.8, 0.15),
                reflection=0.0,
                transparency=0.0,
                ior=1.0
            )
        )

        # Right side
        objects.append(
            Triangle(
                Vec3(11.5, -1.3, z),
                Vec3(9.7,   0.1, z - 0.2),
                Vec3(10.5,  1.7, z + 0.2),
                Vec3(0.2, 0.85, 1.0),
                reflection=0.0,
                transparency=0.0,
                ior=1.0
            )
        )

    # =========================================================
    # Small triangle band near the lower background
    # This increases the object count significantly.
    # =========================================================
    for i in range(20):
        x = -9.5 + i * 1.0
        z = -11.0 - (i % 4) * 0.5
        color = triangle_colors[i % len(triangle_colors)]

        objects.append(
            Triangle(
                Vec3(x - 0.35, -1.8, z),
                Vec3(x + 0.35, -1.8, z),
                Vec3(x,        -0.9, z + 0.1),
                color,
                reflection=0.0,
                transparency=0.0,
                ior=1.0
            )
        )

    return objects, background_color, light_position
def build_obj_test_scene():
    light_position = Vec3(10, 10, 6)
    background_color = Vec3(0.08, 0.08, 0.10)

    objects = []

    # =========================================================
    # Main OBJ object: sword in the center
    # =========================================================
    add_obj_to_scene(
        objects=objects,
        filepath="casa.obj",
        position=Vec3(-1.2, -1, -3.0),
        scale=0.7,
        color=Vec3(0.75, 0.78, 0.82),
        reflection=0.12,
        transparency=0.0,
        ior=1.0
    )

    return objects, background_color, light_position

def build_showcase_scene_v3():
    light_position = Vec3(-7, 7, 4)
    background_color = Vec3(0.16, 0.18, 0.22)

    objects = []

    # =========================================================
    # CENTER COMPOSITION
    # =========================================================

    # Main pedestal
    add_obj_to_scene(
        objects=objects,
        filepath="pedestal.obj",
        position=Vec3(0.0, -3.0, -4.3),
        scale=0.005,
        color=Vec3(0.72, 0.72, 0.74),
        reflection=0.08,
        transparency=0.0,
        ior=1.0
    )

    # Main sword - dark mirror metal
    add_obj_to_scene(
        objects=objects,
        filepath="greatSword.obj",
        position=Vec3(0.0, -0.3, -4.0),
        scale=0.02,
        color=Vec3(0.50, 0.53, 0.58),
        reflection=0.82,
        transparency=0.0,
        ior=1.0
    )

    # Main arch - mirror stone / polished reflective arch
    add_obj_to_scene(
        objects=objects,
        filepath="arch.obj",
        position=Vec3(0.0, 0.2, -7.0),
        scale=5.0,
        color=Vec3(0.78, 0.80, 0.84),
        reflection=0.88,
        transparency=0.0,
        ior=1.0
    )

    # =========================================================
    # SIDE OBJECTS NEAR THE ARCH
    # =========================================================

    # Left stone pedestal
    add_obj_to_scene(
        objects=objects,
        filepath="stone_pedestal.obj",
        position=Vec3(-3.8, -3.0, -4.5),
        scale=0.01,
        color=Vec3(0.58, 0.58, 0.60),
        reflection=0.06,
        transparency=0.0,
        ior=1.0
    )

    # Right stone pedestal
    add_obj_to_scene(
        objects=objects,
        filepath="stone_pedestal.obj",
        position=Vec3(3.8, -3.0, -4.5),
        scale=0.01,
        color=Vec3(0.58, 0.58, 0.60),
        reflection=0.06,
        transparency=0.0,
        ior=1.0
    )

    # Left urn - polished stone
    add_obj_to_scene(
        objects=objects,
        filepath="NeoUrn.obj",
        position=Vec3(-3.8, -3.0, -6.4),
        scale=0.15,
        color=Vec3(0.66, 0.60, 0.50),
        reflection=0.18,
        transparency=0.0,
        ior=1.0
    )

    # Right brazier - bronze / darker metal
    add_obj_to_scene(
        objects=objects,
        filepath="Brazier.obj",
        position=Vec3(3.8, -3.0, -6.7),
        scale=0.007,
        color=Vec3(0.45, 0.24, 0.10),
        reflection=0.35,
        transparency=0.0,
        ior=1.0
    )

    # =========================================================
    # MAIN CRYSTAL GROUPS AROUND CENTER
    # =========================================================

    # Large cluster left of pedestal - transparent sapphire
    add_obj_to_scene(
        objects=objects,
        filepath="Crystals.obj",
        position=Vec3(-1.0, 0.0, -5.1),
        scale=3,
        color=Vec3(0.16, 0.45, 0.95),
        reflection=0.10,
        transparency=0.65,
        ior=1.45
    )

    # Large cluster right of pedestal - metallic blue crystal
    add_obj_to_scene(
        objects=objects,
        filepath="Crystals.obj",
        position=Vec3(1.0, 0.0, -5.15),
        scale=3,
        color=Vec3(0.10, 0.28, 0.75),
        reflection=0.42,
        transparency=0.0,
        ior=1.0
    )

    # Front-left crystal - transparent sapphire
    add_obj_to_scene(
        objects=objects,
        filepath="crystal_1.obj",
        position=Vec3(-3.8, -2.5, -4.5),
        scale=2,
        color=Vec3(0.18, 0.52, 1.0),
        reflection=0.10,
        transparency=0.60,
        ior=1.42
    )

    # Front-right crystal - metallic sapphire
    add_obj_to_scene(
        objects=objects,
        filepath="crystal_1.obj",
        position=Vec3(3.8, -2.5, -4.5),
        scale=2,
        color=Vec3(0.12, 0.35, 0.88),
        reflection=0.45,
        transparency=0.0,
        ior=1.0
    )

    # Small crystal near left arch base - transparent
    add_obj_to_scene(
        objects=objects,
        filepath="crystal_1.obj",
        position=Vec3(-1.8, -2.95, -5.0),
        scale=3,
        color=Vec3(0.18, 0.56, 1.0),
        reflection=0.08,
        transparency=0.55,
        ior=1.40
    )

    # Small crystal near right arch base - metallic
    add_obj_to_scene(
        objects=objects,
        filepath="crystal_1.obj",
        position=Vec3(1.8, -2.95, -5.0),
        scale=3,
        color=Vec3(0.10, 0.32, 0.82),
        reflection=0.40,
        transparency=0.0,
        ior=1.0
    )

    # Small crystal near right side - transparent
    add_obj_to_scene(
        objects=objects,
        filepath="crystal_1.obj",
        position=Vec3(5.7, -2.95, -6.0),
        scale=4.7,
        color=Vec3(0.18, 0.50, 0.98),
        reflection=0.08,
        transparency=0.58,
        ior=1.40
    )

    # Small crystal near left side - metallic
    add_obj_to_scene(
        objects=objects,
        filepath="crystal_1.obj",
        position=Vec3(-5.7, -2.95, -6.0),
        scale=4.7,
        color=Vec3(0.10, 0.30, 0.76),
        reflection=0.42,
        transparency=0.0,
        ior=1.0
    )

    # =========================================================
    # TREE WALL IN A CURVED BACKGROUND
    # =========================================================

    # Left side tree arc
    add_obj_to_scene(
        objects=objects,
        filepath="tree.obj",
        position=Vec3(-12.0, -3.0, -9.5),
        scale=1.8,
        color=Vec3(0.22, 0.52, 0.24),
        reflection=0.0,
        transparency=0.0,
        ior=1.0
    )
    add_obj_to_scene(
        objects=objects,
        filepath="tree.obj",
        position=Vec3(-10.0, -3.0, -10.5),
        scale=1.9,
        color=Vec3(0.22, 0.54, 0.24),
        reflection=0.0,
        transparency=0.0,
        ior=1.0
    )
    add_obj_to_scene(
        objects=objects,
        filepath="tree.obj",
        position=Vec3(-8.0, -3.0, -11.5),
        scale=1.8,
        color=Vec3(0.24, 0.58, 0.26),
        reflection=0.0,
        transparency=0.0,
        ior=1.0
    )
    add_obj_to_scene(
        objects=objects,
        filepath="tree.obj",
        position=Vec3(-5.8, -3.0, -12.2),
        scale=1.7,
        color=Vec3(0.22, 0.56, 0.24),
        reflection=0.0,
        transparency=0.0,
        ior=1.0
    )

    # Right side tree arc
    add_obj_to_scene(
        objects=objects,
        filepath="tree.obj",
        position=Vec3(12.0, -3.0, -9.5),
        scale=1.8,
        color=Vec3(0.22, 0.52, 0.24),
        reflection=0.0,
        transparency=0.0,
        ior=1.0
    )
    add_obj_to_scene(
        objects=objects,
        filepath="tree.obj",
        position=Vec3(10.0, -3.0, -10.5),
        scale=1.9,
        color=Vec3(0.22, 0.54, 0.24),
        reflection=0.0,
        transparency=0.0,
        ior=1.0
    )
    add_obj_to_scene(
        objects=objects,
        filepath="tree.obj",
        position=Vec3(8.0, -3.0, -11.5),
        scale=1.8,
        color=Vec3(0.24, 0.58, 0.26),
        reflection=0.0,
        transparency=0.0,
        ior=1.0
    )
    add_obj_to_scene(
        objects=objects,
        filepath="tree.obj",
        position=Vec3(5.8, -3.0, -12.2),
        scale=1.7,
        color=Vec3(0.22, 0.56, 0.24),
        reflection=0.0,
        transparency=0.0,
        ior=1.0
    )

    add_obj_to_scene(
        objects=objects,
        filepath="tree.obj",
        position=Vec3(-3.8, -3.0, -12.8),
        scale=1.55,
        color=Vec3(0.22, 0.50, 0.23),
        reflection=0.0,
        transparency=0.0,
        ior=1.0
    )
    add_obj_to_scene(
        objects=objects,
        filepath="tree.obj",
        position=Vec3(3.8, -3.0, -12.8),
        scale=1.55,
        color=Vec3(0.22, 0.50, 0.23),
        reflection=0.0,
        transparency=0.0,
        ior=1.0
    )

    add_obj_to_scene(
        objects=objects,
        filepath="tree.obj",
        position=Vec3(0, -4.0, -13),
        scale=2.5,
        color=Vec3(0.22, 0.50, 0.23),
        reflection=0.0,
        transparency=0.0,
        ior=1.0
    )

    # =========================================================
    # GROUND
    # =========================================================

    objects.append(
        Plane(
            Vec3(0, -3.0, 0),
            Vec3(0, 1, 0),
            Vec3(0.16, 0.40, 0.18),
            reflection=0.12,
            transparency=0.0,
            ior=1.0
        )
    )

    return objects, background_color, light_position
#