import config
from math3d import Vec3
from aabb import compute_objects_aabb, get_largest_axis, get_aabb_center


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

def is_shadow_blocked(shadow_ray, objects, distance_to_light):
    # -----------------------------------------
    # BVH mode
    # -----------------------------------------
    if config.use_bvh:
        # Check finite objects inside BVH
        if bvh_shadow_blocked(shadow_ray, config.bvh_root, distance_to_light):
            return True

        # Check non-BVH objects, for example Plane
        for obj in config.non_bvh_objects:
            t = obj.intersect(shadow_ray)
            if t is not None and t < distance_to_light:
                return True

        return False

    # -----------------------------------------
    # Non-BVH mode: blocker cache + brute force
    # -----------------------------------------
    if config.blocker_cache_object is not None:
        t = config.blocker_cache_object.intersect(shadow_ray)
        if t is not None and t < distance_to_light:
            return True

    for obj in objects:
        if obj is config.blocker_cache_object:
            continue

        t = obj.intersect(shadow_ray)
        if t is not None and t < distance_to_light:
            config.blocker_cache_object = obj
            return True

    return False

def bvh_shadow_blocked(shadow_ray, node, distance_to_light):
    if node is None:
        return False

    # If the shadow ray does not hit the node box,
    # nothing inside can block the light
    if not node.aabb.intersect(shadow_ray):
        return False

    # Leaf node: test objects directly
    if node.is_leaf:
        for obj in node.objects:
            t = obj.intersect(shadow_ray)
            if t is not None and t < distance_to_light:
                return True

        return False

    # Inner node: recurse into children
    if bvh_shadow_blocked(shadow_ray, node.left, distance_to_light):
        return True

    if bvh_shadow_blocked(shadow_ray, node.right, distance_to_light):
        return True

    return False