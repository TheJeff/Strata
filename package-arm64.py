"""Package the self-built Windows-ARM64 Strata engine into the app's component folder."""
import hashlib, json, shutil
from pathlib import Path

BUILD = Path(r"C:\Projects\strata-arm\build-arm64")
CUDA = Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.4")
DEST = Path(r"C:\Users\imkoa\AppData\Local\Strata\components\engine\0.1.47-windows-arm64-cuda-cuda13")

FILES = [
    (BUILD / "strata.exe", "strata.exe"),
    (BUILD / "strata_kq.dll", "strata_kq.dll"),
    (Path(r"C:\Projects\strata-arm\build-vision\bin\strata-vision.exe"), "strata-vision.exe"),
    (CUDA / "bin/arm64/cublas64_13.dll", "cublas64_13.dll"),
    (CUDA / "bin/arm64/cublasLt64_13.dll", "cublasLt64_13.dll"),
]

DEST.mkdir(parents=True, exist_ok=True)
for src, name in FILES:
    if not src.exists():
        raise SystemExit(f"missing {src}")
    shutil.copy2(src, DEST / name)

build_record = {
    "version": "0.1.47",
    "source": "self-built arm64 (ferstar/gb10-022 d891f006 + windows-arm64 fixes)",
    "commit": "d891f006",
    "archs": [121],
    "ptx": False,
    "cuda": "13.4",
    "vision": "gpu-cuda13",
    "portable": False,
    "compiler": "clang-cl 19.1.5 (VS LLVM ARM64) + nvcc 13.4.59 host cl msvc 19.44",
}
(DEST / "BUILD.json").write_text(json.dumps(build_record, indent=1), encoding="utf-8")


def digest(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest(), path.stat().st_size


names = [n for _, n in FILES] + ["BUILD.json"]
files = []
for name in names:
    sha, size = digest(DEST / name)
    files.append({"path": name, "sha256": sha, "bytes": size})

manifest = {
    "schema_version": 2,
    "id": "strata-engine",
    "name": "strata-engine",
    "version": "0.1.47",
    "platform": "windows-arm64",
    "backend": "cuda",
    "archs": ["sm_121"],
    "min_driver": {"nvidia": "580.65"},
    "build_id": "d891f006+cuda13.4",
    "min_runtime": "0.1.47",
    "entrypoint": "strata.exe",
    "files": files,
    "signature": None,
    "notes": "Self-built on the RTX Spark N1X (GB10, sm_121) from the open ARM64 port PR #3622.",
}
(DEST / "engine-component.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
print("packaged into", DEST)
for f in files:
    print(f"  {f['path']:22s} {f['bytes']/1e6:8.1f} MB  {f['sha256'][:16]}")
