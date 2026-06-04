# instruction.md

## Project setup and run instructions

This document describes how to set up, build, and run the project on different systems after importing or cloning the repository.

---

## 1. General project steps

After importing or cloning the project:

1. Open the project folder in your IDE or terminal.
2. Create a local virtual environment.
3. Install Python dependencies.
4. Build the native `rt_core` extension for your platform.
5. Run the project using the project virtual environment, not the system Python.

---

## 2. Common Python environment setup

From the project root:

### Windows
```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel pybind11
```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel pybind11
```

---

## 3. Windows setup and build

### Requirements
- Python installed
- Visual Studio Build Tools or a working C++ compiler environment for Python extensions

### Build native extension
From the project root:

```bash
.venv\Scripts\activate
python setup.py build_ext --inplace
```

### Run the project
```bash
.venv\Scripts\activate
python main.py
```

### Notes
- On Windows, `setup.py` automatically enables the Windows OpenMP compiler flag.
- The build will generate the `rt_core` native module for Windows.
- Always run the project from the virtual environment.

---

## 4. macOS Apple Silicon setup and build

### Requirements
- Python installed
- Xcode Command Line Tools
- Homebrew
- `libomp` installed through Homebrew

### Install required macOS tools
```bash
xcode-select --install
brew install libomp
```

### Build native extension with OpenMP
From the project root:

```bash
source .venv/bin/activate
export RT_OPENMP=1
export RT_MAC_ARCH=arm64
python setup.py build_ext --inplace
```

### Optional: build without OpenMP for debugging
```bash
source .venv/bin/activate
export RT_OPENMP=0
export RT_MAC_ARCH=arm64
python setup.py build_ext --inplace
```

### Verify native backend import
```bash
python -c "import rt_core; print(rt_core.hello_backend())"
```

Expected result:
```text
rt_core loaded successfully
```

### Run the project
```bash
source .venv/bin/activate
python main.py
```

### Important macOS notes
- Use the project virtual environment interpreter, not the system Python.
- In PyCharm, select:
  - `.../project/.venv/bin/python`
- The project is configured to build correctly on Apple Silicon with `libomp`.
- `RT_MAC_ARCH=arm64` is recommended.
- `RT_MAC_ARCH=universal2` should only be used if you explicitly need a universal build.

---

## 5. Linux setup and build

### Requirements
- Python installed
- C++ compiler installed
- OpenMP-capable compiler toolchain

### Example package prerequisites
Depending on distribution, install:
- `build-essential`
- `python3-dev`
- `libomp-dev` or equivalent if needed

### Build native extension
```bash
source .venv/bin/activate
python setup.py build_ext --inplace
```

### Run the project
```bash
source .venv/bin/activate
python main.py
```

### Notes
- On Linux, `setup.py` automatically uses `-fopenmp` when OpenMP is enabled.

---

## 6. Platform-aware build controls

The project `setup.py` supports optional environment variables:

### Enable or disable OpenMP
```bash
export RT_OPENMP=1
```
or
```bash
export RT_OPENMP=0
```

### Select macOS architecture mode
```bash
export RT_MAC_ARCH=arm64
```
or
```bash
export RT_MAC_ARCH=universal2
```

Recommended defaults:
- Windows: no extra env variables needed
- macOS Apple Silicon: `RT_OPENMP=1`, `RT_MAC_ARCH=arm64`
- Linux: no extra env variables needed unless debugging OpenMP

---

## 7. Quick backend verification inside Python

You can check whether the C++ backend is available:

```python
import logic_scripts.config as config
from logic_scripts.parallel import CPP_BACKEND_AVAILABLE

print("CPP_BACKEND_AVAILABLE:", CPP_BACKEND_AVAILABLE)
print("backend_mode:", config.backend_mode)
print("use_triangle_backend:", config.use_triangle_backend)
```

For the fast native path, you want:
- `CPP_BACKEND_AVAILABLE: True`
- `config.backend_mode = "cpp"`
- `config.use_triangle_backend = True`

---

## 8. Typical run configuration

The optimized native CPU renderer expects the following in `main.py` or runtime config:

```python
config.backend_mode = "cpp"
config.use_triangle_backend = True
```

This enables:
- native C++ render core
- OpenMP full-image rendering path
- triangle backend for optimized rendering

---

## 9. Troubleshooting

### Problem: `No module named 'rt_core'`
Cause:
- native extension was not built
- wrong Python interpreter is used
- build failed for the current platform

Fix:
1. Activate `.venv`
2. Rebuild with `python setup.py build_ext --inplace`
3. Verify import with:
   ```bash
   python -c "import rt_core; print(rt_core.hello_backend())"
   ```

### Problem: macOS build fails with `unsupported option '-fopenmp'`
Cause:
- macOS Apple clang does not accept plain `-fopenmp`

Fix:
- use the provided platform-aware `setup.py`
- install `libomp`
- rebuild with:
  ```bash
  export RT_OPENMP=1
  export RT_MAC_ARCH=arm64
  python setup.py build_ext --inplace
  ```

### Problem: project runs but is much slower than expected
Cause:
- C++ backend is unavailable and the project uses fallback path

Fix:
- verify `CPP_BACKEND_AVAILABLE`
- verify `rt_core` imports successfully
- verify `backend_mode == "cpp"`

---

## 10. Recommended workflow

### For development
1. Activate `.venv`
2. Rebuild native module after backend changes
3. Run benchmark scene
4. Check generated logs and summaries

### For PyCharm
1. Open project
2. Set interpreter to project `.venv`
3. Rebuild `rt_core` after changing C++ files
4. Run `main.py`

---

## 11. Summary

### Windows
- create `.venv`
- install Python packages
- build with `python setup.py build_ext --inplace`
- run with `.venv`

### macOS Apple Silicon
- create `.venv`
- install Python packages
- install `libomp`
- build with `RT_OPENMP=1 RT_MAC_ARCH=arm64`
- verify `rt_core`
- run with `.venv`

### Linux
- create `.venv`
- install Python packages
- build with `python setup.py build_ext --inplace`
- run with `.venv`
