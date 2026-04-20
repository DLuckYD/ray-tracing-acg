import math

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
    def __init__(self, center, radius, color, reflection):
        self.center = center
        self.radius = radius
        self.color = color
        self.reflection = reflection

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

    def __init__ (self, point, normal , color, reflection):
        self.point = point
        self.normal = normal.normalize()
        self.color = color
        self.reflection = reflection

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



def find_closest_hit(ray , objects):
    closest_t = None
    closest_object = None

    for object in objects:
        t = object.intersect(ray)
        if t is None:
            continue

        if closest_t is None:
            closest_t = t
            closest_object = object
        elif closest_t > t:
            closest_t = t
            closest_object = object

    return closest_object , closest_t


# def trace_ray(ray, spheres, background_color, light_position):
#     hit_sphere, t = find_closest_hit(ray, spheres)
#     if hit_sphere is not None:
#         hit_point = ray.dotOnRayT(t)
#         normal = hit_sphere.normal_dotOnRayT(hit_point)
#         to_light = light_position - hit_point
#         distance_to_light = to_light.length()
#         direction_light = to_light.normalize()
#
#         epsilon = 0.001
#         shadow_origin = hit_point + normal * epsilon
#
#         shadow_ray = Ray(shadow_origin , direction_light)
#         shadow_sphere , shadow_t = find_closest_hit(shadow_ray, spheres)
#
#         if shadow_t is not None and shadow_t < distance_to_light:
#                 diffuse = 0
#         else:
#             diffuse = max(0, normal.dot(direction_light))
#
#         ambient_strength = 0.1 #adding some color to black parts of obj
#         light_strength = min(1.0, ambient_strength + diffuse)
#         color = hit_sphere.color * light_strength
#
#         return color
#     else:
#         return background_color

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


        #COLOR PART
        ambient_strength = 0.1 #adding some color to black parts of obj
        light_strength = min(1.0, ambient_strength + diffuse)
        local_color = hit_object.color * light_strength
        final_color = local_color * (1- hit_object.reflection) + reflected_color * hit_object.reflection
        return final_color
    else:
        return background_color

def render(width, height, objects, background_color, light_position, depth, max_depth):
    image = Image.new("RGB", (width,height))
    camera_origin = Vec3(0, 0, 0)
    image_plane_z = -1
    aspect_ratio = width / height
    viewport_height = 2.0
    viewport_width = viewport_height * aspect_ratio

    for y in range(height):
        print(f"\rRendering row {y + 1} / {height}", end="", flush=True)
        for x in range(width): #normalize pixels to [0..1]
            u = (x + 0.5) / width
            v = (y + 0.5) / height

            screen_x = (u - 0.5) * viewport_width # convert [0..1] to virtual screen
            screen_y = (0.5 - v) * viewport_height

            pixel_pos = Vec3(screen_x, screen_y, image_plane_z) # pixel on virt screen
            direction = (pixel_pos - camera_origin).normalize()

            ray = Ray(camera_origin, direction)
            color = trace_ray(ray, objects, background_color, light_position, depth, max_depth)

            r = int(max(0, min(255, color.x * 255))) #make separate function
            g = int(max(0, min(255, color.y * 255)))
            b = int(max(0, min(255, color.z * 255)))

            image.putpixel((x,y), (r, g, b))



    image.save("render.png")
    print()
    print("Render finished: render.png")

    return image



light_position = Vec3(-6, 4, 0)
background_color = Vec3(0, 0, 0)

sphere1 = Sphere(
    Vec3(-0.5, 2, -5),
    1.0,
    Vec3(1, 0, 0),
    0.25
)

sphere2 = Sphere(
    Vec3(0.8, 0, -7.0),
    1.3,
    Vec3(0, 1, 0),
    0.35
)

plane = Plane(
    Vec3(0, -2, 0),      # точка на плоскости
    Vec3(0, 1, 0),       # нормаль вверх
    Vec3(0.8, 0.8, 0.8), # светло-серый пол
    0.15
)

objects = [sphere1, sphere2, plane]

render(400, 300, objects, background_color, light_position, 0, 4)


