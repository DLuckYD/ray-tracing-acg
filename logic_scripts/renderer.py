import math
import time
from PIL import Image

import logic_scripts.config
from logic_scripts.math3d import Vec3
from logic_scripts.ray import Ray
from logic_scripts.bvh import bvh_intersect, is_shadow_blocked
from triangle_logic.triangle_hit import make_triangle_hit_record, hit_record_normal_components
from triangle_logic.triangle_bvh import triangle_bvh_intersect, triangle_bvh_shadow_blocked

config = logic_scripts.config

def find_closest_hit_triangle_bvh(ray, objects):
    closest_t = None
    closest_hit_record = None

    triangle_data = config.triangle_data
    triangle_bvh = config.triangle_bvh_root

    if triangle_data is None or triangle_bvh is None:
        return None, None

    triangle_index, triangle_t = triangle_bvh_intersect(ray, triangle_bvh, triangle_data)

    if triangle_t is not None:
        closest_t = triangle_t
        closest_hit_record = make_triangle_hit_record(triangle_data, triangle_index)

    for obj in triangle_data["non_triangle_objects"]:
        if config.use_aabb:
            aabb = obj.get_aabb()
            if aabb is not None and not aabb.intersect(ray):
                continue

        t = obj.intersect(ray)
        if t is None:
            continue

        if closest_t is None or t < closest_t:
            closest_t = t
            closest_hit_record = {
                "type": "object",
                "object": obj,
                "reflection": obj.reflection,
                "transparency": obj.transparency,
                "ior": obj.ior,
            }

    return closest_hit_record, closest_t


def is_shadow_blocked_triangle_backend(shadow_ray, distance_to_light):
    triangle_data = config.triangle_data
    triangle_bvh = config.triangle_bvh_root

    if triangle_data is None or triangle_bvh is None:
        return False

    if triangle_bvh_shadow_blocked(shadow_ray, distance_to_light, triangle_bvh, triangle_data):
        return True

    for obj in triangle_data["non_triangle_objects"]:
        t = obj.intersect(shadow_ray)
        if t is not None and t < distance_to_light:
            return True

    return False


def find_closest_hit(ray, objects):
    if config.use_triangle_backend:
        return find_closest_hit_triangle_bvh(ray, objects)

    if config.use_bvh:
        bvh_hit_object, bvh_hit_t = bvh_intersect(ray, config.bvh_root)

        extra_hit_object = None
        extra_hit_t = None

        for obj in config.non_bvh_objects:
            t = obj.intersect(ray)
            if t is None:
                continue

            if extra_hit_t is None:
                extra_hit_t = t
                extra_hit_object = obj
            elif t < extra_hit_t:
                extra_hit_t = t
                extra_hit_object = obj

        if bvh_hit_t is not None and extra_hit_t is None:
            return bvh_hit_object, bvh_hit_t

        if extra_hit_t is not None and bvh_hit_t is None:
            return extra_hit_object, extra_hit_t

        if bvh_hit_t is not None and extra_hit_t is not None:
            if bvh_hit_t < extra_hit_t:
                return bvh_hit_object, bvh_hit_t
            else:
                return extra_hit_object, extra_hit_t

        return None, None

    closest_t = None
    closest_object = None

    for obj in objects:
        if config.use_aabb:
            aabb = obj.get_aabb()
            if aabb is not None and not aabb.intersect(ray):
                continue

        t = obj.intersect(ray)
        if t is None:
            continue

        if closest_t is None:
            closest_t = t
            closest_object = obj
        elif t < closest_t:
            closest_t = t
            closest_object = obj

    return closest_object, closest_t


def trace_ray(ray, objects, background_color, light_position, depth, max_depth):
    if depth > max_depth:
        return background_color

    hit_record, t = find_closest_hit(ray, objects)
    if hit_record is None:
        return background_color

    hit_point = ray.dotOnRayT(t)

    if config.use_triangle_backend and hit_record["type"] == "triangle":
        nx, ny, nz = hit_record_normal_components(hit_record, config.triangle_data)

        surface_color_r = hit_record["color_r"]
        surface_color_g = hit_record["color_g"]
        surface_color_b = hit_record["color_b"]
        surface_reflection = hit_record["reflection"]
        surface_transparency = hit_record["transparency"]
        surface_ior = hit_record["ior"]
    else:
        obj = hit_record if not isinstance(hit_record, dict) else hit_record["object"]
        normal = obj.normal_at(hit_point)

        nx = normal.x
        ny = normal.y
        nz = normal.z

        surface_color_r = obj.color.x
        surface_color_g = obj.color.y
        surface_color_b = obj.color.z
        surface_reflection = obj.reflection
        surface_transparency = obj.transparency
        surface_ior = obj.ior

    hp_x = hit_point.x
    hp_y = hit_point.y
    hp_z = hit_point.z

    to_light_x = light_position.x - hp_x
    to_light_y = light_position.y - hp_y
    to_light_z = light_position.z - hp_z

    distance_to_light = (to_light_x * to_light_x + to_light_y * to_light_y + to_light_z * to_light_z) ** 0.5
    if distance_to_light == 0.0:
        direction_light_x = 0.0
        direction_light_y = 0.0
        direction_light_z = 0.0
    else:
        inv_light_len = 1.0 / distance_to_light
        direction_light_x = to_light_x * inv_light_len
        direction_light_y = to_light_y * inv_light_len
        direction_light_z = to_light_z * inv_light_len

    epsilon = 0.001
    shadow_origin = Vec3(
        hp_x + nx * epsilon,
        hp_y + ny * epsilon,
        hp_z + nz * epsilon
    )

    shadow_ray = Ray(shadow_origin, Vec3(direction_light_x, direction_light_y, direction_light_z))

    if config.use_triangle_backend:
        blocked = is_shadow_blocked_triangle_backend(shadow_ray, distance_to_light)
    else:
        blocked = is_shadow_blocked(shadow_ray, objects, distance_to_light)

    if blocked:
        diffuse = 0.0
    else:
        diffuse = nx * direction_light_x + ny * direction_light_y + nz * direction_light_z
        if diffuse < 0.0:
            diffuse = 0.0

    ambient_strength = 0.1
    light_strength = ambient_strength + diffuse
    if light_strength > 1.0:
        light_strength = 1.0

    local_color = Vec3(
        surface_color_r * light_strength,
        surface_color_g * light_strength,
        surface_color_b * light_strength
    )

    if surface_reflection <= 0.0 and surface_transparency <= 0.0:
        return local_color

    if surface_transparency <= 0.0:
        dot_dn = ray.direction.x * nx + ray.direction.y * ny + ray.direction.z * nz

        reflected_direction = Vec3(
            ray.direction.x - nx * (2.0 * dot_dn),
            ray.direction.y - ny * (2.0 * dot_dn),
            ray.direction.z - nz * (2.0 * dot_dn)
        ).normalize()

        reflect_origin = Vec3(
            hp_x + nx * epsilon,
            hp_y + ny * epsilon,
            hp_z + nz * epsilon
        )

        reflected_ray = Ray(reflect_origin, reflected_direction)
        reflected_color = trace_ray(
            reflected_ray,
            objects,
            background_color,
            light_position,
            depth + 1,
            max_depth
        )

        local_weight = 1.0 - surface_reflection
        if local_weight < 0.0:
            local_weight = 0.0

        return local_color * local_weight + reflected_color * surface_reflection

    dot_dn = ray.direction.x * nx + ray.direction.y * ny + ray.direction.z * nz

    reflected_direction = Vec3(
        ray.direction.x - nx * (2.0 * dot_dn),
        ray.direction.y - ny * (2.0 * dot_dn),
        ray.direction.z - nz * (2.0 * dot_dn)
    ).normalize()

    reflect_origin = Vec3(
        hp_x + nx * epsilon,
        hp_y + ny * epsilon,
        hp_z + nz * epsilon
    )

    reflected_ray = Ray(reflect_origin, reflected_direction)
    reflected_color = trace_ray(
        reflected_ray,
        objects,
        background_color,
        light_position,
        depth + 1,
        max_depth
    )

    refracted_color = Vec3(0, 0, 0)

    if dot_dn < 0:
        refract_normal = Vec3(nx, ny, nz)
        n1 = 1.0
        n2 = surface_ior
    else:
        refract_normal = Vec3(-nx, -ny, -nz)
        n1 = surface_ior
        n2 = 1.0

    refracted_direction = refract(ray.direction, refract_normal, n1, n2)

    if refracted_direction is not None:
        refract_origin = Vec3(
            hp_x - refract_normal.x * epsilon,
            hp_y - refract_normal.y * epsilon,
            hp_z - refract_normal.z * epsilon
        )
        refracted_ray = Ray(refract_origin, refracted_direction)

        refracted_color = trace_ray(
            refracted_ray,
            objects,
            background_color,
            light_position,
            depth + 1,
            max_depth
        )

    local_weight = 1.0 - surface_reflection - surface_transparency
    if local_weight < 0.0:
        local_weight = 0.0

    final_color = (
        local_color * local_weight
        + reflected_color * surface_reflection
        + refracted_color * surface_transparency
    )
    return final_color


def render(width, height, objects, background_color, light_position, depth, max_depth):
    image = Image.new("RGB", (width, height))
    camera_origin = Vec3(0, 0, 0)
    image_plane_z = -1
    aspect_ratio = width / height
    viewport_height = 2.0
    viewport_width = viewport_height * aspect_ratio

    for y in range(height):
        print(f"\\rRendering row {y + 1} / {height}", end="", flush=True)

        for x in range(width):
            u = (x + 0.5) / width
            v = (y + 0.5) / height

            screen_x = (u - 0.5) * viewport_width
            screen_y = (0.5 - v) * viewport_height

            pixel_pos = Vec3(screen_x, screen_y, image_plane_z)
            direction = (pixel_pos - camera_origin).normalize()

            ray = Ray(camera_origin, direction)

            color = trace_ray(
                ray,
                objects,
                background_color,
                light_position,
                depth,
                max_depth
            )

            r = int(max(0, min(255, color.x * 255)))
            g = int(max(0, min(255, color.y * 255)))
            b = int(max(0, min(255, color.z * 255)))

            image.putpixel((x, y), (r, g, b))

    image.save("render.png")
    print()
    print("Render finished: render.png")

    return image


def refract(direction, normal, n1, n2):
    direction_norm = direction.normalize()
    normal_norm = normal.normalize()

    eta = n1 / n2
    cos_i = -normal_norm.dot(direction_norm)

    k = 1 - eta ** 2 * (1 - cos_i ** 2)
    if k < 0:
        return None
    else:
        refracted_ray = direction_norm * eta + normal_norm * (eta * cos_i - math.sqrt(k))
        return refracted_ray.normalize()


def benchmark_render(runs, width, height, objects, background_color, light_position, depth, max_depth):
    times = []

    for i in range(runs):
        print(f"\\nStarting run {i + 1} / {runs}")

        config.blocker_cache_object = None

        start_time = time.perf_counter()
        render(width, height, objects, background_color, light_position, depth, max_depth)
        end_time = time.perf_counter()

        elapsed = end_time - start_time
        times.append(elapsed)

        print(f"Run {i + 1} time: {elapsed:.3f} seconds")

    average_time = sum(times) / len(times)

    print("\\nBenchmark finished.")
    print("All runs:")
    for i, t in enumerate(times, start=1):
        print(f"  Run {i}: {t:.3f} seconds")

    print(f"\\nAverage render time over {runs} runs: {average_time:.3f} seconds")

    return times, average_time