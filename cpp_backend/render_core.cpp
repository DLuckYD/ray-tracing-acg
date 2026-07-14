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

inline double clamp_double(double v, double lo, double hi) {
    return std::max(lo, std::min(hi, v));
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

inline double fresnel_schlick(double cos_theta, double n1, double n2) {
    double r0 = (n1 - n2) / (n1 + n2);
    r0 = r0 * r0;
    return r0 + (1.0 - r0) * std::pow(1.0 - cos_theta, 5.0);
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

inline double wrap01(double x) {
    x = std::fmod(x, 1.0);
    if (x < 0.0) x += 1.0;
    return x;
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

inline bool compute_barycentric(
    const Vec3d& p,
    const Vec3d& a,
    const Vec3d& b,
    const Vec3d& c,
    double& w0,
    double& w1,
    double& w2
) {
    Vec3d v0 = sub(b, a);
    Vec3d v1 = sub(c, a);
    Vec3d v2 = sub(p, a);

    double d00 = dot(v0, v0);
    double d01 = dot(v0, v1);
    double d11 = dot(v1, v1);
    double d20 = dot(v2, v0);
    double d21 = dot(v2, v1);

    double denom = d00 * d11 - d01 * d01;
    if (std::fabs(denom) < 1e-12) {
        return false;
    }

    w1 = (d11 * d20 - d01 * d21) / denom;
    w2 = (d00 * d21 - d01 * d20) / denom;
    w0 = 1.0 - w1 - w2;
    return true;
}

inline Vec3d fetch_texture_texel(
    int tex_id,
    int x,
    int y,
    const int* texture_widths,
    const int* texture_heights,
    const int* texture_offsets,
    const unsigned char* texture_pixels
) {
    int width = texture_widths[tex_id];
    int height = texture_heights[tex_id];
    int offset = texture_offsets[tex_id];

    x = std::max(0, std::min(width - 1, x));
    y = std::max(0, std::min(height - 1, y));

    int index = offset + (y * width + x) * 3;

    return {
        texture_pixels[index] / 255.0,
        texture_pixels[index + 1] / 255.0,
        texture_pixels[index + 2] / 255.0
    };
}

inline Vec3d sample_triangle_texture(
    int tri,
    const Vec3d& hit_point,

    const double* v0x, const double* v0y, const double* v0z,
    const double* v1x, const double* v1y, const double* v1z,
    const double* v2x, const double* v2y, const double* v2z,

    const double* uv0_u,
    const double* uv0_v,
    const double* uv1_u,
    const double* uv1_v,
    const double* uv2_u,
    const double* uv2_v,
    const unsigned char* has_uv,

    const int* texture_ids_per_triangle,
    const int* texture_widths,
    const int* texture_heights,
    const int* texture_offsets,
    const unsigned char* texture_pixels,

    int texture_count
) {
    if (texture_count <= 0 || has_uv == nullptr || texture_ids_per_triangle == nullptr) {
        return {-1.0, -1.0, -1.0};
    }

    if (has_uv[tri] == 0) {
        return {-1.0, -1.0, -1.0};
    }

    int tex_id = texture_ids_per_triangle[tri];
    if (tex_id < 0 || tex_id >= texture_count) {
        return {-1.0, -1.0, -1.0};
    }

    Vec3d a = {v0x[tri], v0y[tri], v0z[tri]};
    Vec3d b = {v1x[tri], v1y[tri], v1z[tri]};
    Vec3d c = {v2x[tri], v2y[tri], v2z[tri]};

    double w0, w1, w2;
    if (!compute_barycentric(hit_point, a, b, c, w0, w1, w2)) {
        return {-1.0, -1.0, -1.0};
    }

    double u = w0 * uv0_u[tri] + w1 * uv1_u[tri] + w2 * uv2_u[tri];
    double v = w0 * uv0_v[tri] + w1 * uv1_v[tri] + w2 * uv2_v[tri];

    u = wrap01(u);
    v = wrap01(v);

    int width = texture_widths[tex_id];
    int height = texture_heights[tex_id];

    double fx = u * (width - 1);
    double fy = (1.0 - v) * (height - 1);

    int x0 = static_cast<int>(std::floor(fx));
    int y0 = static_cast<int>(std::floor(fy));
    int x1 = std::min(x0 + 1, width - 1);
    int y1 = std::min(y0 + 1, height - 1);

    double tx = fx - x0;
    double ty = fy - y0;

    Vec3d c00 = fetch_texture_texel(tex_id, x0, y0, texture_widths, texture_heights, texture_offsets, texture_pixels);
    Vec3d c10 = fetch_texture_texel(tex_id, x1, y0, texture_widths, texture_heights, texture_offsets, texture_pixels);
    Vec3d c01 = fetch_texture_texel(tex_id, x0, y1, texture_widths, texture_heights, texture_offsets, texture_pixels);
    Vec3d c11 = fetch_texture_texel(tex_id, x1, y1, texture_widths, texture_heights, texture_offsets, texture_pixels);

    Vec3d top = mix(c00, c10, tx);
    Vec3d bottom = mix(c01, c11, tx);
    return mix(top, bottom, ty);
}

inline Vec3d resolve_triangle_albedo(
    int tri,
    const Vec3d& hit_point,

    const double* v0x, const double* v0y, const double* v0z,
    const double* v1x, const double* v1y, const double* v1z,
    const double* v2x, const double* v2y, const double* v2z,

    const double* color_r,
    const double* color_g,
    const double* color_b,

    const double* uv0_u,
    const double* uv0_v,
    const double* uv1_u,
    const double* uv1_v,
    const double* uv2_u,
    const double* uv2_v,
    const unsigned char* has_uv,

    const int* texture_ids_per_triangle,
    const int* texture_widths,
    const int* texture_heights,
    const int* texture_offsets,
    const unsigned char* texture_pixels,

    int texture_count
) {
    Vec3d base_color = {color_r[tri], color_g[tri], color_b[tri]};

    Vec3d texture_color = sample_triangle_texture(
        tri,
        hit_point,

        v0x, v0y, v0z,
        v1x, v1y, v1z,
        v2x, v2y, v2z,

        uv0_u, uv0_v,
        uv1_u, uv1_v,
        uv2_u, uv2_v,
        has_uv,

        texture_ids_per_triangle,
        texture_widths,
        texture_heights,
        texture_offsets,
        texture_pixels,

        texture_count
    );

    if (texture_color.x < 0.0) {
        return base_color;
    }

    return texture_color;
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

    const double* uv0_u,
    const double* uv0_v,
    const double* uv1_u,
    const double* uv1_v,
    const double* uv2_u,
    const double* uv2_v,
    const unsigned char* has_uv,

    const int* texture_ids_per_triangle,
    const int* texture_widths,
    const int* texture_heights,
    const int* texture_offsets,
    const unsigned char* texture_pixels,

    int node_count_total,
    int texture_count
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
    Vec3d surface_albedo = resolve_triangle_albedo(
        tri,
        hit_point,

        v0x, v0y, v0z,
        v1x, v1y, v1z,
        v2x, v2y, v2z,

        color_r, color_g, color_b,

        uv0_u, uv0_v,
        uv1_u, uv1_v,
        uv2_u, uv2_v,
        has_uv,

        texture_ids_per_triangle,
        texture_widths,
        texture_heights,
        texture_offsets,
        texture_pixels,

        texture_count
    );

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
        surface_albedo.x * light_strength,
        surface_albedo.y * light_strength,
        surface_albedo.z * light_strength
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

            uv0_u, uv0_v,
            uv1_u, uv1_v,
            uv2_u, uv2_v,
            has_uv,

            texture_ids_per_triangle,
            texture_widths,
            texture_heights,
            texture_offsets,
            texture_pixels,

            node_count_total,
            texture_count
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

        uv0_u, uv0_v,
        uv1_u, uv1_v,
        uv2_u, uv2_v,
        has_uv,

        texture_ids_per_triangle,
        texture_widths,
        texture_heights,
        texture_offsets,
        texture_pixels,

        node_count_total,
        texture_count
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

            uv0_u, uv0_v,
            uv1_u, uv1_v,
            uv2_u, uv2_v,
            has_uv,

            texture_ids_per_triangle,
            texture_widths,
            texture_heights,
            texture_offsets,
            texture_pixels,

            node_count_total,
            texture_count
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
    int use_russian_roulette,
    int rr_start_depth,

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

    const double* uv0_u,
    const double* uv0_v,
    const double* uv1_u,
    const double* uv1_v,
    const double* uv2_u,
    const double* uv2_v,
    const unsigned char* has_uv,

    const int* texture_ids_per_triangle,
    const int* texture_widths,
    const int* texture_heights,
    const int* texture_offsets,
    const unsigned char* texture_pixels,

    int node_count_total,
    int texture_count
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

    if (dot(normal, direction) > 0.0) {
        normal = mul(normal, -1.0);
    }

    Vec3d base_albedo = resolve_triangle_albedo(
        tri,
        hit_point,

        v0x, v0y, v0z,
        v1x, v1y, v1z,
        v2x, v2y, v2z,

        color_r, color_g, color_b,

        uv0_u, uv0_v,
        uv1_u, uv1_v,
        uv2_u, uv2_v,
        has_uv,

        texture_ids_per_triangle,
        texture_widths,
        texture_heights,
        texture_offsets,
        texture_pixels,

        texture_count
    );

    Vec3d albedo = {
        clamp_double(base_albedo.x * 0.82, 0.0, 1.0),
        clamp_double(base_albedo.y * 0.82, 0.0, 1.0),
        clamp_double(base_albedo.z * 0.82, 0.0, 1.0)
    };

    double material_reflection = clamp_double(reflection[tri], 0.0, 1.0);
    double material_transparency = clamp_double(transparency[tri], 0.0, 1.0);
    double material_ior = std::max(1.0, ior[tri]);

    double remaining_diffuse = 1.0 - material_reflection - material_transparency;
    if (remaining_diffuse < 0.0) {
        remaining_diffuse = 0.0;
    }

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
                direct_color = mul(albedo, n_dot_l * attenuation * remaining_diffuse);
            }
        }
    }

    if (use_russian_roulette != 0 && depth >= rr_start_depth) {
        double p = std::max({albedo.x, albedo.y, albedo.z, material_reflection, material_transparency, 0.25});
        p = clamp_double(p, 0.10, 0.95);

        if (random_double_01(rng_state) > p) {
            return direct_color;
        }

        double inv_p = 1.0 / p;
        albedo = mul(albedo, inv_p);
        material_reflection *= inv_p;
        material_transparency *= inv_p;
        remaining_diffuse *= inv_p;
    }

    double chooser = random_double_01(rng_state);

    if (material_transparency > 0.0 && chooser < material_transparency) {
        double n1 = 1.0;
        double n2 = material_ior;
        Vec3d oriented_normal = normal;
        bool entering = dot(direction, normal) < 0.0;

        if (!entering) {
            oriented_normal = mul(normal, -1.0);
            n1 = material_ior;
            n2 = 1.0;
        }

        double cos_theta = std::max(0.0, -dot(direction, oriented_normal));

        Vec3d refracted_dir;
        bool refracted_ok = refract_dir(direction, oriented_normal, n1, n2, refracted_dir);

        double fresnel = fresnel_schlick(cos_theta, n1, n2);
        fresnel = clamp_double(fresnel, 0.02, 0.98);

        Vec3d next_dir;
        Vec3d next_origin;
        Vec3d bounced;

        double reflection_pick = fresnel * 0.65;

        if (!refracted_ok || random_double_01(rng_state) < reflection_pick) {
            next_dir = reflect_dir(direction, oriented_normal);
            next_origin = add(hit_point, mul(oriented_normal, EPSILON * 2.0));
        } else {
            next_dir = refracted_dir;
            next_origin = sub(hit_point, mul(oriented_normal, EPSILON * 2.0));
        }

        bounced = trace_path_ray_triangle_only(
            next_origin,
            next_dir,
            depth + 1,
            max_bounces,
            rng_state,
            use_russian_roulette,
            rr_start_depth,

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

            uv0_u, uv0_v,
            uv1_u, uv1_v,
            uv2_u, uv2_v,
            has_uv,

            texture_ids_per_triangle,
            texture_widths,
            texture_heights,
            texture_offsets,
            texture_pixels,

            node_count_total,
            texture_count
        );

        Vec3d transmission_tint = mix(
            Vec3d{1.0, 1.0, 1.0},
            albedo,
            0.08
        );

        bounced = mul_vec(bounced, transmission_tint);
        Vec3d glass_lift = mul(albedo, 0.015);

        return add(add(direct_color, bounced), glass_lift);
    }

    if (material_reflection > 0.0 && chooser < material_transparency + material_reflection) {
        Vec3d reflected_dir = reflect_dir(direction, normal);
        Vec3d reflect_origin = add(hit_point, mul(normal, EPSILON));

        Vec3d bounced = trace_path_ray_triangle_only(
            reflect_origin,
            reflected_dir,
            depth + 1,
            max_bounces,
            rng_state,
            use_russian_roulette,
            rr_start_depth,

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

            uv0_u, uv0_v,
            uv1_u, uv1_v,
            uv2_u, uv2_v,
            has_uv,

            texture_ids_per_triangle,
            texture_widths,
            texture_heights,
            texture_offsets,
            texture_pixels,

            node_count_total,
            texture_count
        );

        Vec3d tinted = mix(bounced, mul_vec(bounced, albedo), 0.20);
        return add(direct_color, tinted);
    }

    Vec3d bounce_dir = cosine_weighted_hemisphere_direction(normal, rng_state);
    Vec3d bounce_origin = add(hit_point, mul(normal, EPSILON));

    Vec3d indirect = trace_path_ray_triangle_only(
        bounce_origin,
        bounce_dir,
        depth + 1,
        max_bounces,
        rng_state,
        use_russian_roulette,
        rr_start_depth,

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

        uv0_u, uv0_v,
        uv1_u, uv1_v,
        uv2_u, uv2_v,
        has_uv,

        texture_ids_per_triangle,
        texture_widths,
        texture_heights,
        texture_offsets,
        texture_pixels,

        node_count_total,
        texture_count
    );

    Vec3d sky_tint = {0.92, 0.95, 1.0};
    Vec3d indirect_color = mul_vec(albedo, mul_vec(indirect, sky_tint));

    Vec3d ambient_lift = mul(albedo, 0.025 * remaining_diffuse);
    Vec3d result = add(add(mul(direct_color, 0.72), mul(indirect_color, 0.82 * remaining_diffuse)), ambient_lift);
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

    const double* uv0_u,
    const double* uv0_v,
    const double* uv1_u,
    const double* uv1_v,
    const double* uv2_u,
    const double* uv2_v,
    const unsigned char* has_uv,

    const int* texture_ids_per_triangle,
    const int* texture_widths,
    const int* texture_heights,
    const int* texture_offsets,
    const unsigned char* texture_pixels,

    const double* screen_x_values,
    const double* screen_y_values,

    int node_count_total,
    int texture_count
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

                uv0_u, uv0_v,
                uv1_u, uv1_v,
                uv2_u, uv2_v,
                has_uv,

                texture_ids_per_triangle,
                texture_widths,
                texture_heights,
                texture_offsets,
                texture_pixels,

                node_count_total,
                texture_count
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
    int use_russian_roulette,
    int rr_start_depth,

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

    const double* uv0_u,
    const double* uv0_v,
    const double* uv1_u,
    const double* uv1_v,
    const double* uv2_u,
    const double* uv2_v,
    const unsigned char* has_uv,

    const int* texture_ids_per_triangle,
    const int* texture_widths,
    const int* texture_heights,
    const int* texture_offsets,
    const unsigned char* texture_pixels,

    const double* screen_x_values,
    const double* screen_y_values,

    int node_count_total,
    int texture_count
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
                    use_russian_roulette,
                    rr_start_depth,

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

                    uv0_u, uv0_v,
                    uv1_u, uv1_v,
                    uv2_u, uv2_v,
                    has_uv,

                    texture_ids_per_triangle,
                    texture_widths,
                    texture_heights,
                    texture_offsets,
                    texture_pixels,

                    node_count_total,
                    texture_count
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