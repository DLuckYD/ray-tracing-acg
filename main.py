import math
import time

from PIL import Image


def main():
    print("Hello")

if __name__ == "__main__":
    main()


class Vec3:

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __add__(self, other):
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, value):
        if isinstance(value, Vec3):
            return Vec3(self.x * value.x, self.y * value.y, self.z * value.z)
        return Vec3(self.x * value, self.y * value, self.z * value)

    def __truediv__(self, value):
        return Vec3(self.x / value, self.y / value, self.z / value)

    def __repr__(self):
        return f"Vec3({self.x}, {self.y}, {self.z})"

    def dot (self, value):
        return self.x * value.x + self.y * value.y + self.z * value.z

    def length(self):
        return math.sqrt(self.dot(self))

    def normalize(self):
        length_vec = self.length()
        if length_vec == 0:
            return Vec3(0.0, 0.0, 0.0);
        return self / length_vec

class Ray:
    def __init__ (self, origin, direction):
        self.origin = origin
        self.direction = direction

    def __repr__(self):
        return f"Ray(origin={self.origin}, direction={self.direction})"

    def dotOnRayT (self, t):
        return self.origin + self.direction * t

class Sphere:
    def __init__(self, center, radius, color, reflection = 0.0, transparency = 0.0, ior = 1.0):
        self.center = center
        self.radius = radius
        self.color = color
        self.reflection = reflection
        self.transparency = transparency
        self.ior = ior #index of refraction

    def intersect(self, ray):

        oc = ray.origin - self.center
        a = ray.direction.dot(ray.direction)
        b = 2 * (oc.dot(ray.direction))
        c = oc.dot(oc) - self.radius ** 2

        discriminant = b ** 2 - 4*a*c

        if discriminant < 0:
            return None


        t1 = (-b - math.sqrt(discriminant)) / (2 * a)
        t2 = (-b + math.sqrt(discriminant)) / (2 * a)

        if (t1 > 0) and (t2 > 0):
            return min(t1, t2)
        elif t1 > 0:
            return t1
        elif t2 > 0:
            return t2
        else:
            return None

    def normal_at(self, hit_point):
        return Vec3((hit_point.x - self.center.x)/self.radius ,(hit_point.y - self.center.y)/self.radius ,(hit_point.z - self.center.z)/self.radius)

class Plane :

    def __init__ (self, point, normal , color, reflection = 0.0, transparency = 0.0, ior = 1.0):
        self.point = point
        self.normal = normal.normalize()
        self.color = color
        self.reflection = reflection
        self.transparency = transparency
        self.ior = ior  # index of refraction

    def intersect(self, ray):
        denom = self.normal.dot(ray.direction)
        if abs(denom) < 0.000001:
            return None
        t = self.normal.dot(((self.point - ray.origin))) / denom
        if t <= 0:
            return None
        return t
    def normal_at(self, hit_point):
        return self.normal



# def find_closest_hit(ray , objects):
#     closest_t = None
#     closest_object = None
#
#     for object in objects:
#         t = object.intersect(ray)
#         if t is None:
#             continue
#
#         if closest_t is None:
#             closest_t = t
#             closest_object = object
#         elif closest_t > t:
#             closest_t = t
#             closest_object = object
#
#     return closest_object , closest_t

def find_closest_hit(ray, objects, cached_object=None):
    closest_t = None
    closest_object = None

    # First test the cached object
    if cached_object is not None:
        t = cached_object.intersect(ray)
        if t is not None:
            closest_t = t
            closest_object = cached_object

    # Then test all other objects
    for obj in objects:
        if obj is cached_object:
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
        shadow_sphere , shadow_t = find_closest_hit(shadow_ray, objects)

        if shadow_t is not None and shadow_t < distance_to_light:
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

    # Cache for the last successfully hit primary object
    last_hit_object = None

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

            # ---------------------------------------------
            # Primary-ray cache test:
            # test the previous hit object first
            # ---------------------------------------------
            primary_hit_object, _ = find_closest_hit(ray, objects, last_hit_object)
            last_hit_object = primary_hit_object

            # Full ray tracing as before
            color = trace_ray(ray, objects, background_color, light_position, depth, max_depth)

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

def build_final_scene():
    light_position = Vec3(-14, 12, 6)
    background_color = Vec3(0.05, 0.08, 0.14)

    objects = []

    # Main central glass sphere
    objects.append(
        Sphere(Vec3(0.0, 0.8, -6.0), 1.5, Vec3(0.92, 0.95, 1.0), 0.08, 0.82, 1.5)
    )

    # Two reflective metallic spheres near the front
    objects.append(
        Sphere(Vec3(-1.8, -0.4, -4.8), 0.7, Vec3(0.9, 0.9, 0.95), 0.75, 0.0, 1.0)
    )
    objects.append(
        Sphere(Vec3(1.8, -0.35, -5.0), 0.7, Vec3(0.9, 0.9, 0.95), 0.75, 0.0, 1.0)
    )

    # Large colored spheres around the center
    objects.append(
        Sphere(Vec3(-3.8, 0.7, -8.0), 1.15, Vec3(1.0, 0.15, 0.15), 0.18, 0.0, 1.0)
    )
    objects.append(
        Sphere(Vec3(3.9, 0.6, -8.2), 1.15, Vec3(0.15, 1.0, 0.2), 0.18, 0.0, 1.0)
    )
    objects.append(
        Sphere(Vec3(0.0, -0.1, -9.5), 1.25, Vec3(0.2, 0.45, 1.0), 0.22, 0.0, 1.0)
    )

    # Medium ring of spheres
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

    for x, y, z, r, color, refl in ring_data:
        objects.append(Sphere(Vec3(x, y, z), r, color, refl, 0.0, 1.0))

    # Front row of small spheres
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

    # Additional transparent accent spheres
    objects.append(
        Sphere(Vec3(-2.2, 0.15, -5.9), 0.55, Vec3(0.85, 0.95, 1.0), 0.05, 0.75, 1.45)
    )
    objects.append(
        Sphere(Vec3(2.4, 0.1, -6.1), 0.55, Vec3(0.85, 0.95, 1.0), 0.05, 0.75, 1.45)
    )

    # Back row for more reflections/refractions
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

    # Floor plane
    objects.append(
        Plane(Vec3(0, -1.7, 0), Vec3(0, 1, 0), Vec3(0.78, 0.78, 0.82), 0.22)
    )

    return objects, background_color, light_position

objects, background_color, light_position = build_final_scene()

start_time = time.perf_counter()
render(1000, 1000, objects, background_color, light_position, 0, 4)
end_time = time.perf_counter()

print(f"Render time: {end_time - start_time:.3f} seconds")
im = Image.open("render.png")
im.show("Render")



