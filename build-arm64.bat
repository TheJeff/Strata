@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" arm64
if errorlevel 1 (echo VCVARS FAILED & exit /b 1)
set "CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.4"
set "CUDA_PATH_V13_4=%CUDA_PATH%"
set "PATH=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\Llvm\ARM64\bin;%PATH%"

"C:\Projects\strata-tools\Scripts\cmake.exe" --build C:\Projects\strata-arm\build-arm64 --target strata --parallel 20 -- -k 0
exit /b %errorlevel%
