from setuptools import setup
from Cython.Build import cythonize
from setuptools.extension import Extension


extensions = [
    # you can also include all py files using sources=["*.py"]

    Extension(
        name="FileItem",
        sources=["FileItem.py"],  # Will ALSO be compiled
    ),

    Extension(
        name="WebFileBrowserAPI",  # This controls the name of the .pyd file (my_hello.pyd)
        sources=["api.py"],        # Your .pyx source file
        #compiler_directives={'language_level': "3"},
        #build_dir="build"
    )
]

setup(
    name="WebFileBrowserClient",
    ext_modules=cythonize(extensions),
    zip_safe=False,
)
