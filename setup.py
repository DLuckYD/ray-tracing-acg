from pathlib import Path
from setuptools import setup, Extension
import pybind11

cpp_backend = Path(__file__).parent / "cpp_backend"

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
        extra_compile_args=["/std:c++17"] if __import__("os").name == "nt" else ["-std=c++17"],
    )
]

setup(
    name="rt_core",
    version="0.1.0",
    ext_modules=ext_modules,
)