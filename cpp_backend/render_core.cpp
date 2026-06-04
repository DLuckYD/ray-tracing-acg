#include "render_core.h"
#include "bvh_core.h"

#include <algorithm>
#include <cmath>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace {

struct Vec3d {
    double x;
    double y;
    double z;
};

inline Vec3d make_vec3(double x, double y, double z) {
    return {x, y, z};
}

inline Vec3d add(const Vec3d& a, const Vec3d& b) {
    return {a.x + b.x, a.y + b.y, a.z + b.z};
}

inline Vec3d sub(const Vec3d& a, const Vec3d& b) {
    return {a.x - b.x, a.y - b.y, a.z - b.z};
}

inline Vec3d mul(const Vec3d& a, double s) {
    return {a.x * s, a.y * s, a.z * s};
}

inline double dot(const Vec3d& a, const Vec3d& b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

inline double length(const Vec3d& v) {
    return std::sqrt(dot(v, v));
}

inline Vec3d normalize(const Vec3d& v) {
    double len = length(v);
    if (len == 0.0) return {0.0, 0.0, 0.0};
    return {v.x / len, v.y / len, v.z / len};
}

inline Vec3d clamp01(const Vec3d& v) {
    return {
        std::max(0.0, std::min(1.0, v.x)),
        std::max(0.0, std::min(1.0, v.y)),
        std::max(0.0, std::min(1.0, v.z))
    };
}

inline Vec3d reflect_dir(const Vec3d& dir, const Vec3d& normal) {
    double d = dot(dir, normal);
    return normalize(sub(dir, mul(normal, 2.0 * d)));
}

inline bool refract_dir(const Vec3d& direction, const Vec3d& normal, double n1, double n2, Vec3d& out_dir) {
    Vec3d d = normalize(direction);
    Vec3d n = normalize(normal);

    double eta = n1 / n2;
    double cos_i = -dot(n, d);
    double k = 1.0 - eta * eta * (1.0 - cos_i * cos_i);

    if (k < 0.0) {
        return false;
    }

    out_dir = normalize(add(mul(d, eta), mul(n, eta * cos_i - std::sqrt(k))));
    return true;
}

struct HitInfo {
    bool hit;
    int triangle_index;
    double t;
};

inline HitInfo find_closest_triangle_hit(
    const Vec3d& origin,
    const Vec3d& direction,
    int root_index,

    const int* flat_triangle_indices,

    const double* node_aabb_min_x,
    const double* node_aabb_min_y,
    const double* node_aabb_min_z,
    const double* node_aabb_max_x,
    const double* node_aabb_max_y,
    const double* node_aabb_max_z,

    const int* node_left,
    const int* node_right,
    const int* node_start,
    const int* node_count,
    const unsigned char* node_is_leaf,

    const double* v0x, const double* v0y, const double* v0z,
    const double* v1x, const double* v1y, const double* v1z,
    const double* v2x, const double* v2y, const double* v2z,

    int node_count_total
) {
    auto result = triangle_bvh_intersect_cpp(
        origin.x, origin.y, origin.z,
        direction.x, direction.y, direction.z,
        root_index,

        flat_triangle_indices,

        node_aabb_min_x,
        node_aabb_min_y,
        node_aabb_min_z,
        node_aabb_max_x,
        node_aabb_max_y,
        node_aabb_max_z,

        node_left,
        node_right,
        node_start,
        node_count,
        node_is_leaf,

        v0x, v0y, v0z,
        v1x, v1y, v1z,
        v2x, v2y, v2z,

        node_count_total
    );

    if (result.first < 0 || result.second < 0.0) {
        return {false, -1, -1.0};
    }

    return {true, result.first, result.second};
}

inline bool shadow_blocked(
    const Vec3d& origin,
    const Vec3d& direction,
    double max_distance,
    int root_index,

    const int* flat_triangle_indices,

    const double* node_aabb_min_x,
    const double* node_aabb_min_y,
    const double* node_aabb_min_z,
    const double* node_aabb_max_x,
    const double* node_aabb_max_y,
    const double* node_aabb_max_z,

    const int* node_left,
    const int* node_right,
    const int* node_start,
    const int* node_count,
    const unsigned char* node_is_leaf,

    const double* v0x, const double* v0y, const double* v0z,
    const double* v1x, const double* v1y, const double* v1z,
    const double* v2x, const double* v2y, const double* v2z,

    int node_count_total
) {
    return triangle_bvh_shadow_blocked_cpp(
        origin.x, origin.y, origin.z,
        direction.x, direction.y, direction.z,
        max_distance,
        root_index,

        flat_triangle_indices,

        node_aabb_min_x,
        node_aabb_min_y,
        node_aabb_min_z,
        node_aabb_max_x,
        node_aabb_max_y,
        node_aabb_max_z,

        node_left,
        node_right,
        node_start,
        node_count,
        node_is_leaf,

        v0x, v0y, v0z,
        v1x, v1y, v1z,
        v2x, v2y, v2z,

        node_count_total
    );
}

Vec3d trace_ray_triangle_only(
    const Vec3d& origin,
    const Vec3d& direction,
    int depth,
    int max_depth,

    const Vec3d& light_position,
    const Vec3d& background_color,

    int root_index,

    const int* flat_triangle_indices,

    const double* node_aabb_min_x,
    const double* node_aabb_min_y,
    const double* node_aabb_min_z,
    const double* node_aabb_max_x,
    const double* node_aabb_max_y,
    const double* node_aabb_max_z,

    const int* node_left,
    const int* node_right,
    const int* node_start,
    const int* node_count,
    const unsigned char* node_is_leaf,

    const double* v0x, const double* v0y, const double* v0z,
    const double* v1x, const double* v1y, const double* v1z,
    const double* v2x, const double* v2y, const double* v2z,

    const double* normal_x,
    const double* normal_y,
    const double* normal_z,

    const double* color_r,
    const double* color_g,
    const double* color_b,

    const double* reflection,
    const double* transparency,
    const double* ior,

    int node_count_total
) {
    if (depth > max_depth) {
        return background_color;
    }

    HitInfo hit = find_closest_triangle_hit(
        origin, direction,
        root_index,

        flat_triangle_indices,

        node_aabb_min_x,
        node_aabb_min_y,
        node_aabb_min_z,
        node_aabb_max_x,
        node_aabb_max_y,
        node_aabb_max_z,

        node_left,
        node_right,
        node_start,
        node_count,
        node_is_leaf,

        v0x, v0y, v0z,
        v1x, v1y, v1z,
        v2x, v2y, v2z,

        node_count_total
    );

    if (!hit.hit) {
        return background_color;
    }

    const int tri = hit.triangle_index;
    const double t = hit.t;

    Vec3d hit_point = add(origin, mul(direction, t));
    Vec3d normal = {normal_x[tri], normal_y[tri], normal_z[tri]};

    const double surface_color_r = color_r[tri];
    const double surface_color_g = color_g[tri];
    const double surface_color_b = color_b[tri];
    const double surface_reflection = reflection[tri];
    const double surface_transparency = transparency[tri];
    const double surface_ior = ior[tri];

    Vec3d to_light = sub(light_position, hit_point);
    double distance_to_light = length(to_light);

    Vec3d direction_light;
    if (distance_to_light == 0.0) {
        direction_light = {0.0, 0.0, 0.0};
    } else {
        direction_light = mul(to_light, 1.0 / distance_to_light);
    }

    const double epsilon = 0.001;
    Vec3d shadow_origin = {
        hit_point.x + normal.x * epsilon,
        hit_point.y + normal.y * epsilon,
        hit_point.z + normal.z * epsilon
    };

    bool blocked = shadow_blocked(
        shadow_origin,
        direction_light,
        distance_to_light,
        root_index,

        flat_triangle_indices,

        node_aabb_min_x,
        node_aabb_min_y,
        node_aabb_min_z,
        node_aabb_max_x,
        node_aabb_max_y,
        node_aabb_max_z,

        node_left,
        node_right,
        node_start,
        node_count,
        node_is_leaf,

        v0x, v0y, v0z,
        v1x, v1y, v1z,
        v2x, v2y, v2z,

        node_count_total
    );

    double diffuse = 0.0;
    if (!blocked) {
        diffuse = dot(normal, direction_light);
        if (diffuse < 0.0) diffuse = 0.0;
    }

    const double ambient_strength = 0.1;
    double light_strength = ambient_strength + diffuse;
    if (light_strength > 1.0) light_strength = 1.0;

    Vec3d local_color = {
        surface_color_r * light_strength,
        surface_color_g * light_strength,
        surface_color_b * light_strength
    };

    if (surface_reflection <= 0.0 && surface_transparency <= 0.0) {
        return local_color;
    }

    if (surface_transparency <= 0.0) {
        Vec3d reflected_direction = reflect_dir(direction, normal);
        Vec3d reflect_origin = {
            hit_point.x + normal.x * epsilon,
            hit_point.y + normal.y * epsilon,
            hit_point.z + normal.z * epsilon
        };

        Vec3d reflected_color = trace_ray_triangle_only(
            reflect_origin,
            reflected_direction,
            depth + 1,
            max_depth,
            light_position,
            background_color,

            root_index,

            flat_triangle_indices,

            node_aabb_min_x,
            node_aabb_min_y,
            node_aabb_min_z,
            node_aabb_max_x,
            node_aabb_max_y,
            node_aabb_max_z,

            node_left,
            node_right,
            node_start,
            node_count,
            node_is_leaf,

            v0x, v0y, v0z,
            v1x, v1y, v1z,
            v2x, v2y, v2z,

            normal_x,
            normal_y,
            normal_z,

            color_r,
            color_g,
            color_b,

            reflection,
            transparency,
            ior,

            node_count_total
        );

        double local_weight = 1.0 - surface_reflection;
        if (local_weight < 0.0) local_weight = 0.0;

        return add(mul(local_color, local_weight), mul(reflected_color, surface_reflection));
    }

    Vec3d reflected_direction = reflect_dir(direction, normal);
    Vec3d reflect_origin = {
        hit_point.x + normal.x * epsilon,
        hit_point.y + normal.y * epsilon,
        hit_point.z + normal.z * epsilon
    };

    Vec3d reflected_color = trace_ray_triangle_only(
        reflect_origin,
        reflected_direction,
        depth + 1,
        max_depth,
        light_position,
        background_color,

        root_index,

        flat_triangle_indices,

        node_aabb_min_x,
        node_aabb_min_y,
        node_aabb_min_z,
        node_aabb_max_x,
        node_aabb_max_y,
        node_aabb_max_z,

        node_left,
        node_right,
        node_start,
        node_count,
        node_is_leaf,

        v0x, v0y, v0z,
        v1x, v1y, v1z,
        v2x, v2y, v2z,

        normal_x,
        normal_y,
        normal_z,

        color_r,
        color_g,
        color_b,

        reflection,
        transparency,
        ior,

        node_count_total
    );

    Vec3d refracted_color = {0.0, 0.0, 0.0};

    Vec3d refract_normal;
    double n1, n2;

    if (dot(direction, normal) < 0.0) {
        refract_normal = normal;
        n1 = 1.0;
        n2 = surface_ior;
    } else {
        refract_normal = {-normal.x, -normal.y, -normal.z};
        n1 = surface_ior;
        n2 = 1.0;
    }

    Vec3d refracted_direction;
    bool refracted_ok = refract_dir(direction, refract_normal, n1, n2, refracted_direction);

    if (refracted_ok) {
        Vec3d refract_origin = {
            hit_point.x - refract_normal.x * epsilon,
            hit_point.y - refract_normal.y * epsilon,
            hit_point.z - refract_normal.z * epsilon
        };

        refracted_color = trace_ray_triangle_only(
            refract_origin,
            refracted_direction,
            depth + 1,
            max_depth,
            light_position,
            background_color,

            root_index,

            flat_triangle_indices,

            node_aabb_min_x,
            node_aabb_min_y,
            node_aabb_min_z,
            node_aabb_max_x,
            node_aabb_max_y,
            node_aabb_max_z,

            node_left,
            node_right,
            node_start,
            node_count,
            node_is_leaf,

            v0x, v0y, v0z,
            v1x, v1y, v1z,
            v2x, v2y, v2z,

            normal_x,
            normal_y,
            normal_z,

            color_r,
            color_g,
            color_b,

            reflection,
            transparency,
            ior,

            node_count_total
        );
    }

    double local_weight = 1.0 - surface_reflection - surface_transparency;
    if (local_weight < 0.0) local_weight = 0.0;

    return add(
        add(mul(local_color, local_weight), mul(reflected_color, surface_reflection)),
        mul(refracted_color, surface_transparency)
    );
}

} // namespace

std::vector<unsigned char> render_triangle_image_cpp(
    int width,
    int height,
    int max_depth,
    int num_threads,

    double light_x,
    double light_y,
    double light_z,

    double background_r,
    double background_g,
    double background_b,

    int root_index,

    const int* flat_triangle_indices,

    const double* node_aabb_min_x,
    const double* node_aabb_min_y,
    const double* node_aabb_min_z,
    const double* node_aabb_max_x,
    const double* node_aabb_max_y,
    const double* node_aabb_max_z,

    const int* node_left,
    const int* node_right,
    const int* node_start,
    const int* node_count,
    const unsigned char* node_is_leaf,

    const double* v0x, const double* v0y, const double* v0z,
    const double* v1x, const double* v1y, const double* v1z,
    const double* v2x, const double* v2y, const double* v2z,

    const double* normal_x,
    const double* normal_y,
    const double* normal_z,

    const double* color_r,
    const double* color_g,
    const double* color_b,

    const double* reflection,
    const double* transparency,
    const double* ior,

    const double* screen_x_values,
    const double* screen_y_values,

    int node_count_total
) {
    std::vector<unsigned char> buffer(static_cast<size_t>(width * height * 3));

    Vec3d camera_origin = {0.0, 0.0, 0.0};
    Vec3d light_position = {light_x, light_y, light_z};
    Vec3d background_color = {background_r, background_g, background_b};

#ifdef _OPENMP
    if (num_threads > 0) {
        omp_set_num_threads(num_threads);
    }
#endif

#pragma omp parallel for schedule(dynamic, 4) if(height > 32)
    for (int y = 0; y < height; ++y) {
        double screen_y = screen_y_values[y];

        for (int x = 0; x < width; ++x) {
            double screen_x = screen_x_values[x];

            Vec3d pixel_pos = {screen_x, screen_y, -1.0};
            Vec3d direction = normalize(sub(pixel_pos, camera_origin));

            Vec3d color = trace_ray_triangle_only(
                camera_origin,
                direction,
                0,
                max_depth,
                light_position,
                background_color,

                root_index,

                flat_triangle_indices,

                node_aabb_min_x,
                node_aabb_min_y,
                node_aabb_min_z,
                node_aabb_max_x,
                node_aabb_max_y,
                node_aabb_max_z,

                node_left,
                node_right,
                node_start,
                node_count,
                node_is_leaf,

                v0x, v0y, v0z,
                v1x, v1y, v1z,
                v2x, v2y, v2z,

                normal_x,
                normal_y,
                normal_z,

                color_r,
                color_g,
                color_b,

                reflection,
                transparency,
                ior,

                node_count_total
            );

            color = clamp01(color);

            size_t write_index = static_cast<size_t>((y * width + x) * 3);

            buffer[write_index]     = static_cast<unsigned char>(std::max(0.0, std::min(255.0, color.x * 255.0)));
            buffer[write_index + 1] = static_cast<unsigned char>(std::max(0.0, std::min(255.0, color.y * 255.0)));
            buffer[write_index + 2] = static_cast<unsigned char>(std::max(0.0, std::min(255.0, color.z * 255.0)));
        }
    }

    return buffer;
}