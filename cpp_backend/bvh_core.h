#pragma once

#include <tuple>
#include <vector>

std::tuple<bool, double, double> intersect_aabb_kernel_cpp(
    double ox, double oy, double oz,
    double dx, double dy, double dz,
    double min_x, double min_y, double min_z,
    double max_x, double max_y, double max_z
);

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
);

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
);