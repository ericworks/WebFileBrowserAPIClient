
When you compile `*.pyd` file,
it doesn't automatically compile all imports. 
it just tries to look for the module at runtime.


So the correct steps:

1. compile all necessary `.py` files in setup.py, in `extensions` array. e.g.:
   1. ```python
        from setuptools import setup
        from Cython.Build import cythonize
        from setuptools.extension import Extension
        
        
        extensions = [
        
            Extension(
                name="FileItem",
                sources=["FileItem.py"],  # Will ALSO be compiled
            ),
        
            Extension(
                name="HttpBrowserUploaderAPI",              # This controls the name of the .pyd file (my_hello.pyd)
                sources=["api.py"],        # Your .pyx source file
                #compiler_directives={'language_level': "3"},
                #build_dir="build"
            )
        ]
        
        setup(
            name="HttpBrowserUploader",
            ext_modules=cythonize(extensions),
            zip_safe=False,
        )
        ``` 
1. when running `pyinstaller` to package the executable, we need to ensure:
   1. external libraries used in compiled `pyd` file should be included in `hidden imports`
   1. imported compiled `pyd` file should be included in `binaries` array
   1. e.g. 
   ```python
     a = Analysis(
                ['main.py'],
                pathex=[],
                binaries=[
                    ('build/lib.win-amd64-cpython-313/FileItem.cp313-win_amd64.pyd', '.')
                ],
                hiddenimports=["requests"],
                datas=[],
                hookspath=[],
                hooksconfig={},
                runtime_hooks=[],
                excludes=[],
                noarchive=False,
                optimize=0,
         )
   ```

