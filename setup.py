import os
import sys
import sysconfig
from distutils.ccompiler import get_default_compiler

import numpy as np
from Cython.Build import cythonize
from setuptools import Extension, setup
from wheel.bdist_wheel import bdist_wheel

from setupext import check_for_openmp

if check_for_openmp():
    omp_args = ["-fopenmp"]
else:
    omp_args = None

cpp11_args = ["-std=c++11" if get_default_compiler() != "msvc" else "/std:c++11"]

if os.name == "nt":
    std_libs = []
else:
    std_libs = ["m"]


# restrict LIMITED_API usage:
# - require an env var EWAH_BOOL_UTILS_LIMITED_API=1
# - compiling with Python 3.10 doesn't work (as of Cython 3.1.1)
# - LIMITED_API is not compatible with free-threading (as of CPython 3.14)
USE_PY_LIMITED_API = (
    os.environ.get("EWAH_BOOL_UTILS_LIMITED_API") == "1"
    and sys.version_info >= (3, 11)
    and not sysconfig.get_config_var("Py_GIL_DISABLED")
)
ABI3_TARGET_VERSION = "".join(str(_) for _ in sys.version_info[:2])
ABI3_TARGET_HEX = hex(sys.hexversion & 0xFFFF00F0)


class bdist_wheel_abi3(bdist_wheel):
    def get_tag(self):
        python, abi, plat = super().get_tag()

        if python.startswith("cp") and USE_PY_LIMITED_API:
            return f"cp{ABI3_TARGET_VERSION}", "abi3", plat

        return python, abi, plat


define_macros = [
    ("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION"),
    # keep in sync with runtime requirements (pyproject.toml)
    ("NPY_TARGET_VERSION", "NPY_1_19_API_VERSION"),
]
if USE_PY_LIMITED_API:
    define_macros.append(("Py_LIMITED_API", ABI3_TARGET_HEX))

extensions = [
    Extension(
        "ewah_bool_utils.ewah_bool_wrap",
        ["ewah_bool_utils/ewah_bool_wrap.pyx"],
        define_macros=define_macros,
        include_dirs=["ewah_bool_utils", "ewah_bool_utils/cpp", np.get_include()],
        language="c++",
        extra_compile_args=cpp11_args,
        py_limited_api=USE_PY_LIMITED_API,
    ),
    Extension(
        "ewah_bool_utils.morton_utils",
        ["ewah_bool_utils/morton_utils.pyx"],
        define_macros=define_macros,
        extra_compile_args=omp_args,
        extra_link_args=omp_args,
        libraries=std_libs,
        include_dirs=[np.get_include()],
        py_limited_api=USE_PY_LIMITED_API,
    ),
    Extension(
        "ewah_bool_utils._testing",
        ["ewah_bool_utils/_testing.pyx"],
        include_dirs=["ewah_bool_utils", "ewah_bool_utils/cpp", np.get_include()],
        define_macros=define_macros,
        extra_compile_args=["-O3"],
        language="c++",
        py_limited_api=USE_PY_LIMITED_API,
    ),
]

setup(
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": 3},
    ),
    cmdclass={"bdist_wheel": bdist_wheel_abi3},
)
