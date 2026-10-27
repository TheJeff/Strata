# Strata engine — Windows ARM64 (RTX Spark N1X / GB10) self-build

Status: **working**. The arm64 engine builds, loads IQ3_S, serves OpenAI-compatible
requests on the Spark, and the desktop app's Control now recognises it as the engine
for this PC.

## Why this exists

The upstream project publishes prebuilt engines only for `windows-x86_64`,
`linux-x86_64` and `macos-arm64` — there is no aarch64 package at all, for Windows or
Linux. The desktop app installs prebuilt packages only and never compiles, so on
Windows-ARM64 it reported "no engine for this PC". DGX Spark users get around it by
compiling from source on Linux with the community ARM64 port.

Upstream references: PR #3622 (`ferstar/gb10-022`, the open ARM64 port onto 0.2.x),
PR #2063 (`sykuang/windows-arm64-rtx-spark`, the Windows-ARM64 build path — closed in
the 0.2.0-beta tracker reset, not rejected), PR #2419 (DGX Spark validation).

## What was built

- Source: `Niko1221/Strata` @ `main` 011c9e60 (0.1.47) + `ferstar/gb10-022` d891f006
  (PR #3622), plus the local Windows fixes listed below.
- Checkout: `C:\Projects\strata-arm` (branch `ferstar-gb10-022`); the pinned llama.cpp/ggml
  source it builds against is vendored at `C:\Projects\strata-arm\third_party\llama.cpp`.
  The cmake/ninja venv lives at `C:\Projects\strata-tools` (its launchers embed absolute
  paths, so it must stay there).
- Toolchain: CUDA Toolkit **13.4.1 Windows-ARM64** (installed at
  `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.4`, arm64 nvcc 13.4.59),
  clang-cl 19.1.5 (VS 2022 BuildTools LLVM ARM64), MSVC 14.44 arm64 cl.exe as the
  NVCC host compiler, CMake 4.4.4 + Ninja, ggml from llama.cpp `3cf03257`.
- Result: `strata.exe` (75.8 MB, ARM64, sm_121), `strata_kq.dll` (12.4 MB).

## Local fixes on top of the ARM64 PR (all needed on Windows/ARM64)

1. `src/kernels/cpu/expert_layout.cpp` — the `<immintrin.h>` include was gated only on
   `_MSC_VER`; clang-cl defines that on ARM64 too, so the header exploded. Guard is now
   `_MSC_VER && (_M_X64 || _M_IX86)`.
2. `CMakeLists.txt` — clang 19 (VS LLVM) mis-emits a return-block address in the SEH
   epilogue at `/O2` for `src/core/layer.cpp` and `src/core/verify.cpp`
   (`error: assembler label '' can not be undefined`, from `add x0, x0, .LBB…`).
   Those two TUs are compiled `/O1`; everything else stays `/O2`.
3. `strata_control/targets.py` — `BACKEND_MATRIX` did not list `windows-arm64` under
   `cuda`, so even a perfect package was refused. Added it (also patched in the
   installed control at
   `C:\Users\imkoa\AppData\Local\Programs\Strata\control\strata_control\targets.py`).

## Build commands

`C:\Projects\strata-arm\configure-arm64.bat` then `build-arm64.bat` — both call
`vcvarsall.bat arm64`, put the VS LLVM ARM64 bin on PATH, set `CUDA_PATH`, and drive
CMake/Ninja with clang-cl + nvcc(host cl) + `CMAKE_CUDA_ARCHITECTURES=121` +
`STRATA_GGML_DIR=C:/Projects/llama.cpp-3cf03257…`. Roughly 4 minutes on this box.

## Package + install

`package-arm64.py` copies the binary, `strata_kq.dll` and the arm64 `cublas`/
`cublasLt` DLLs from the toolkit into

    C:\Users\imkoa\AppData\Local\Strata\components\engine\0.1.47-windows-arm64-cuda-cuda13

and writes `BUILD.json` + `engine-component.json` (schema 2, `platform:
windows-arm64`, `backend: cuda`, `archs: [sm_121]`, SHA-256 for every file).
Control's own check (`strata_control.engine_component.status()`) reports
`usable: true`, backend `cuda` (detected via nvidia-smi), platform `windows-arm64`.

## Measured on this box (2026-10-22)

Qwen3.8-Flash-Next IQ3_S (GSQ-RCO), 256K context, `--resident-experts`, MTP on,
greedy, 120 max tokens:

- decode 61.9 tok/s, prompt 94.1 tok/s on a 61-token request
- MTP draft 38/44 accepted
- 46.84 GiB expert cache in VRAM, 47.2 GiB VRAM free with everything loaded

That is in line with the DGX Spark reference runs in PR #2419 (58.8–66 tok/s).

## Known gaps

- `strata-vision.exe` (the picture reader) is a separate CMake project; see
  `vision-arm64.bat`. Until it is packaged the app keeps "Read pictures" off.
- The package is unsigned (`signature: null`) — accepted, since signature checking is
  not enforced by default.
- `Settings → Update engine` consults the signed feed, which has no `windows-arm64`
  entry, so it will not replace this package; rebuild and re-run the packaging script
  after pulling a newer `main`.
- The `/O1` workaround for the two TUs costs some decode speed versus a clean `/O2`
  build; a newer clang (or MSVC for those files) would recover it.
