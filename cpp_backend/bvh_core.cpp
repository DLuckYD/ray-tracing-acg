#include "bvh_core.h"
#include "triangle_core.h"

#include <algorithm>
#include <cmath>
#include <tuple>
#include <utility>
#include <vector>

std::tuple<bool, double, double> intersect_aabb_kernel_cpp(
    double ox, double oy, double oz,
    double dx, double dy, double dz,
    double min_x, double min_y, double min_z,
    double max_x, double max_y, double max_z
) {
    const double epsilon = 1e-6;

    double tx_min, tx_max;
    double ty_min, ty_max;
    double tz_min, tz_max;

    if (std::abs(dx) < epsilon) {
        if (ox < min_x || ox > max_x) {
            return {false, 0.0, 0.0};
        }
        tx_min = -1.0e30;
        tx_max =  1.0e30;
    } else {
        const double tx1 = (min_x - ox) / dx;
        const double tx2 = (max_x - ox) / dx;
        tx_min = std::min(tx1, tx2);
        tx_max = std::max(tx1, tx2);
    }

    if (std::abs(dy) < epsilon) {
        if (oy < min_y || oy > max_y) {
            return {false, 0.0, 0.0};
        }
        ty_min = -1.0e30;
        ty_max =  1.0e30;
    } else {
        const double ty1 = (min_y - oy) / dy;
        const double ty2 = (max_y - oy) / dy;
        ty_min = std::min(ty1, ty2);
        ty_max = std::max(ty1, ty2);
    }

    if (std::abs(dz) < epsilon) {
        if (oz < min_z || oz > max_z) {
            return {false, 0.0, 0.0};
        }
        tz_min = -1.0e30;
        tz_max =  1.0e30;
    } else {
        const double tz1 = (min_z - oz) / dz;
        const double tz2 = (max_z - oz) / dz;
        tz_min = std::min(tz1, tz2);
        tz_max = std::max(tz1, tz2);
    }

    const double t_enter = std::max({tx_min, ty_min, tz_min});
    const double t_exit  = std::min({tx_max, ty_max, tz_max});

    if (t_enter > t_exit || t_exit < 0.0) {
        return {false, 0.0, 0.0};
    }

    return {true, t_enter, t_exit};
}

static inline double intersect_triangle_direct_cpp(
    double ox, double oy, double oz,
    double dx, double dy, double dz,
    const double* v0x, const double* v0y, const double* v0z,
    const double* v1x, const double* v1y, const double* v1z,
    const double* v2x, const double* v2y, const double* v2z,
    int triangle_index
) {
    return intersect_triangle_kernel_cpp(
        ox, oy, oz,
        dx, dy, dz,
        v0x[triangle_index], v0y[triangle_index], v0z[triangle_index],
        v1x[triangle_index], v1y[triangle_index], v1z[triangle_index],
        v2x[triangle_index], v2y[triangle_index], v2z[triangle_index]
    );
}

std::pair<int, double> triangle_bvh_intersect_cpp(
    double ox, double oy, double oz,
    double dx, double dy, double dz,
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
    if (root_index < 0) {
        return {-1, -1.0};
    }

    std::vector<int> stack;
    stack.reserve(node_count_total);
    stack.push_back(root_index);

    int best_triangle_index = -1;
    double best_t = -1.0;

    while (!stack.empty()) {
        const int node_index = stack.back();
        stack.pop_back();

        auto [hit, node_t_enter, node_t_exit] = intersect_aabb_kernel_cpp(
            ox, oy, oz, dx, dy, dz,
            node_aabb_min_x[node_index],
            node_aabb_min_y[node_index],
            node_aabb_min_z[node_index],
            node_aabb_max_x[node_index],
            node_aabb_max_y[node_index],
            node_aabb_max_z[node_index]
        );

        if (!hit) {
            continue;
        }

        if (best_t > 0.0 && node_t_enter > best_t) {
            continue;
        }

        if (node_is_leaf[node_index] == 1) {
            const int start = node_start[node_index];
            const int end = start + node_count[node_index];

            for (int i = start; i < end; ++i) {
                const int triangle_index = flat_triangle_indices[i];

                const double t = intersect_triangle_direct_cpp(
                    ox, oy, oz, dx, dy, dz,
                    v0x, v0y, v0z,
                    v1x, v1y, v1z,
                    v2x, v2y, v2z,
                    triangle_index
                );

                if (t > 0.0) {
                    if (best_t < 0.0 || t < best_t) {
                        best_t = t;
                        best_triangle_index = triangle_index;
                    }
                }
            }

            continue;
        }

        const int left_index = node_left[node_index];
        const int right_index = node_right[node_index];

        bool left_hit = false;
        bool right_hit = false;
        double left_t_enter = 0.0;
        double right_t_enter = 0.0;

        if (left_index != -1) {
            auto [lh, le, lx] = intersect_aabb_kernel_cpp(
                ox, oy, oz, dx, dy, dz,
                node_aabb_min_x[left_index],
                node_aabb_min_y[left_index],
                node_aabb_min_z[left_index],
                node_aabb_max_x[left_index],
                node_aabb_max_y[left_index],
                node_aabb_max_z[left_index]
            );
            left_hit = lh;
            left_t_enter = le;
        }

        if (right_index != -1) {
            auto [rh, re, rx] = intersect_aabb_kernel_cpp(
                ox, oy, oz, dx, dy, dz,
                node_aabb_min_x[right_index],
                node_aabb_min_y[right_index],
                node_aabb_min_z[right_index],
                node_aabb_max_x[right_index],
                node_aabb_max_y[right_index],
                node_aabb_max_z[right_index]
            );
            right_hit = rh;
            right_t_enter = re;
        }

        if (!left_hit && !right_hit) {
            continue;
        }

        if (!right_hit) {
            stack.push_back(left_index);
            continue;
        }

        if (!left_hit) {
            stack.push_back(right_index);
            continue;
        }

        int near_index, far_index;
        double far_t_enter;

        if (left_t_enter <= right_t_enter) {
            near_index = left_index;
            far_index = right_index;
            far_t_enter = right_t_enter;
        } else {
            near_index = right_index;
            far_index = left_index;
            far_t_enter = left_t_enter;
        }

        if (best_t < 0.0 || far_t_enter <= best_t) {
            stack.push_back(far_index);
        }

        stack.push_back(near_index);
    }

    return {best_triangle_index, best_t};
}

bool triangle_bvh_shadow_blocked_cpp(
    double ox, double oy, double oz,
    double dx, double dy, double dz,
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
    if (root_index < 0) {
        return false;
    }

    std::vector<int> stack;
    stack.reserve(node_count_total);
    stack.push_back(root_index);

    while (!stack.empty()) {
        const int node_index = stack.back();
        stack.pop_back();

        auto [hit, node_t_enter, node_t_exit] = intersect_aabb_kernel_cpp(
            ox, oy, oz, dx, dy, dz,
            node_aabb_min_x[node_index],
            node_aabb_min_y[node_index],
            node_aabb_min_z[node_index],
            node_aabb_max_x[node_index],
            node_aabb_max_y[node_index],
            node_aabb_max_z[node_index]
        );

        if (!hit) {
            continue;
        }

        if (node_t_enter > max_distance) {
            continue;
        }

        if (node_is_leaf[node_index] == 1) {
            const int start = node_start[node_index];
            const int end = start + node_count[node_index];

            for (int i = start; i < end; ++i) {
                const int triangle_index = flat_triangle_indices[i];

                const double t = intersect_triangle_direct_cpp(
                    ox, oy, oz, dx, dy, dz,
                    v0x, v0y, v0z,
                    v1x, v1y, v1z,
                    v2x, v2y, v2z,
                    triangle_index
                );

                if (t > 0.0 && t < max_distance) {
                    return true;
                }
            }

            continue;
        }

        const int left_index = node_left[node_index];
        const int right_index = node_right[node_index];

        bool left_hit = false;
        bool right_hit = false;
        double left_t_enter = 0.0;
        double right_t_enter = 0.0;

        if (left_index != -1) {
            auto [lh, le, lx] = intersect_aabb_kernel_cpp(
                ox, oy, oz, dx, dy, dz,
                node_aabb_min_x[left_index],
                node_aabb_min_y[left_index],
                node_aabb_min_z[left_index],
                node_aabb_max_x[left_index],
                node_aabb_max_y[left_index],
                node_aabb_max_z[left_index]
            );
            left_hit = lh;
            left_t_enter = le;
        }

        if (right_index != -1) {
            auto [rh, re, rx] = intersect_aabb_kernel_cpp(
                ox, oy, oz, dx, dy, dz,
                node_aabb_min_x[right_index],
                node_aabb_min_y[right_index],
                node_aabb_min_z[right_index],
                node_aabb_max_x[right_index],
                node_aabb_max_y[right_index],
                node_aabb_max_z[right_index]
            );
            right_hit = rh;
            right_t_enter = re;
        }

        if (!left_hit && !right_hit) {
            continue;
        }

        if (!right_hit) {
            stack.push_back(left_index);
            continue;
        }

        if (!left_hit) {
            stack.push_back(right_index);
            continue;
        }

        if (left_t_enter <= right_t_enter) {
            stack.push_back(right_index);
            stack.push_back(left_index);
        } else {
            stack.push_back(left_index);
            stack.push_back(right_index);
        }
    }

    return false;
}