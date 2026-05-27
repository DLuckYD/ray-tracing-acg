from math3d import Vec3

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