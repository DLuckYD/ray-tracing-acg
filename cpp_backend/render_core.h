#pragma once

#include <vector>

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
);

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
);