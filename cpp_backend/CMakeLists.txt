cmake_minimum_required(VERSION 3.18)
project(rt_core LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(rt_core
    bindings.cpp
    triangle_core.cpp
    bvh_core.cpp
)