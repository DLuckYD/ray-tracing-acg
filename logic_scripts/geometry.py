import math
from logic_scripts.math3d import Vec3
from logic_scripts.aabb import AABB

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