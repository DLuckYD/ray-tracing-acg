from pathlib import Path
from setuptools import setup, Extension
import pybind11
import os
import sys
import platform

cpp_backend = Path(__file__).parent / "cpp_backend"

SYSTEM = sys.platform
MACHINE = platform.machine().lower()

# Optional environment overrides
# RT_OPENMP=1 / 0
# RT_MAC_ARCH=arm64 / universal2
env_openmp = os.environ.get("RT_OPENMP")
env_mac_arch = os.environ.get("RT_MAC_ARCH", "arm64").lower()

if env_openmp is None:
    USE_OPENMP = True
else:
    USE_OPENMP = env_openmp == "1"

extra_compile_args = []
extra_link_args = []
define_macros = []

# ---------- macOS ----------
if SYSTEM == "darwin":
    libomp_prefix = "/opt/homebrew/opt/libomp"

    # By default on Apple Silicon we force arm64 build
    # because Homebrew libomp is usually arm64 only.
    if env_mac_arch == "arm64":
        os.environ["ARCHFLAGS"] = "-arch arm64"
    elif env_mac_arch == "universal2":
        os.environ["ARCHFLAGS"] = "-arch arm64 -arch x86_64"

    extra_compile_args = ["-std=c++17"]

    if USE_OPENMP:
        extra_compile_args += [
            "-Xpreprocessor",
            "-fopenmp",
            f"-I{libomp_prefix}/include",
        ]
        extra_link_args += [
            f"-L{libomp_prefix}/lib",
            "-lomp",
        ]

# ---------- Windows ----------
elif os.name == "nt":
    extra_compile_args = ["/std:c++17"]
    if USE_OPENMP:
        extra_compile_args += ["/openmp"]

# ---------- Linux / other Unix ----------
else:
    extra_compile_args = ["-std=c++17"]
    if USE_OPENMP:
        extra_compile_args += ["-fopenmp"]
        extra_link_args += ["-fopenmp"]

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
        define_macros=define_macros,
    )
]

setup(
    name="rt_core",
    version="0.2.0",
    ext_modules=ext_modules,
)