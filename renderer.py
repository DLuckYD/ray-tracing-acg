import math
import time
from PIL import Image

import config
from math3d import Vec3
from ray import Ray
from bvh import bvh_intersect, is_shadow_blocked


def find_closest_hit(ray, objects):
    # =====================================================
    # BVH mode
    # =====================================================
    if config.use_bvh:
        bvh_hit_object, bvh_hit_t = bvh_intersect(ray, config.bvh_root)

        extra_hit_object = None
        extra_hit_t = None

        # Test objects that are not inside BVH, for example Plane
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

        # Compare BVH result and non-BVH result
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

    # =====================================================
    # Brute force / AABB mode
    # =====================================================
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

def trace_ray(ray, objects, background_color, light_position , depth, max_depth):
    if depth > max_depth:
        return background_color #stop recursion

    hit_object, t = find_closest_hit(ray, objects)
    if hit_object is not None:
        hit_point = ray.dotOnRayT(t)
        normal = hit_object.normal_at(hit_point)
        #SHADOW RAY PART
        to_light = light_position - hit_point
        distance_to_light = to_light.length()
        direction_light = to_light.normalize()

        epsilon = 0.001
        shadow_origin = hit_point + normal * epsilon

        shadow_ray = Ray(shadow_origin , direction_light)
        blocked = is_shadow_blocked(shadow_ray, objects, distance_to_light)

        if blocked:
            diffuse = 0
        else:
            diffuse = max(0, normal.dot(direction_light))

        #REFLECTED RAY PART
        reflected_direction = (ray.direction - normal * (2 * ray.direction.dot(normal))).normalize()
        reflect_origin = hit_point + normal * epsilon

        reflected_ray = Ray(reflect_origin, reflected_direction)
        reflected_color = trace_ray(reflected_ray,objects,background_color,light_position,depth+1,max_depth)

        # REFRACTED RAY PART
        transparency = hit_object.transparency
        refracted_color = Vec3(0, 0, 0)

        if transparency > 0:
            # Checking: the ray enters or exits the object
            # If dot < 0, the ray enters the object
            # If dot > 0, the ray exits the object
            if ray.direction.dot(normal) < 0:
                refract_normal = normal
                n1 = 1.0
                n2 = hit_object.ior
            else:
                refract_normal = normal * -1
                n1 = hit_object.ior
                n2 = 1.0

            refracted_direction = refract(ray.direction, refract_normal, n1, n2)

            if refracted_direction is not None:
                refract_origin = hit_point - refract_normal * epsilon
                refracted_ray = Ray(refract_origin, refracted_direction)

                refracted_color = trace_ray(
                    refracted_ray,
                    objects,
                    background_color,
                    light_position,
                    depth + 1,
                    max_depth
                )

        #COLOR PART
        ambient_strength = 0.1 #adding some color to black parts of obj
        light_strength = min(1.0, ambient_strength + diffuse)
        local_color = hit_object.color * light_strength
        local_weight = max(0.0, 1.0 - hit_object.reflection - hit_object.transparency)

        final_color = (
                local_color * local_weight
                + reflected_color * hit_object.reflection
                + refracted_color * hit_object.transparency
        )
        return final_color
    else:
        return background_color


def render(width, height, objects, background_color, light_position, depth, max_depth):
    image = Image.new("RGB", (width, height))
    camera_origin = Vec3(0, 0, 0)
    image_plane_z = -1
    aspect_ratio = width / height
    viewport_height = 2.0
    viewport_width = viewport_height * aspect_ratio

    for y in range(height):
        print(f"\rRendering row {y + 1} / {height}", end="", flush=True)

        for x in range(width):
            # Normalize pixel coordinates to [0..1]
            u = (x + 0.5) / width
            v = (y + 0.5) / height

            # Convert [0..1] to image plane coordinates
            screen_x = (u - 0.5) * viewport_width
            screen_y = (0.5 - v) * viewport_height

            # Point on the virtual screen
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

    k = 1 - eta ** 2  * (1- cos_i**2)
    if k < 0:
        return None
    else:
        refracted_ray = direction_norm * eta + normal_norm * (eta * cos_i - math.sqrt(k))
        return refracted_ray.normalize()


def benchmark_render(runs, width, height, objects, background_color, light_position, depth, max_depth):
    times = []

    for i in range(runs):
        print(f"\nStarting run {i + 1} / {runs}")

        config.blocker_cache_object = None

        start_time = time.perf_counter()
        render(width, height, objects, background_color, light_position, depth, max_depth)
        end_time = time.perf_counter()

        elapsed = end_time - start_time
        times.append(elapsed)

        print(f"Run {i + 1} time: {elapsed:.3f} seconds")

    average_time = sum(times) / len(times)

    print("\nBenchmark finished.")
    print("All runs:")
    for i, t in enumerate(times, start=1):
        print(f"  Run {i}: {t:.3f} seconds")

    print(f"\nAverage render time over {runs} runs: {average_time:.3f} seconds")

    return times, average_time