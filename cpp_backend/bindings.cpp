#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include "triangle_core.h"
#include "bvh_core.h"
#include "render_core.h"

namespace py = pybind11;

PYBIND11_MODULE(rt_core, m) {
    m.doc() = "C++ rendering core for ray tracing";

    m.def("hello_backend", []() {
        return "rt_core loaded successfully";
    });

    m.def(
        "intersect_triangle_kernel_cpp",
        &intersect_triangle_kernel_cpp,
        py::arg("ox"), py::arg("oy"), py::arg("oz"),
        py::arg("dx"), py::arg("dy"), py::arg("dz"),
        py::arg("v0x"), py::arg("v0y"), py::arg("v0z"),
        py::arg("v1x"), py::arg("v1y"), py::arg("v1z"),
        py::arg("v2x"), py::arg("v2y"), py::arg("v2z")
    );

    m.def(
        "intersect_aabb_kernel_cpp",
        &intersect_aabb_kernel_cpp,
        py::arg("ox"), py::arg("oy"), py::arg("oz"),
        py::arg("dx"), py::arg("dy"), py::arg("dz"),
        py::arg("min_x"), py::arg("min_y"), py::arg("min_z"),
        py::arg("max_x"), py::arg("max_y"), py::arg("max_z")
    );

    m.def(
        "triangle_bvh_intersect_cpp",
        [](
            double ox, double oy, double oz,
            double dx, double dy, double dz,
            int root_index,

            py::array_t<int, py::array::c_style | py::array::forcecast> flat_triangle_indices,

            py::array_t<double, py::array::c_style | py::array::forcecast> node_aabb_min_x,
            py::array_t<double, py::array::c_style | py::array::forcecast> node_aabb_min_y,
            py::array_t<double, py::array::c_style | py::array::forcecast> node_aabb_min_z,
            py::array_t<double, py::array::c_style | py::array::forcecast> node_aabb_max_x,
            py::array_t<double, py::array::c_style | py::array::forcecast> node_aabb_max_y,
            py::array_t<double, py::array::c_style | py::array::forcecast> node_aabb_max_z,

            py::array_t<int, py::array::c_style | py::array::forcecast> node_left,
            py::array_t<int, py::array::c_style | py::array::forcecast> node_right,
            py::array_t<int, py::array::c_style | py::array::forcecast> node_start,
            py::array_t<int, py::array::c_style | py::array::forcecast> node_count,
            py::array_t<unsigned char, py::array::c_style | py::array::forcecast> node_is_leaf,

            py::array_t<double, py::array::c_style | py::array::forcecast> v0x,
            py::array_t<double, py::array::c_style | py::array::forcecast> v0y,
            py::array_t<double, py::array::c_style | py::array::forcecast> v0z,
            py::array_t<double, py::array::c_style | py::array::forcecast> v1x,
            py::array_t<double, py::array::c_style | py::array::forcecast> v1y,
            py::array_t<double, py::array::c_style | py::array::forcecast> v1z,
            py::array_t<double, py::array::c_style | py::array::forcecast> v2x,
            py::array_t<double, py::array::c_style | py::array::forcecast> v2y,
            py::array_t<double, py::array::c_style | py::array::forcecast> v2z
        ) {
            auto result = triangle_bvh_intersect_cpp(
                ox, oy, oz,
                dx, dy, dz,
                root_index,

                flat_triangle_indices.data(),

                node_aabb_min_x.data(),
                node_aabb_min_y.data(),
                node_aabb_min_z.data(),
                node_aabb_max_x.data(),
                node_aabb_max_y.data(),
                node_aabb_max_z.data(),

                node_left.data(),
                node_right.data(),
                node_start.data(),
                node_count.data(),
                node_is_leaf.data(),

                v0x.data(), v0y.data(), v0z.data(),
                v1x.data(), v1y.data(), v1z.data(),
                v2x.data(), v2y.data(), v2z.data(),

                static_cast<int>(node_left.size())
            );

            return py::make_tuple(result.first, result.second);
        }
    );

    m.def(
        "triangle_bvh_shadow_blocked_cpp",
        [](
            double ox, double oy, double oz,
            double dx, double dy, double dz,
            double max_distance,
            int root_index,

            py::array_t<int, py::array::c_style | py::array::forcecast> flat_triangle_indices,

            py::array_t<double, py::array::c_style | py::array::forcecast> node_aabb_min_x,
            py::array_t<double, py::array::c_style | py::array::forcecast> node_aabb_min_y,
            py::array_t<double, py::array::c_style | py::array::forcecast> node_aabb_min_z,
            py::array_t<double, py::array::c_style | py::array::forcecast> node_aabb_max_x,
            py::array_t<double, py::array::c_style | py::array::forcecast> node_aabb_max_y,
            py::array_t<double, py::array::c_style | py::array::forcecast> node_aabb_max_z,

            py::array_t<int, py::array::c_style | py::array::forcecast> node_left,
            py::array_t<int, py::array::c_style | py::array::forcecast> node_right,
            py::array_t<int, py::array::c_style | py::array::forcecast> node_start,
            py::array_t<int, py::array::c_style | py::array::forcecast> node_count,
            py::array_t<unsigned char, py::array::c_style | py::array::forcecast> node_is_leaf,

            py::array_t<double, py::array::c_style | py::array::forcecast> v0x,
            py::array_t<double, py::array::c_style | py::array::forcecast> v0y,
            py::array_t<double, py::array::c_style | py::array::forcecast> v0z,
            py::array_t<double, py::array::c_style | py::array::forcecast> v1x,
            py::array_t<double, py::array::c_style | py::array::forcecast> v1y,
            py::array_t<double, py::array::c_style | py::array::forcecast> v1z,
            py::array_t<double, py::array::c_style | py::array::forcecast> v2x,
            py::array_t<double, py::array::c_style | py::array::forcecast> v2y,
            py::array_t<double, py::array::c_style | py::array::forcecast> v2z
        ) {
            return triangle_bvh_shadow_blocked_cpp(
                ox, oy, oz,
                dx, dy, dz,
                max_distance,
                root_index,

                flat_triangle_indices.data(),

                node_aabb_min_x.data(),
                node_aabb_min_y.data(),
                node_aabb_min_z.data(),
                node_aabb_max_x.data(),
                node_aabb_max_y.data(),
                node_aabb_max_z.data(),

                node_left.data(),
                node_right.data(),
                node_start.data(),
                node_count.data(),
                node_is_leaf.data(),

                v0x.data(), v0y.data(), v0z.data(),
                v1x.data(), v1y.data(), v1z.data(),
                v2x.data(), v2y.data(), v2z.data(),

                static_cast<int>(node_left.size())
            );
        }
    );

    m.def(
        "render_triangle_image_cpp",
        [](
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

            py::array_t<int, py::array::c_style | py::array::forcecast> flat_triangle_indices,

            py::array_t<double, py::array::c_style | py::array::forcecast> node_aabb_min_x,
            py::array_t<double, py::array::c_style | py::array::forcecast> node_aabb_min_y,
            py::array_t<double, py::array::c_style | py::array::forcecast> node_aabb_min_z,
            py::array_t<double, py::array::c_style | py::array::forcecast> node_aabb_max_x,
            py::array_t<double, py::array::c_style | py::array::forcecast> node_aabb_max_y,
            py::array_t<double, py::array::c_style | py::array::forcecast> node_aabb_max_z,

            py::array_t<int, py::array::c_style | py::array::forcecast> node_left,
            py::array_t<int, py::array::c_style | py::array::forcecast> node_right,
            py::array_t<int, py::array::c_style | py::array::forcecast> node_start,
            py::array_t<int, py::array::c_style | py::array::forcecast> node_count,
            py::array_t<unsigned char, py::array::c_style | py::array::forcecast> node_is_leaf,

            py::array_t<double, py::array::c_style | py::array::forcecast> v0x,
            py::array_t<double, py::array::c_style | py::array::forcecast> v0y,
            py::array_t<double, py::array::c_style | py::array::forcecast> v0z,
            py::array_t<double, py::array::c_style | py::array::forcecast> v1x,
            py::array_t<double, py::array::c_style | py::array::forcecast> v1y,
            py::array_t<double, py::array::c_style | py::array::forcecast> v1z,
            py::array_t<double, py::array::c_style | py::array::forcecast> v2x,
            py::array_t<double, py::array::c_style | py::array::forcecast> v2y,
            py::array_t<double, py::array::c_style | py::array::forcecast> v2z,

            py::array_t<double, py::array::c_style | py::array::forcecast> normal_x,
            py::array_t<double, py::array::c_style | py::array::forcecast> normal_y,
            py::array_t<double, py::array::c_style | py::array::forcecast> normal_z,

            py::array_t<double, py::array::c_style | py::array::forcecast> color_r,
            py::array_t<double, py::array::c_style | py::array::forcecast> color_g,
            py::array_t<double, py::array::c_style | py::array::forcecast> color_b,

            py::array_t<double, py::array::c_style | py::array::forcecast> reflection,
            py::array_t<double, py::array::c_style | py::array::forcecast> transparency,
            py::array_t<double, py::array::c_style | py::array::forcecast> ior,

            py::array_t<double, py::array::c_style | py::array::forcecast> screen_x_values,
            py::array_t<double, py::array::c_style | py::array::forcecast> screen_y_values
        ) {
            std::vector<unsigned char> buffer = render_triangle_image_cpp(
                width,
                height,
                max_depth,
                num_threads,

                light_x,
                light_y,
                light_z,

                background_r,
                background_g,
                background_b,

                root_index,

                flat_triangle_indices.data(),

                node_aabb_min_x.data(),
                node_aabb_min_y.data(),
                node_aabb_min_z.data(),
                node_aabb_max_x.data(),
                node_aabb_max_y.data(),
                node_aabb_max_z.data(),

                node_left.data(),
                node_right.data(),
                node_start.data(),
                node_count.data(),
                node_is_leaf.data(),

                v0x.data(), v0y.data(), v0z.data(),
                v1x.data(), v1y.data(), v1z.data(),
                v2x.data(), v2y.data(), v2z.data(),

                normal_x.data(),
                normal_y.data(),
                normal_z.data(),

                color_r.data(),
                color_g.data(),
                color_b.data(),

                reflection.data(),
                transparency.data(),
                ior.data(),

                screen_x_values.data(),
                screen_y_values.data(),

                static_cast<int>(node_left.size())
            );

            return py::bytes(reinterpret_cast<const char*>(buffer.data()), buffer.size());
        }
    );
}