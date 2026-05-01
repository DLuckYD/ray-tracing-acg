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

    def cross(self, other): #vec multiplication
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )


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
        radius_vec = Vec3(self.radius, self.radius, self.radius)
        self.aabb = AABB(self.center - radius_vec, self.center + radius_vec)

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

    def get_aabb(self):
        return self.aabb



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

    def get_aabb(self):
        return None

class Triangle:

    def __init__(self, v0 ,v1 , v2, color, reflection = 0.0, transparency = 0.0, ior = 1.0):
        self.v0 = v0
        self.v1 = v1
        self.v2 = v2
        self.color = color
        self.reflection = reflection
        self. transparency = transparency
        self.ior = ior  # index of refraction
        self.aabb = self.create_aabb()

    def normal_at(self, hit_point):
        edge1 = self.v1 - self.v0
        edge2 = self.v2 - self.v0
        return edge1.cross(edge2).normalize()

    def intersect(self, ray):
        epsilon = 0.000001

        edge1 = self.v1 - self.v0
        edge2 = self.v2 - self.v0

        pvec = ray.direction.cross(edge2)
        det = edge1.dot(pvec)

        if abs(det) < epsilon:
            return None

        inv_det = 1.0 / det
        tvec = ray.origin - self.v0

        u = tvec.dot(pvec) * inv_det
        if u < 0.0 or u > 1.0:
            return None

        qvec = tvec.cross(edge1)

        v = ray.direction.dot(qvec) * inv_det
        if v < 0.0 or (u + v) > 1.0:
            return None

        t = edge2.dot(qvec) * inv_det

        if t > epsilon:
            return t

        return None

    def create_aabb(self):
        epsilon = 0.000001
        min_x = min(self.v0.x, self.v1.x, self.v2.x) - epsilon
        min_y = min(self.v0.y, self.v1.y, self.v2.y) - epsilon
        min_z = min(self.v0.z, self.v1.z, self.v2.z) - epsilon

        max_x = max(self.v0.x, self.v1.x, self.v2.x) + epsilon
        max_y = max(self.v0.y, self.v1.y, self.v2.y) + epsilon
        max_z = max(self.v0.z, self.v1.z, self.v2.z) + epsilon

        min_point = Vec3(min_x, min_y, min_z)
        max_point = Vec3(max_x, max_y, max_z)

        return AABB(min_point, max_point)

    def get_aabb(self):
        return self.aabb


def find_closest_hit(ray, objects):
    global use_aabb
    global use_bvh
    global bvh_root
    global non_bvh_objects

    # =====================================================
    # BVH mode
    # =====================================================
    if use_bvh:
        bvh_hit_object, bvh_hit_t = bvh_intersect(ray, bvh_root)

        extra_hit_object = None
        extra_hit_t = None

        # Test objects that are not inside BVH, for example Plane
        for obj in non_bvh_objects:
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
        if use_aabb:
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
        global blocker_cache_object
        blocker_cache_object = None

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



def is_shadow_blocked(shadow_ray, objects, distance_to_light):
    global blocker_cache_object

    # 1. First test the object stored in the blocker cache
    if blocker_cache_object is not None:
        t = blocker_cache_object.intersect(shadow_ray)

        if t is not None and t < distance_to_light:
            return True

    # 2. If the cached object did not block the light,
    #    test all other objects
    for obj in objects:
        if obj is blocker_cache_object:
            continue

        t = obj.intersect(shadow_ray)

        if t is not None and t < distance_to_light:
            blocker_cache_object = obj
            return True

    # 3. Nothing blocks the light
    return False

class AABB:
    def __init__(self, min_point, max_point):
        self.min_point = min_point
        self.max_point = max_point

    def intersect(self, ray):
        # Small epsilon to avoid division issues when direction is very close to zero
        epsilon = 0.000001

        # ---------------------------------------------------------
        # X slab
        # ---------------------------------------------------------
        # If the ray is almost parallel to the X planes,
        # then it can hit the box only if its origin.x is already inside the slab.
        if abs(ray.direction.x) < epsilon:
            if ray.origin.x < self.min_point.x or ray.origin.x > self.max_point.x:
                return False
            tx_min = -float("inf")
            tx_max = float("inf")
        else:
            tx1 = (self.min_point.x - ray.origin.x) / ray.direction.x
            tx2 = (self.max_point.x - ray.origin.x) / ray.direction.x

            # tx_min is the entry distance for X, tx_max is the exit distance
            tx_min = min(tx1, tx2)
            tx_max = max(tx1, tx2)

        # ---------------------------------------------------------
        # Y slab
        # ---------------------------------------------------------
        if abs(ray.direction.y) < epsilon:
            if ray.origin.y < self.min_point.y or ray.origin.y > self.max_point.y:
                return False
            ty_min = -float("inf")
            ty_max = float("inf")
        else:
            ty1 = (self.min_point.y - ray.origin.y) / ray.direction.y
            ty2 = (self.max_point.y - ray.origin.y) / ray.direction.y

            ty_min = min(ty1, ty2)
            ty_max = max(ty1, ty2)

        # ---------------------------------------------------------
        # Z slab
        # ---------------------------------------------------------
        if abs(ray.direction.z) < epsilon:
            if ray.origin.z < self.min_point.z or ray.origin.z > self.max_point.z:
                return False
            tz_min = -float("inf")
            tz_max = float("inf")
        else:
            tz1 = (self.min_point.z - ray.origin.z) / ray.direction.z
            tz2 = (self.max_point.z - ray.origin.z) / ray.direction.z

            tz_min = min(tz1, tz2)
            tz_max = max(tz1, tz2)

        # ---------------------------------------------------------
        # Combine intervals from X, Y, Z
        # ---------------------------------------------------------
        # The ray must be inside all three slab intervals at the same time.
        t_enter = max(tx_min, ty_min, tz_min)
        t_exit = min(tx_max, ty_max, tz_max)

        # If entry is after exit, intervals do not overlap -> no hit
        if t_enter > t_exit:
            return False

        # If the whole box is behind the ray origin, we also reject it
        if t_exit < 0:
            return False

        return True



def merge_aabb(aabb1, aabb2):
    min_x = min(aabb1.min_point.x, aabb2.min_point.x)
    min_y = min(aabb1.min_point.y, aabb2.min_point.y)
    min_z = min(aabb1.min_point.z, aabb2.min_point.z)

    max_x = max(aabb1.max_point.x, aabb2.max_point.x)
    max_y = max(aabb1.max_point.y, aabb2.max_point.y)
    max_z = max(aabb1.max_point.z, aabb2.max_point.z)

    min_point = Vec3(min_x, min_y, min_z)
    max_point = Vec3(max_x, max_y, max_z)

    return AABB(min_point, max_point)

def compute_objects_aabb(objects):
    scene_aabb = None

    for obj in objects:
        obj_aabb = obj.get_aabb()

        # Skip objects without finite AABB, for example Plane
        if obj_aabb is None:
            continue

        if scene_aabb is None:
            scene_aabb = obj_aabb
        else:
            scene_aabb = merge_aabb(scene_aabb, obj_aabb)

    return scene_aabb

class BVHNode():
    def __init__(self, aabb, left=None, right=None, objects=None, is_leaf=False):
        self.aabb = aabb
        self.left = left
        self.right = right
        self.objects = objects
        self.is_leaf = is_leaf

def build_bvh(objects):
    # Remove objects without finite AABB
    valid_objects = []
    for obj in objects:
        if obj.get_aabb() is not None:
            valid_objects.append(obj)

    # Safety check
    if len(valid_objects) == 0:
        return None

    # Compute bounding box for the whole node
    node_aabb = compute_objects_aabb(valid_objects)

    # Leaf criterion
    if len(valid_objects) <= 2:
        return BVHNode(
            aabb=node_aabb,
            left=None,
            right=None,
            objects=valid_objects,
            is_leaf=True
        )

    # Choose split axis based on node AABB extent
    axis = get_largest_axis(node_aabb)

    # Sort objects by AABB center along the chosen axis
    if axis == 0:
        valid_objects.sort(key=lambda obj: get_aabb_center(obj).x)
    elif axis == 1:
        valid_objects.sort(key=lambda obj: get_aabb_center(obj).y)
    else:
        valid_objects.sort(key=lambda obj: get_aabb_center(obj).z)

    # Split in the middle
    mid = len(valid_objects) // 2
    left_objects = valid_objects[:mid]
    right_objects = valid_objects[mid:]

    # Build children recursively
    left_node = build_bvh(left_objects)
    right_node = build_bvh(right_objects)

    # Create inner node
    return BVHNode(
        aabb=node_aabb,
        left=left_node,
        right=right_node,
        objects=None,
        is_leaf=False
    )

def get_aabb_center(obj):
    aabb = obj.get_aabb()

    center_x = (aabb.min_point.x + aabb.max_point.x) * 0.5
    center_y = (aabb.min_point.y + aabb.max_point.y) * 0.5
    center_z = (aabb.min_point.z + aabb.max_point.z) * 0.5

    return Vec3(center_x, center_y, center_z)

def get_largest_axis(aabb):
    size_x = aabb.max_point.x - aabb.min_point.x
    size_y = aabb.max_point.y - aabb.min_point.y
    size_z = aabb.max_point.z - aabb.min_point.z

    if size_x >= size_y and size_x >= size_z:
        return 0
    elif size_y >= size_x and size_y >= size_z:
        return 1
    else:
        return 2

def bvh_intersect(ray, node):
    # Safety check
    if node is None:
        return None, None

    # If the ray does not hit the node bounding box,
    # nothing inside this node can be hit
    if not node.aabb.intersect(ray):
        return None, None

    # -------------------------------------------------
    # Leaf node: test all objects stored in the leaf
    # -------------------------------------------------
    if node.is_leaf:
        hit_object = None
        hit_t = None

        for obj in node.objects:
            t = obj.intersect(ray)
            if t is None:
                continue

            if hit_t is None:
                hit_t = t
                hit_object = obj
            elif t < hit_t:
                hit_t = t
                hit_object = obj

        return hit_object, hit_t

    # -------------------------------------------------
    # Inner node: recurse into both children
    # -------------------------------------------------
    left_object, left_t = bvh_intersect(ray, node.left)
    right_object, right_t = bvh_intersect(ray, node.right)

    # If only left child has a hit
    if left_t is not None and right_t is None:
        return left_object, left_t

    # If only right child has a hit
    if right_t is not None and left_t is None:
        return right_object, right_t

    # If both children have hits, choose the nearer one
    if left_t is not None and right_t is not None:
        if left_t < right_t:
            return left_object, left_t
        else:
            return right_object, right_t

    # No hit in either child
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


def build_realistic_benchmark_scene():
    # Main light source
    light_position = Vec3(-16, 14, 8)

    # Dark bluish background
    background_color = Vec3(0.3, 0.5, 0.3)

    objects = []

    # =========================================================
    # Foreground / hero objects
    # =========================================================

    # Central glass sphere
    objects.append(
        Sphere(
            Vec3(0.0, 0.8, -6.2),
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

    # Deep blue sphere behind the glass
    objects.append(
        Sphere(
            Vec3(0.0, -0.1, -9.9),
            1.3,
            Vec3(0.2, 0.45, 1.0),
            reflection=0.18,
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
            Vec3(-0.9, -1.6, -5.2),
            Vec3(0.0, 0.1, -5.3),
            Vec3(1.0, -1.55, -5.1),
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
            Vec3(0, -2.1, 0),
            Vec3(0, 1, 0),
            Vec3(0.76, 0.76, 0.80),
            reflection=0.18,
            transparency=0.0,
            ior=1.0
        )
    )

    return objects, background_color, light_position

# Global feature flags
use_aabb = True
blocker_cache_object = None
use_bvh = True
bvh_root = None



objects, background_color, light_position = build_realistic_benchmark_scene()

bvh_objects, non_bvh_objects = split_bvh_objects(objects)

if use_bvh:
    bvh_root = build_bvh(bvh_objects)
else:
    bvh_root = None



times, average_time = benchmark_render(
    runs=1,
    width=200,
    height=300,
    objects=objects,
    background_color=background_color,
    light_position=light_position,
    depth=0,
    max_depth=4
)





im = Image.open("render.png")
im.show("Render")


