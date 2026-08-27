# setup.py
from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy

extensions = [
    Extension("quant_execution_engine.ring_buffer_c", ["quant_execution_engine/ring_buffer.pyx"]),
    Extension("quant_execution_engine.profiler_c", ["quant_execution_engine/profiler.pyx"])
]

setup(
    ext_modules=cythonize(
        extensions, 
        compiler_directives={'language_level': "3"}
    ),
    include_dirs=[numpy.get_include()] # Required for C-API numpy headers
)