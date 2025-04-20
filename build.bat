@echo off
REM This build script assumes that MSVC and Windows SDK are installed
REM So that it can build Cython

call .venv/Scripts/activate

REM ===============================================
REM Prepare dependencies
REM ===============================================
pip install -r requirements.txt

REM ===============================================
REM Compile to pyd file
REM ===============================================
python setup.py build_ext
REM --inplace 
REM this is convenient if you want the compiled pyd file be at the same location as the py file

python setup.py install

REM ===============================================
REM COPY ALL PYD FILES TO PYD FOLDER
REM ===============================================

REM the block below is deprecated and it shouldn't run
if 1 == 0 (
set PYD_TARGET_DIR=pyd
set PYD_SOURCE_DIR=build

if not exist "%PYD_TARGET_DIR%" (
    echo Creating directory: %PYD_TARGET_DIR%
    mkdir "%PYD_TARGET_DIR%"
)

for /r "%PYD_SOURCE_DIR%" %%f in (*.pyd) do (
    echo Copying: %%f
    copy "%%f" "%PYD_TARGET_DIR%"
)
)

REM ===============================================
REM package to executable file
REM ===============================================
pyinstaller WebFileBrowserClient.spec
REM finishing off...
deactivate