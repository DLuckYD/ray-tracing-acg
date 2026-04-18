import math
from random import random, randrange
import array
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
    def __init__(self, center, radius):
        self.center = center
        self.radius = radius

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

    def normal_dotOnRayT(self, hit_point):
        return Vec3((hit_point.x - self.center.x)/self.radius ,(hit_point.y - self.center.y)/self.radius ,(hit_point.z - self.center.z)/self.radius)


def find_closest_hit(ray , spheres):
    closest_t = None
    closest_sphere = None

    for sphere in spheres:
        t = sphere.intersect(ray)
        if t is None:
            continue

        if  closest_t == None:
            closest_t = t
            closest_sphere = sphere
        elif closest_t > t:
            closest_t = t
            closest_sphere = sphere

    return closest_sphere , closest_t

sphere1 = Sphere(Vec3(0, 0, -5), 1)
sphere2 = Sphere(Vec3(0, 0, -8), 1)

spheres = [sphere1, sphere2]

ray = Ray(Vec3(0, 0, 0), Vec3(0, 0, -1))
hit_sphere, t = find_closest_hit(ray, spheres)
if t != None:
    hit_point = ray.dotOnRayT(t)
    print("Hit point",hit_point)
if(hit_sphere != None):
    normal = hit_sphere.normal_dotOnRayT(hit_point)
    print("closest t =", t)
    print("closest sphere center =", hit_sphere.center if hit_sphere else None)
    print("normal =",normal)
else:
    print("No hit")
