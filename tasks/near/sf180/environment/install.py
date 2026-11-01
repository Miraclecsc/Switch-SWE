import json, os, pathlib, shutil, subprocess, tarfile

def unpack_source(source, target):
    if source.is_dir():
        # Accept the old layout during in-place migration.
        shutil.copytree(source, target, dirs_exist_ok=True)
        return
    with tarfile.open(source, "r:gz") as archive:
        seen = set()
        for member in archive:
            relative = pathlib.PurePosixPath(member.name)
            if (not member.isfile() or relative.is_absolute() or not relative.parts
                    or ".." in relative.parts or ".git" in relative.parts
                    or relative.as_posix() in seen):
                raise ValueError("Unsafe dependency source archive member")
            seen.add(relative.as_posix())
            destination = target / relative
            if not destination.resolve().is_relative_to(target.resolve()):
                raise ValueError("Dependency source escapes its install directory")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as src, destination.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            destination.chmod(member.mode & 0o777)

cfg = json.loads(pathlib.Path("/opt/ssb/environment.json").read_text())
for layer in cfg["layers"]:
    prefix = "/opt/python/" + layer["python"]
    env = dict(os.environ, PYTHONHOME=prefix, LD_LIBRARY_PATH=prefix + "/lib",
               PIP_INDEX_URL="https://pypi.org/simple", PIP_CONFIG_FILE="/dev/null",
               PIP_DISABLE_PIP_VERSION_CHECK="1")
    env.pop("PYTHONPATH", None)
    env.pop("PIP_EXTRA_INDEX_URL", None)
    target = pathlib.Path(layer["destination"])
    target.mkdir(parents=True, exist_ok=True)
    req = pathlib.Path("/opt/ssb") / layer["requirements"]
    if req.read_text().strip():
        subprocess.run([prefix + "/bin/python3", "-m", "pip", "install",
                        "--no-cache-dir", "--no-deps", "--target", str(target),
                        "-r", str(req)], env=env, check=True)
    source = pathlib.Path("/opt/ssb") / layer["source"]
    if source.exists():
        unpack_source(source, target)
    elif source.name.endswith(".tar.gz"):
        raise FileNotFoundError(source)
for i, destination in enumerate(cfg["base_layers"]):
    for alias in ("/work/test-deps", "/opt/runtime/deps"):
        path = pathlib.Path(alias) / ("%02d" % i)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(destination)
for alias, destination in cfg["native_aliases"].items():
    path = pathlib.Path(alias)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(destination)
