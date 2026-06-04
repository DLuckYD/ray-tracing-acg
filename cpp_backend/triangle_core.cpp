#include "triangle_core.h"
#include <cmath>

double intersect_triangle_kernel_cpp(
    double ox, double oy, double oz,
    double dx, double dy, double dz,
    double v0x, double v0y, double v0z,
    double v1x, double v1y, double v1z,
    double v2x, double v2y, double v2z
) {
    const double epsilon = 1e-6;

    const double edge1x = v1x - v0x;
    const double edge1y = v1y - v0y;
    const double edge1z = v1z - v0z;

    const double edge2x = v2x - v0x;
    const double edge2y = v2y - v0y;
    const double edge2z = v2z - v0z;

    const double pvec_x = dy * edge2z - dz * edge2y;
    const double pvec_y = dz * edge2x - dx * edge2z;
    const double pvec_z = dx * edge2y - dy * edge2x;

    const double det = edge1x * pvec_x + edge1y * pvec_y + edge1z * pvec_z;

    if (det > -epsilon && det < epsilon) {
        return -1.0;
    }

    const double inv_det = 1.0 / det;

    const double tvec_x = ox - v0x;
    const double tvec_y = oy - v0y;
    const double tvec_z = oz - v0z;

    const double u = (tvec_x * pvec_x + tvec_y * pvec_y + tvec_z * pvec_z) * inv_det;
    if (u < 0.0 || u > 1.0) {
        return -1.0;
    }

    const double qvec_x = tvec_y * edge1z - tvec_z * edge1y;
    const double qvec_y = tvec_z * edge1x - tvec_x * edge1z;
    const double qvec_z = tvec_x * edge1y - tvec_y * edge1x;

    const double v = (dx * qvec_x + dy * qvec_y + dz * qvec_z) * inv_det;
    if (v < 0.0 || (u + v) > 1.0) {
        return -1.0;
    }

    const double t = (edge2x * qvec_x + edge2y * qvec_y + edge2z * qvec_z) * inv_det;
    if (t > epsilon) {
        return t;
    }

    return -1.0;
}