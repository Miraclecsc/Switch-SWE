#!/usr/bin/python3
"""Rebuild pandas extensions from the supplied checkout, including final edits."""
import json, os, pathlib, shutil, subprocess, sys, tempfile, zipfile
repo = pathlib.Path(sys.argv[1]).resolve()
cfg = json.loads(pathlib.Path("/opt/ssb/environment.json").read_text())
ws = os.environ.get("SSB_WORKSPACE", cfg.get("focus_workspace", "w00"))
if repo.name in cfg["profiles"]:
    ws = repo.name
profile = cfg["profiles"][ws]
prefix = "/opt/python/" + profile["python"]
env = dict(os.environ, PYTHONHOME=prefix, LD_LIBRARY_PATH=prefix + "/lib",
           PYTHONPATH=":".join(cfg["native_build_paths"] + profile["paths"]),
           PATH=prefix + "/bin:" + ":".join(p + "/bin" for p in cfg["native_build_paths"]) +
                ":/usr/bin:/bin", CC="gcc-11", CXX="g++-11")
with tempfile.TemporaryDirectory(prefix="ssb-native-") as tmp:
    source = pathlib.Path(tmp) / "source"
    shutil.copytree(repo, source, symlinks=True)
    wheels = pathlib.Path(tmp) / "wheels"
    subprocess.run([prefix + "/bin/python3", "-m", "pip", "wheel",
                    "--no-deps", "--no-build-isolation", "--wheel-dir", str(wheels),
                    "--config-settings=compile-args=-j2", str(source)],
                   env=env, check=True)
    wheel, = wheels.glob("pandas-*.whl")
    tracked = set(subprocess.check_output(["git", "-C", str(repo), "ls-files", "-z"]
                                        ).decode().split("\0"))
    with zipfile.ZipFile(wheel) as archive:
        for name in archive.namelist():
            path = pathlib.PurePosixPath(name)
            if path.parts[0] != "pandas" or ".." in path.parts or path.is_absolute():
                continue
            if not (name.endswith(".so") or name == "pandas/_version_meson.py"):
                continue
            if name in tracked:
                raise RuntimeError("Native wheel would replace tracked source: " + name)
            target = repo / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
