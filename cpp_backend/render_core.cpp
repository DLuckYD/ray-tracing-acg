#include "render_core.h"
#include "bvh_core.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace {

constexpr double PI = 3.14159265358979323846;
constexpr double EPSILON = 0.001;

struct Vec3d {
    double x;
    double y;
    double z;
};

struct HitInfo {
    bool hit;
    int triangle_index;
    double t;
};

inline Vec3d add(const Vec3d& a, const Vec3d& b) {
    return {a.x + b.x, a.y + b.y, a.z + b.z};
}

inline Vec3d sub(const Vec3d& a, const Vec3d& b) {
    return {a.x - b.x, a.y - b.y, a.z - b.z};
}

inline Vec3d mul(const Vec3d& a, double s) {
    return {a.x * s, a.y * s, a.z * s};
}

inline Vec3d mul_vec(const Vec3d& a, const Vec3d& b) {
    return {a.x * b.x, a.y * b.y, a.z * b.z};
}

inline Vec3d div_vec(const Vec3d& a, double s) {
    return {a.x / s, a.y / s, a.z / s};
}

inline double dot(const Vec3d& a, const Vec3d& b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

inline Vec3d cross(const Vec3d& a, const Vec3d& b) {
    return {
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x
    };
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

inline uint64_t xorshift64(uint64_t& state) {
    state ^= state << 13;
    state ^= state >> 7;
    state ^= state << 17;
    return state;
}

inline double random_double_01(uint64_t& state) {
    uint64_t v = xorshift64(state);
    return (v >> 11) * (1.0 / 9007199254740992.0);
}

inline Vec3d mix(const Vec3d& a, const Vec3d& b, double t) {
    return add(mul(a, 1.0 - t), mul(b, t));
}

inline Vec3d build_sky_color(const Vec3d& direction, const Vec3d& background_color) {
    double t = 0.5 * (direction.y + 1.0);

    Vec3d ground_tint = {
        background_color.x * 0.55 + 0.10,
        background_color.y * 0.55 + 0.11,
        background_color.z * 0.55 + 0.13
    };

    Vec3d horizon = {
        background_color.x * 0.75 + 0.18,
        background_color.y * 0.75 + 0.20,
        background_color.z * 0.75 + 0.24
    };

    Vec3d zenith = {
        background_color.x * 0.45 + 0.36,
        background_color.y * 0.45 + 0.42,
        background_color.z * 0.45 + 0.55
    };

    if (direction.y < 0.0) {
        double g = std::min(1.0, -direction.y);
        return mix(horizon, ground_tint, g * 0.65);
    }

    return mix(horizon, zenith, t);
}

inline Vec3d cosine_weighted_hemisphere_direction(const Vec3d& normal, uint64_t& rng_state) {
    double r1 = random_double_01(rng_state);
    double r2 = random_double_01(rng_state);

    double phi = 2.0 * PI * r1;
    double r = std::sqrt(r2);

    double x = r * std::cos(phi);
    double y = r * std::sin(phi);
    double z = std::sqrt(std::max(0.0, 1.0 - r2));

    Vec3d n = normalize(normal);
    Vec3d helper = (std::fabs(n.x) > 0.1) ? Vec3d{0.0, 1.0, 0.0} : Vec3d{1.0, 0.0, 0.0};

    Vec3d tangent = normalize(cross(helper, n));
    Vec3d bitangent = cross(n, tangent);

    Vec3d world_dir = add(
        add(mul(tangent, x), mul(bitangent, y)),
        mul(n, z)
    );

    return normalize(world_dir);
}

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

    Vec3d shadow_origin = {
        hit_point.x + normal.x * EPSILON,
        hit_point.y + normal.y * EPSILON,
        hit_point.z + normal.z * EPSILON
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
            hit_point.x + normal.x * EPSILON,
            hit_point.y + normal.y * EPSILON,
            hit_point.z + normal.z * EPSILON
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
        hit_point.x + normal.x * EPSILON,
        hit_point.y + normal.y * EPSILON,
        hit_point.z + normal.z * EPSILON
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
            hit_point.x - refract_normal.x * EPSILON,
            hit_point.y - refract_normal.y * EPSILON,
            hit_point.z - refract_normal.z * EPSILON
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

Vec3d trace_path_ray_triangle_only(
    const Vec3d& origin,
    const Vec3d& direction,
    int depth,
    int max_bounces,
    uint64_t& rng_state,

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

    int node_count_total
) {
    if (depth >= max_bounces) {
        return {0.0, 0.0, 0.0};
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
        return build_sky_color(direction, background_color);
    }

    const int tri = hit.triangle_index;
    const double t = hit.t;

    Vec3d hit_point = add(origin, mul(direction, t));
    Vec3d normal = normalize({normal_x[tri], normal_y[tri], normal_z[tri]});
    Vec3d base_albedo = {color_r[tri], color_g[tri], color_b[tri]};

    if (dot(normal, direction) > 0.0) {
        normal = mul(normal, -1.0);
    }

    Vec3d albedo = {
        std::max(0.0, std::min(1.0, base_albedo.x * 0.82)),
        std::max(0.0, std::min(1.0, base_albedo.y * 0.82)),
        std::max(0.0, std::min(1.0, base_albedo.z * 0.82))
    };

    Vec3d direct_color = {0.0, 0.0, 0.0};

    Vec3d to_light = sub(light_position, hit_point);
    double distance_to_light = length(to_light);

    if (distance_to_light > 0.0) {
        Vec3d light_dir = mul(to_light, 1.0 / distance_to_light);
        double n_dot_l = std::max(0.0, dot(normal, light_dir));

        if (n_dot_l > 0.0) {
            Vec3d shadow_origin = add(hit_point, mul(normal, EPSILON));
            bool blocked = shadow_blocked(
                shadow_origin,
                light_dir,
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

            if (!blocked) {
                double attenuation = 1.35 / (1.0 + 0.0045 * distance_to_light * distance_to_light);
                direct_color = mul(albedo, n_dot_l * attenuation);
            }
        }
    }

    Vec3d bounce_dir = cosine_weighted_hemisphere_direction(normal, rng_state);
    Vec3d bounce_origin = add(hit_point, mul(normal, EPSILON));

    Vec3d indirect = trace_path_ray_triangle_only(
        bounce_origin,
        bounce_dir,
        depth + 1,
        max_bounces,
        rng_state,

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

        node_count_total
    );

    Vec3d sky_tint = {
        0.92,
        0.95,
        1.0
    };

    Vec3d indirect_color = mul_vec(albedo, mul_vec(indirect, sky_tint));

    if (depth >= 2) {
        double p = std::max({albedo.x, albedo.y, albedo.z, 0.30});
        if (random_double_01(rng_state) > p) {
            return direct_color;
        }
        indirect_color = div_vec(indirect_color, p);
    }

    Vec3d ambient_lift = mul(albedo, 0.025);
    Vec3d result = add(add(mul(direct_color, 0.72), mul(indirect_color, 0.82)), ambient_lift);
    return result;
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

std::vector<unsigned char> render_triangle_path_traced_image_cpp(
    int width,
    int height,
    int samples_per_pixel,
    int max_bounces,
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
    (void)reflection;
    (void)transparency;
    (void)ior;

    std::vector<unsigned char> buffer(static_cast<size_t>(width * height * 3));

    Vec3d camera_origin = {0.0, 0.0, 0.0};
    Vec3d light_position = {light_x, light_y, light_z};
    Vec3d background_color = {background_r, background_g, background_b};

#ifdef _OPENMP
    if (num_threads > 0) {
        omp_set_num_threads(num_threads);
    }
#endif

#pragma omp parallel for schedule(dynamic, 2) if(height > 16)
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            uint64_t rng_state = 1469598103934665603ull
                                 ^ static_cast<uint64_t>(x + 1) * 1099511628211ull
                                 ^ static_cast<uint64_t>(y + 1) * 1469598103934665603ull;

            Vec3d accumulated = {0.0, 0.0, 0.0};

            for (int s = 0; s < samples_per_pixel; ++s) {
                double jitter_x = random_double_01(rng_state) - 0.5;
                double jitter_y = random_double_01(rng_state) - 0.5;

                double screen_x = screen_x_values[x] + jitter_x * (2.0 / static_cast<double>(width));
                double screen_y = screen_y_values[y] - jitter_y * (2.0 / static_cast<double>(height));

                Vec3d pixel_pos = {screen_x, screen_y, -1.0};
                Vec3d direction = normalize(sub(pixel_pos, camera_origin));

                Vec3d sample_color = trace_path_ray_triangle_only(
                    camera_origin,
                    direction,
                    0,
                    max_bounces,
                    rng_state,

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

                    node_count_total
                );

                accumulated = add(accumulated, sample_color);
            }

            Vec3d color = div_vec(accumulated, static_cast<double>(samples_per_pixel));
            color = clamp01(color);

            color.x = std::sqrt(color.x);
            color.y = std::sqrt(color.y);
            color.z = std::sqrt(color.z);

            size_t write_index = static_cast<size_t>((y * width + x) * 3);

            buffer[write_index]     = static_cast<unsigned char>(std::max(0.0, std::min(255.0, color.x * 255.0)));
            buffer[write_index + 1] = static_cast<unsigned char>(std::max(0.0, std::min(255.0, color.y * 255.0)));
            buffer[write_index + 2] = static_cast<unsigned char>(std::max(0.0, std::min(255.0, color.z * 255.0)));
        }
    }

    return buffer;
}