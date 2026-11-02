#!/usr/bin/env python3
"""Teach the installed Strata Control about ISTA-DASLab's DeepSeek Coder set (idempotent).

The Coder set (ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-Coder-GGUF, 183.7 GB: five IQ2_XXS shards and the
Engram) is a DeepSeek-V4.1-Flash set with 192 of 384 experts a layer.  Control 0.1.55 knows only the non-Coder
ISTA-DASLab sets and Unsloth's UD sets, matched by exact file name + size + SHA-256, so the app answers
"This model type isn't supported by the Strata engine" for a folder of these files.

Run it after every Control update (an update replaces the files it edits):

    <control>/python/python.exe C:/Projects/strata-arm/patch-control-coder.py

It prints what it changed and what it skipped, and exits non-zero if an anchor is missing (a Control version that
moved the code).  Nothing is downloaded; the model files stay where they are.
"""
from __future__ import annotations

import sys
from pathlib import Path

CONTROL = Path(r"C:/Users/imkoa/AppData/Local/Programs/Strata/control")

SETUP = CONTROL / "setup.py"
SETS = CONTROL / "strata_control" / "dsv41_sets.py"
FIT = CONTROL / "strata_control" / "dsv41_fit.py"
MODELS = CONTROL / "strata_control" / "models.py"

REVISION = "54229d38d588a66d1c6cff08af7b281b9326c656"
CODER_BLOCK = '''DSV41_CODER_REPO = "ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-Coder-GGUF"
DSV41_CODER_SHARD = "DeepSeek-V4.1-Flash-1017-GSQ-RCO-Coder-IQ2_XXS-{i:05d}-of-00006.gguf"
DSV41_CODER_FILES = {
    "DeepSeek-V4.1-Flash-1017-GSQ-RCO-Coder-IQ2_XXS-00001-of-00006.gguf": (5780704, "108e63d27240da2d99846250727a7b282e05a7fdf2448435e81904b9a98d8a4a"),
    "DeepSeek-V4.1-Flash-1017-GSQ-RCO-Coder-IQ2_XXS-00002-of-00006.gguf": (19776064960, "75079999eb3a492ad695f3466fd6a068a1cf1920980eac1c7f51406363fadf7a"),
    "DeepSeek-V4.1-Flash-1017-GSQ-RCO-Coder-IQ2_XXS-00003-of-00006.gguf": (19939989696, "ea964e525922f36d3b984299c1a5bb8d896f50b9c2942364cd221c37863331f2"),
    "DeepSeek-V4.1-Flash-1017-GSQ-RCO-Coder-IQ2_XXS-00004-of-00006.gguf": (19682533472, "2d95806d186597cb0ea32635c92f0b66a9a6afae1a399ff74b13aebaa4ac7a52"),
    "DeepSeek-V4.1-Flash-1017-GSQ-RCO-Coder-IQ2_XXS-00005-of-00006.gguf": (12719198624, "3665b48c3bd46330780caf286ee40a087ac11499e5b7df8c943b098d10f426d4"),
}
'''

CODER_MODEL = '''    "IST-DAS-Coder-2.00bpw": {
        "label": "IST-DAS Coder 2.00 bpw",
        "about": "IST-DASLab's Coder version: half of every layer's 384 experts pruned (192 kept) and the rest requantized, 72 GB of model "
                 "+ 111 GB n-gram table (183 GB of disk, 74 GB less than 2.00). Built for code and agent work; its quality against the "
                 "original model is not measured here",
        "ram_gb": 34, "recipe": "ista", "layout": "six", "meta_from_set": True, "subdir": "IQ2_XXS", "legacy_subdir": None, "profile": None,
        "hf": hf(DSV41_CODER_REPO) + "IQ2_XXS/",
        "shards": [DSV41_CODER_SHARD.format(i=i) for i in range(1, 6)],
        "shards6": [DSV41_CODER_SHARD.format(i=i) for i in range(1, 6)],
        "shared": [DSV41_ISTA_ENGRAM, DSV41_DSPARK]},
'''

CODER_FIT = '''ISTA_SETS["IST-DAS-Coder-2.00bpw"] = {"title": "IST-DAS Coder 2.00 bpw", "set_bytes": 72_123_567_456, "experts_gb": 66.2, "profile": None,
                                      "ppl": "?", "ram_ok_gb": 34.0, "disk_total": 183.7,
                                      "quality": "IST-DASLab's Coder version, built for code and agent work; quality against the original model not measured here"}
'''

# (file, anchor that must be present, replacement, marker proving the edit is already there)
EDITS = [
    (SETUP,
     '"ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF": "cb02422c900df489cea5833e8a92171224059b3c",',
     '"ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF": "cb02422c900df489cea5833e8a92171224059b3c",'
     f'\n    "ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-Coder-GGUF": "{REVISION}",',
     "DSV41_CODER_REPO"),
    (SETUP,
     "DSV41_SHA_ALSO = {DSV41_ISTA_ENGRAM: (DSV41_ENGRAM_CONVERTED[1],)}",
     "DSV41_SHA_ALSO = {DSV41_ISTA_ENGRAM: (DSV41_ENGRAM_CONVERTED[1],)}\n" + CODER_BLOCK,
     CODER_BLOCK.splitlines()[0]),
    (SETUP,
     "DSV41_ALL_FILES = {**DSV41_FILES, **DSV41_ISTA_FILES, **DSV41_ISTA6_FILES, **DSV41_LEGACY_FILES, **DSV41_UD_FILES}",
     "DSV41_ALL_FILES = {**DSV41_FILES, **DSV41_ISTA_FILES, **DSV41_ISTA6_FILES, **DSV41_CODER_FILES, **DSV41_LEGACY_FILES, **DSV41_UD_FILES}",
     "**DSV41_CODER_FILES, **DSV41_LEGACY_FILES"),
    (SETUP,
     '"ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF": DSV41_ISTA_FILES,',
     '"ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF": DSV41_ISTA_FILES,\n'
     '    "ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-Coder-GGUF": DSV41_CODER_FILES,',
     '"ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-Coder-GGUF": DSV41_CODER_FILES'),
    (SETUP,
     '    "UD-IQ1_S": {\n        "label": "Unsloth UD-IQ1_S",',
     CODER_MODEL + '    "UD-IQ1_S": {\n        "label": "Unsloth UD-IQ1_S",',
     '"IST-DAS-Coder-2.00bpw": {'),
    (SETUP,
     'layout = dsv41_layout_of(md, lambda n: (folder / n).exists()) if (ista and a.gguf_dir) else "four"',
     'layout = md.get("layout") or (dsv41_layout_of(md, lambda n: (folder / n).exists()) if (ista and a.gguf_dir) else "four")',
     'md.get("layout") or (dsv41_layout_of'),
    (SETUP,
     "if udlow:       # the set's own shard 1 carries the metadata",
     'if udlow or md.get("meta_from_set"):       # the set\'s own shard 1 carries the metadata',
     'md.get("meta_from_set")'),
    (SETUP,
     'prof = DSV41_PROFILES / md["profile"]          # which experts are used most',
     'prof = DSV41_PROFILES / md["profile"] if md.get("profile") else None          # which experts are used most',
     'if md.get("profile") else None'),
    (SETUP,
     '        if prof.is_file() and not (pack / "expert-profile.bin").exists():',
     '        if prof and prof.is_file() and not (pack / "expert-profile.bin").exists():',
     'if prof and prof.is_file()'),
    (SETS,
     'new1, six = getattr(module, "DSV41_NEW_SHARD1", {}), getattr(module, "DSV41_ISTA6_FILES", {})',
     'new1, six = getattr(module, "DSV41_NEW_SHARD1", {}), {**getattr(module, "DSV41_ISTA6_FILES", {}), **getattr(module, "DSV41_CODER_FILES", {})}',
     '**getattr(module, "DSV41_CODER_FILES", {})'),
    (SETS,
     'ista = {**ista, **getattr(module, "DSV41_UD_FILES", {})}',
     'ista = {**ista, **getattr(module, "DSV41_UD_FILES", {}), **getattr(module, "DSV41_CODER_FILES", {})}',
     '**getattr(module, "DSV41_CODER_FILES", {})'),
    (FIT,
     'ISTA_SETS["UD-IQ1_M"] = {"title": "Unsloth UD-IQ1_M"',
     CODER_FIT + 'ISTA_SETS["UD-IQ1_M"] = {"title": "Unsloth UD-IQ1_M"',
     'ISTA_SETS["IST-DAS-Coder-2.00bpw"]'),
    (MODELS,
     '        except OSError:\n            pass\n    if not found:\n        return None',
     '        except OSError:\n            pass\n'
     '    if not found and picked is None:\n'
     '        try:                    # a Hugging Face repository folder: the shards sit in the set\'s own sub-folder, the Engram beside it\n'
     '            top = _dsv41_files(path)\n'
     '            for sub in sorted((p for p in path.iterdir() if p.is_dir()), key=lambda p: p.name)[:8]:\n'
     '                for row in dsv41_sets.match({**top, **_dsv41_files(sub)}):\n'
     '                    found.append((sub, row))\n'
     '        except OSError:\n'
     '            pass\n'
     '    if not found:\n        return None',
     'a Hugging Face repository folder: the set\'s shards sit'),
]


def main() -> int:
    problems = 0
    for path, anchor, replacement, marker in EDITS:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"MISSING FILE {path}: {exc}")
            problems += 1
            continue
        if marker in text:
            print(f"skip   {path.name}: {marker[:60]}")
            continue
        if anchor not in text:
            print(f"ANCHOR {path.name}: not found -> {anchor[:70]!r}")
            problems += 1
            continue
        path.write_text(text.replace(anchor, replacement, 1), encoding="utf-8")
        print(f"patch  {path.name}: {marker[:60]}")
    print("done" if not problems else f"{problems} problem(s): a Control version moved the code these edits target")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
