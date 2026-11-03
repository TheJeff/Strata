# Strata engine — Windows ARM64 (RTX Spark N1X / GB10) self-build

Status: **working, engine 0.1.55** (built 2026-11-02 from upstream `main` c62d5e3a), plus the
DeepSeek-V4.1 engine `strata-dsv41` 0.1.55 for Windows-ARM64. The arm64 engine loads IQ3_S, serves
OpenAI-compatible requests on the Spark, and the app's Control recognises both packages.

## Why this exists

Upstream publishes prebuilt engines only for `windows-x86_64`, `linux-x86_64` and `macos-arm64`
(the Linux ARM64 / DGX Spark build has its own feed, `strata-feed-linux-aarch64.json`). There is no
`windows-arm64` package in any feed, and the desktop app installs prebuilt packages only and never
compiles, so on Windows-ARM64 it reports "no engine for this PC".

`windows-arm64` appears nowhere in upstream's `CMakeLists.txt` or `strata_control/targets.py`, so
every rebuild is this fork's port. PR #3622 (`ferstar/gb10-022`) was the original ARM64 port; it was
**closed unmerged** on 2026-10-28 and upstream rewrote ARM64 support for Linux only. Our branch keeps
the local fixes on top of upstream `main`.

## What was built (0.1.55, 2026-11-02)

- Source: upstream `main` `c62d5e3a` (0.1.55) + the local fixes below, branch `windows-arm64-0.1.55`
  in `C:\Projects\strata-arm`. ggml comes from the vendored llama.cpp at the pinned commit
  `3cf03257f219afbe7334045ff7c6a06ac68c627d` (`third_party/llama.cpp`, gitignored).
- Toolchain: CUDA Toolkit **13.4.1 Windows-ARM64** (`C:\Program Files\NVIDIA GPU Computing
  Toolkit\CUDA\v13.4`, arm64 nvcc 13.4.59), clang-cl 19.1.5 (VS 2022 BuildTools LLVM ARM64),
  MSVC 14.44 arm64 `cl.exe` as the NVCC host compiler, CMake 4.4.4 + Ninja from
  `C:\Projects\strata-tools`.
- Build flags mirror upstream's Spark recipe (`spark/build_engine.sh`): `STRATA_NATIVE_EXPERTS=ON`,
  `STRATA_PORTABLE=ON`, `STRATA_Q6K_EXPERTS=ON`, `STRATA_MMQ_KQUANTS=ON`, `STRATA_BUILD_DSV41=ON`,
  `CMAKE_CUDA_ARCHITECTURES=121-real;121-virtual`. `STRATA_PORTABLE` on arm64 sets ggml-cpu to
  `-march=armv8.2-a+dotprod+fp16+i8mm`, which configure detects on the GB10 (dotprod, i8mm, fp16
  all present), and switches the MSVC runtime to static.
- Products: `strata.exe` (104.4 MB, ARM64, sm_121 + PTX 121), `strata_kq.dll` (12.5 MB),
  `strata-dsv41.exe` (42.2 MB), `strata-vision.exe` (56.6 MB).

## Local fixes needed on Windows/ARM64 (0.1.55 tree)

1. `src/kernels/cpu/expert_layout.cpp` — the `<intrin.h>`/`<immintrin.h>` include was gated on
   `_MSC_VER` alone; clang-cl defines that on ARM64 too, so the x86 headers exploded. Gate is now
   `_MSC_VER && (_M_X64 || _M_IX86)`.
2. `CMakeLists.txt` — clang 19 (VS LLVM ARM64) mis-emits a return-block address in the SEH epilogue at
   `/O2` ("assembler label '' can not be undefined"). TUs that hit it build `/O1`: `src/core/layer.cpp`,
   `src/core/verify.cpp` and (new in 0.1.55) `src/prefill/prefill.cpp`.
3. `src/dsv41/ds4_pool.hpp` — `cpu_relax()` used `_mm_pause()` under `_MSC_VER`; on ARM64 it now uses
   `__yield()`, and does nothing in the CUDA device pass.
4. `src/dsv41/ds4_gg_cpu.cpp` — `amd_family()` called `__cpuid()` under `_MSC_VER`; on ARM64 that
   symbol does not exist (link error). The CPUID branch is now x86-only, so ARM64 takes the
   "no family" path.
5. `strata_control/targets.py` + `strata_control/feed.py` — `windows-arm64` added under `cuda` in
   `BACKEND_MATRIX` and to `PLATFORMS`, or Control refuses the package.

## Build commands

`configure-arm64-0155.bat`, `build-arm64-0155.bat` (targets `strata strata_kq strata-dsv41`) and
`vision-arm64-0155.bat`, all in `C:\Projects\strata-arm`. Each calls `vcvarsall.bat arm64`, puts the
VS LLVM ARM64 bin on PATH and sets `CUDA_PATH`. Configure took 20 s, the engine build ~25 min
(178 steps) with `--parallel 20`, vision ~4 min.

## Package + install

Use the repository's own `packaging/package_engine.py` (same tool upstream's release scripts use),
not a hand-written manifest:

    python packaging/package_engine.py --src out-0155/engine --backend cuda --version 0.1.55 \
      --out "C:/Users/imkoa/AppData/Local/Strata/components/engine" \
      --arch sm_121 --arch compute_121 --min-driver nvidia=580.65 --variant cuda13 \
      --platform windows-arm64 --build-id <id> --require-dsv41 \
      --search "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.4/bin/arm64"

    python packaging/package_engine.py --src out-0155/dsv41 --backend cuda --version 0.1.55 \
      --out "C:/Users/imkoa/AppData/Local/Strata/engine-dsv41" \
      --arch sm_121 --arch compute_121 --min-driver nvidia=580.65 --variant cuda13 \
      --platform windows-arm64 --build-id <id> --entrypoint strata-dsv41.exe \
      --search "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.4/bin/arm64"

It bundles the arm64 `cublas64_13.dll` / `cublasLt64_13.dll` from the toolkit and writes
`engine-component.json` (schema 2, hashes for every file, unsigned `signature`). `BUILD.json` must
carry `vision_archs` (stamped with `--stamp-vision out-0155/engine --vision-archs 121`) or packaging
refuses the picture reader.

Installed:

    C:\Users\imkoa\AppData\Local\Strata\components\engine\0.1.55-windows-arm64-cuda-cuda13   (413 MiB)
    C:\Users\imkoa\AppData\Local\Strata\engine-dsv41\0.1.55-windows-arm64-cuda-cuda13       (248 MiB)

`packaging/package_engine.py --verify <folder> --require-dsv41` passes on both, and Control's own
code reports `usable: true`, engine 0.1.55 windows-arm64, `dsv41_engine.find()` returns the installed
`strata-dsv41.exe`, and `dsv41_engine._test_start()` returns
`strata-dsv41 0.1.55 build c62d5e3a1`.

## Measured on this box (2026-11-02)

Same config the app writes (IQ3_S, 256K context, `--resident-experts`, MTP `--spec 4`, int8 KV,
46.84 GiB expert cache in VRAM), served through Control's `serve/server.py`, greedy, identical
prompts, one load per engine, cold runs:

| engine | decode tok/s (120 out) | prefill tok/s (3,903-token prompt) |
|---|---|---|
| 0.1.47 (previous build) | 60.5, 63.8 | 1,331 |
| 0.1.55 (this build) | 65.7, 67.9 | 1,486 |

Decode +6 to +8%, prefill +11.6% (1.16x). Upstream measured 1.20x prompt speed for the
`STRATA_SM121_PERF` settings on a Spark on Linux; we get less here, measured, not assumed. Warm
repeats of the same prompt hit the prompt cache and are not comparable (0.1 s TTFT).

## DeepSeek-V4.1 engine (strata-dsv41)

The 0.1.55 `strata-dsv41.exe` builds and starts on Windows-ARM64, and its package is installed beside
the Qwen engine where Control looks for it (`<data>/engine-dsv41/`). It has **not run a model yet**:
there is no DeepSeek GGUF set on this box. The offered sets are 239 GB (IQ1_M), 257 GB (IQ2_XXS) and
274 GB (IQ2_XS); C: had 450 GB free after the build. DeepSeek's own AVX2/AVX-512 expert rows do not
exist on ARM (they are `__x86_64__`-gated), so the CPU lane runs ggml-cpu's NEON dots — same answers,
unknown speed. Upstream's DGX Spark runs (Linux) report 15 to 26 tok/s decode on UD-IQ1_S.

## DeepSeek Coder set (IST-DASLab's Coder GGUF, added 2026-11-02)

`ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-Coder-GGUF` is a DeepSeek-V4.1-Flash set with half of every layer's
384 experts pruned (192 kept), IQ2_XXS, for code and agent work: 72.1 GB of model in five shards plus the 110.6 GB
Engram (183.7 GB, revision `54229d38`). Control 0.1.55 knows only the non-Coder ISTA-DASLab repo and Unsloth's UD
sets, and it matches sets by exact file name + size + SHA-256, so a folder of these files got
"this model type is not supported by the Strata engine / the file has no usable tokenizer / this is not a model size
Strata knows" (the local-GGUF checker in `strata_control/models.py` also only accepts Qwen's `qwen4exp` arch — the
DeepSeek path is a separate one).

Taught Control the set with `patch-control-coder.py` (idempotent, run it after every Control update):

    <control>/python/python.exe C:/Projects/strata-arm/patch-control-coder.py

It adds the repository revision and its five shard pins to `setup.py` (`HF_REVISIONS`, `REPO_PINS`,
`DSV41_CODER_FILES`, `DSV41_ALL_FILES`), a size `IST-DAS-Coder-2.00bpw` to the DeepSeek family
(`layout: six`, `meta_from_set: True`, no shipped expert profile), the fit numbers to
`strata_control/dsv41_fit.py`, the pins to `strata_control/dsv41_sets.py` (so the app's "I already have the model"
preview recognises the folder, including a Hugging Face snapshot whose shards sit in `IQ2_XXS/` and whose Engram is
one level up), and the `models.py` fallback that looks one folder deeper.

Verified on this box:

- `models.plan_import(<snapshot>)` -> no issues, "This is DeepSeek-V4.1-Flash, IST-DAS Coder 2.00 bpw: all 5 model
  files are here, and the n-gram table", `model_dir` = the `IQ2_XXS` folder.
- `strata launch --family deepseek41 --model IST-DAS-Coder-2.00bpw --model-path <snapshot> --plan` -> nothing to
  download, fits: 15,360 of 15,360 experts (66 GB) on the card.
- Packed with `tools/dsv41/pack_gguf.py` (24,542 tensors, Engram 2 layers x 24 hash columns, vision tower) and ran
  `strata-dsv41` 0.1.55: 66.23 GB of experts in VRAM with 29.4 GB VRAM left, prompt 52 tokens at 27.2 tok/s,
  decode 150 tokens at 21.7 tok/s, Engram reads 4.1 ms/token (`--experts 6`). The answer was coherent reasoning
  text, cut by the 150-token limit.

Launch it from the Terminal (the files stay where they are):

    strata launch --family deepseek41 --model ist-das-coder-2.00bpw --model-path "<snapshot folder>" --yes

## Installing DeepSeek from the app (fixed 2026-11-02)

Two more things stopped the app's install on this box, both now patched by `patch-control-coder.py`:

1. **Setup crashed at step 1/7** with `ValueError: invalid literal for int() with base 10: '[N/A]'` at
   `setup.py:1687 sm60_card`. The RTX Spark reports two devices to `nvidia-smi`: the GB10 graphics card
   (`compute_cap` 12.1) and an **NPU** whose `compute_cap` is `[N/A]`. `gpus()` kept the NPU's arch as the string
   `"[N/A]"` and `old_gpus_opt_in` ran `int()` on it. Fixed by normalising a non-numeric capability to `"0"` when the
   card list is built and by making `sm60_card` / `maxwell_card` return False for it.
2. **Step 4/7 "DeepSeek's engine is not available for this computer yet"**: setup looks for the DeepSeek engine in
   `<home>/engine-dsv41` (the app's `STRATA_INSTALL_DIR`, i.e. `Strata\install`) or, without that variable, in the
   Control folder (`Programs\Strata\control\engine-dsv41`); the feed has no `windows-arm64` DeepSeek package, so it
   found nothing. The self-built package is now copied into both places as well as `Strata\engine-dsv41` (three copies
   of 248 MB; the different code paths look in different folders). The app's install then verified the existing
   Hugging Face files by hash instead of downloading them.

Note that the app's own "Download & load" for a DeepSeek size installs into `models\deepseek-v4.1-flash-<size>` and
downloads whatever is not there; to use files you already have, go through "Use a local GGUF…" (which passes the
folder as `--gguf-dir`), or call `strata_install` with `gguf_dir`.

Three more setup problems met while installing the Coder set (all patched in `patch-control-coder.py`):

- `--gguf-dir` + a data folder elsewhere: the pack is built in `<data>\packs\<tag>` with paths relative to it, and the
  check afterwards resolves them from the model folder, so a pack built for files left in the Hugging Face cache came
  out "not complete". Putting the model files in the app's own folder (hardlinks into `models\models\<tag>` and
  `models\models\deepseek-v4.1-flash-shared`) makes setup verify them and build a pack that resolves.
- The Engram's accepted alternate hash (the converted 2026-10-27 file) was checked *after* the repair step, so a
  perfectly good converted Engram was re-downloaded (110 GB). The patch accepts `also` before repairing.
- `--gpus 0` is refused for a single card ("--gpus takes two or more different GPUs"); use `--gpu 0`.

Also: do not hardlink a model file into a folder setup manages and then let setup repair it - the repair writes through
the link and changes the Hugging Face blob it points at (seen with the Engram; the blob had to be deleted and fetched
again).

## After every Control update: re-apply the platform patch

The app and Terminal ship their own Control, and a Control update **overwrites**
`strata_control/targets.py` and `feed.py`, dropping this fork's platform entries and leaving Control
refusing the packages ("No engine for this PC", `usable: false`). Observed on the 2026-11-02 update to
Control 0.1.55. Re-apply both edits in the installed copy
(`C:\Users\imkoa\AppData\Local\Programs\Strata\control\strata_control\`):

- `targets.py`: `"cuda": ("windows-x86_64", "windows-arm64", "linux-x86_64", "linux-aarch64")`
- `feed.py`: add `"windows-arm64"` to `PLATFORMS`

Check with the bundled interpreter:

    cd /c/Users/imkoa/AppData/Local/Programs/Strata/control
    ./python/python.exe -c "import sys; sys.path.insert(0,'.'); from strata_control import engine_component as ec; s=ec.status(); print(s['usable'], (s['engine'] or {}).get('version'), s['notice'])"

Expect `True 0.1.55 None`. Restart the app afterwards; it caches the pre-patch state.

## Known gaps

- Both packages are unsigned (`signature: null`); accepted, since signature checking is not enforced
  by default. `dsv41_engine.install_package` (the manual "give me a package file" path) *does* require
  a signature, so hand-installs of these packages have to be folder copies, not that path.
- `Settings → Update engine` consults the signed feed, which has no `windows-arm64` entry, so it will
  not replace these packages; rebuild and re-run the packaging commands after pulling a newer `main`.
- The `/O1` workaround on three TUs costs some speed versus a clean `/O2` build; a newer clang (or
  MSVC for those files) would recover it.
- `strata-vision.exe` is built and packaged, but picture reading has not been tested on ARM64; turn
  "Read pictures" off if it misbehaves.
- The old 0.1.47 arm64 package is left in the component folder for rollback; Control picks the newest.
