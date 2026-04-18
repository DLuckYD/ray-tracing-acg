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




a = Vec3(1, 2, 3)
b = Vec3(4, 5, 6)

print(a + b)          # ожидаешь что-то вроде Vec3(5, 7, 9)
print(a - b)          # Vec3(-3, -3, -3)
print(a * 2)          # Vec3(2, 4, 6)
print(a / 2)          # Vec3(0.5, 1.0, 1.5)
print(a.dot(b))       # 32
print(a.length())     # sqrt(14)
print(a.normalize())  # единичный вектор

origin = Vec3(0, 0, 0)
direction = Vec3(1, 2, 3)

ray = Ray(origin, direction)

print(ray)
print(ray.dotOnRayT(0))    # Vec3(0, 0, 0)
print(ray.dotOnRayT(1))    # Vec3(1, 2, 3)
print(ray.dotOnRayT(2))    # Vec3(2, 4, 6)
print(ray.dotOnRayT(0.5))  # Vec3(0.5, 1.0, 1.5)

sphere = Sphere(Vec3(0, 0, -5), 1)

ray1 = Ray(Vec3(0, 0, 0), Vec3(0, 0, -1))
ray2 = Ray(Vec3(0, 0, 0), Vec3(0, 1, 0))

print(sphere.intersect(ray1))
print(sphere.intersect(ray2))