from pathlib import Path
from setuptools import setup, Extension
import pybind11
import os

cpp_backend = Path(__file__).parent / "cpp_backend"

if os.name == "nt":
    extra_compile_args = ["/std:c++17", "/openmp"]
    extra_link_args = []
else:
    extra_compile_args = ["-std=c++17", "-fopenmp"]
    extra_link_args = ["-fopenmp"]

ext_modules = [
    Extension(
        "rt_core",
        sources=[
            str(cpp_backend / "bindings.cpp"),
            str(cpp_backend / "triangle_core.cpp"),
            str(cpp_backend / "bvh_core.cpp"),
            str(cpp_backend / "render_core.cpp"),
        ],
        include_dirs=[
            pybind11.get_include(),
            str(cpp_backend),
        ],
        language="c++",
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    )
]

setup(
    name="rt_core",
    version="0.2.0",
    ext_modules=ext_modules,
)