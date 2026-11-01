"""Export small, public Harbor Docker build contexts from the frozen cohort.

Export and migration write only below task_dir/environment.
Original releases, dependency archives, and repository mirrors are read-only.
No Docker builds, downloads, or dependency-archive copies happen on export.

Harbor API reference: harbor-framework/harbor at
ac533ec72bc506c8a6bf6f296ba6ab80707fad89, docker-compose-build.yaml:
the build context is the task's environment directory.
"""

from __future__ import annotations

import base64
import csv
import email.parser
import gzip
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import tarfile
from functools import lru_cache
from pathlib import Path, PurePosixPath


HARBOR_COMMIT = "ac533ec72bc506c8a6bf6f296ba6ab80707fad89"
_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
_VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.+!-]*\Z")
_APT = ["git", "ca-certificates", "curl", "ripgrep", "less", "patch", "diffutils",
        "build-essential", "binutils", "pkg-config", "python3", "libffi-dev",
        "libssl-dev", "libxml2-dev", "libxslt1-dev", "zlib1g-dev", "tzdata",
        "libbz2-1.0", "libreadline8", "libsqlite3-0", "liblzma5", "libgdbm6",
        "libncursesw6", "ncurses-term", "netbase"]
_BOOTSTRAP = {"pip"}
_NATIVE_TOOLS = {"bin", "lib", "usr"}
_MAX_SOURCE_BYTES = 16 * 1024 * 1024


def _canonical(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def _supports_python(specifier, version):
    """Evaluate the numeric Requires-Python clauses found in frozen metadata."""
    current = tuple(map(int, version.split(".")))
    for clause in (specifier or "").split(","):
        if not clause.strip():
            continue
        match = re.fullmatch(r"\s*(>=|<=|!=|==|~=|>|<)\s*(\d+(?:\.\d+)*)(\.\*)?\s*", clause)
        if not match:
            raise ValueError(f"Unsupported Requires-Python clause: {clause}")
        op, number, wildcard = match.groups()
        given = tuple(map(int, number.split(".")))
        actual = current[:len(given)] if wildcard else current
        wanted = given if wildcard else given + (0,) * max(0, len(current) - len(given))
        comparisons = {">=": actual >= wanted, "<=": actual <= wanted,
                       ">": actual > wanted, "<": actual < wanted,
                       "==": actual == wanted, "!=": actual != wanted}
        if op == "~=":
            allowed = actual >= wanted and current[:len(given) - 1] == given[:-1]
        else:
            allowed = comparisons[op]
        if not allowed:
            return False
    return True


def _relative(name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not path.parts or ".git" in path.parts:
        raise ValueError(f"Unsafe asset path: {name!r}")
    return path.as_posix()


def _digest(data):
    return hashlib.sha256(data).hexdigest()


@lru_cache(maxsize=512)
def _json(path):
    return json.loads(Path(path).read_text())


def _layers(value):
    return value if isinstance(value, list) else ([value] if value else [])


@lru_cache(maxsize=2048)
def _dependency_files(mirror, commit):
    # ls-tree reads local tree objects, not lazily fetched requirement blobs.
    result = subprocess.run(
        ["git", "-C", mirror, "ls-tree", "-z", commit, "--", "pyproject.toml",
         "setup.cfg", "setup.py", "requirements.txt"],
        capture_output=True, check=True, timeout=10,
        env=dict(os.environ, GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0"))
    return {row.split(b"\t", 1)[1].decode(): row.split(b"\t", 1)[0].split()[2].decode()
            for row in result.stdout.split(b"\0") if row}


def _resolve_input(path, roots):
    original = Path(path)
    if original.is_file() or original.is_dir():
        return original
    # Frozen manifests contain historical host paths. Resolve only a suffix
    # anchored at this benchmark's root, never copy that path into an image.
    for marker in ("/SessionSwitchBench/",):
        if marker in str(original):
            suffix = str(original).split(marker, 1)[1]
            for root in roots:
                candidate = root / suffix
                if candidate.exists():
                    return candidate
    raise FileNotFoundError(f"Frozen input is unavailable: {original}")


def _context(case, source_root):
    source_root = Path(source_root).resolve()
    roots = [source_root, *source_root.parents]
    catalog = None
    for root in roots:
        for suffix in ("config/environment-catalog.json",
                       "workspaces/SessionSwitchBench/config/environment-catalog.json"):
            path = root / suffix
            if path.is_file():
                catalog = _json(str(path))
                break
        if catalog is not None:
            break
    if catalog is None:
        raise FileNotFoundError("source_root must locate the frozen environment catalog")
    trial = catalog["trials"][case["case_id"]]
    frozen = trial["case"]
    for key in ("condition", "focus_workspace", "workspaces"):
        if case[key] != frozen[key]:
            raise ValueError(f"{case['case_id']}: {key} differs from the frozen catalog")
    if case["condition"] != "switched" or len(case["workspaces"]) != 5:
        raise ValueError("This exporter accepts only the five-workspace switched cohort")
    if {w["workspace"] for w in case["workspaces"]} != {f"w{i:02}" for i in range(5)}:
        raise ValueError("Expected w00..w04")
    release = _resolve_input(trial["source"]["release"], roots)
    return trial, release, roots


@lru_cache(maxsize=256)
def _archive(path, expected_sha):
    """Read metadata and source deltas, retaining no large binary payloads.

    RECORD hashes distinguish locally patched files from published wheel files.
    Missing RECORD coverage is deliberately preserved as source, not silently
    replaced by a package with a coincidentally matching version.
    """
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    if h.hexdigest() != expected_sha:
        raise ValueError(f"Dependency archive SHA256 mismatch: {Path(path).name}")
    packages, records, owners, payload, blockers, native = {}, {}, {}, {}, [], set()
    with tarfile.open(path, "r:*") as archive:
        files = {}
        for member in archive:
            name = member.name
            while name.startswith("./"):
                name = name[2:]
            if not name or name == "." or member.isdir():
                continue
            name = _relative(name)
            if name in files or not member.isfile():
                raise ValueError(f"Duplicate or nonregular dependency member: {name}")
            files[name] = member
        for name, member in files.items():
            parts = PurePosixPath(name).parts
            if len(parts) != 2 or parts[-1] not in ("METADATA", "PKG-INFO"):
                continue
            if not parts[0].endswith((".dist-info", ".egg-info")):
                continue
            message = email.parser.BytesParser().parsebytes(archive.extractfile(member).read())
            package, version = message.get("Name", ""), message.get("Version", "")
            if not _NAME.fullmatch(package) or not _VERSION.fullmatch(version):
                raise ValueError(f"Invalid dependency identity in {name}")
            key = _canonical(package)
            packages[key] = {"name": package, "version": version, "root": parts[0],
                             "requires_python": message.get("Requires-Python")}
            record_name = parts[0] + "/RECORD"
            if record_name in files:
                text = archive.extractfile(files[record_name]).read().decode()
                for row in csv.reader(io.StringIO(text)):
                    if not row:
                        continue
                    record_path = str(PurePosixPath(row[0]))
                    if record_path.startswith("../"):
                        continue
                    owners[record_path] = key
                    records[record_path] = row[1] if len(row) > 1 else ""
        retained = 0
        for name, member in files.items():
            parts = PurePosixPath(name).parts
            top = parts[0]
            owner = owners.get(name)
            if name.startswith(("share/man/", "share/terminfo/")):
                # Manpages are not runtime inputs; system terminfo comes from
                # ncurses-term. Original archives remain untouched.
                continue
            if (top in ("__pycache__", ".lock", "_virtualenv.py", "_virtualenv.pth")
                    or "__pycache__" in parts or name.endswith((".pyc", ".pyo"))
                    or top.startswith("__editable__") or name.endswith(".egg-link")
                    or top == "pip" or top == "setuptools"):
                continue
            if top in _NATIVE_TOOLS:
                native.add(top)
                continue
            is_metadata = top.endswith((".dist-info", ".egg-info"))
            is_license = any("license" in p.lower() or "copying" in p.lower() for p in parts)
            # Keep license bytes beside retained sources; never ship direct_url
            # metadata, installed console shebangs, or local editable hooks.
            if is_metadata and not is_license:
                continue
            if owner in _BOOTSTRAP and not is_license:
                continue
            if member.size > _MAX_SOURCE_BYTES:
                if owner:
                    continue  # Rebuilt from that distribution, not copied.
                blockers.append(f"Unmapped large asset: {name}")
                continue
            data = archive.extractfile(member).read()
            binary = data.startswith(b"\x7fELF") or name.endswith((".so", ".a", ".whl", ".dll"))
            if binary:
                if not owner:
                    blockers.append(f"Unmapped native asset: {name}")
                continue
            recorded = records.get(name, "")
            unchanged = False
            if recorded.startswith("sha256="):
                actual = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
                unchanged = actual == recorded.split("=", 1)[1]
            # Some qualified source backports deliberately regenerated RECORD.
            # Their package code must survive even when its local RECORD matches.
            custom_source = (
                ("backport" in Path(path).name and top == "httpcore")
                or ("code-location" in Path(path).name and top == "hypothesis"))
            if unchanged and not is_license and not custom_source:
                continue
            if b"\0" in data and not owner:
                blockers.append(f"Unmapped binary data: {name}")
                continue
            # Paths embedded in the original benchmark helper sources must be
            # reviewed, rather than accidentally publishing private endpoints.
            if any(token in data for token in (b"/mnt/jfs/", b"/home/i-", b"hub.i.basemind",
                                                b"oss.i.shaipower", b"platform.shaipower")):
                blockers.append(f"Source asset contains host-specific references: {name}")
                continue
            retained += len(data)
            if retained > _MAX_SOURCE_BYTES:
                raise ValueError(f"Source delta exceeds 16 MiB: {Path(path).name}")
            payload[name] = (data, 0o755 if member.mode & 0o111 else 0o644, owner)
    return {"packages": packages, "payload": payload, "blockers": blockers,
            "native_tools": bool(native)}


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode())


def _write_json(path, value):
    _write(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def _source_archive(files):
    """Pack {relative_name: (bytes, mode)} with deterministic tar/gzip headers."""
    output = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for name, (data, mode) in sorted(files.items()):
                member = tarfile.TarInfo(_relative(name))
                member.size = len(data)
                member.mode = mode & 0o777
                member.mtime = member.uid = member.gid = 0
                member.uname = member.gname = ""
                archive.addfile(member, io.BytesIO(data))
    return output.getvalue()


def migrate_dependency_sources(task_dir) -> dict:
    """Compact an existing task without reading any original frozen assets.

    Only dependency-source/, environment.json and install.py are changed.
    Archives are written first, then the backward-compatible installer and
    config; original directories are removed last. Repeated calls are safe.
    """
    environment = Path(task_dir) / "environment"
    config_path = environment / "environment.json"
    config = json.loads(config_path.read_text())
    directories = []
    converted = files_count = source_bytes = archive_bytes = 0
    for layer in config["layers"]:
        relative = PurePosixPath(_relative(layer["source"]))
        if len(relative.parts) != 2 or relative.parts[0] != "dependency-source":
            raise ValueError(f"Unexpected dependency source path: {relative}")
        source = environment / str(relative)
        if source.is_symlink():
            raise ValueError(f"Dependency source is a symlink: {relative}")
        if str(relative).endswith(".tar.gz"):
            if not source.is_file():
                raise FileNotFoundError(source)
            continue
        files = {}
        if source.exists():
            if not source.is_dir():
                raise ValueError(f"Expected dependency source directory: {relative}")
            for path in sorted(source.rglob("*")):
                mode = path.lstat().st_mode
                if stat.S_ISDIR(mode):
                    continue
                if not stat.S_ISREG(mode):
                    raise ValueError(f"Nonregular dependency source: {path}")
                files[path.relative_to(source).as_posix()] = (
                    path.read_bytes(), stat.S_IMODE(mode))
            directories.append(source)
        # Old exports omitted directories for layers with no retained source.
        data = _source_archive(files)
        archive_path = str(relative) + ".tar.gz"
        destination = environment / archive_path
        if destination.exists() and destination.read_bytes() != data:
            raise ValueError(f"Existing source archive differs: {destination}")
        _write(destination, data)
        layer["source"] = archive_path
        converted += 1
        files_count += len(files)
        source_bytes += sum(len(content) for content, _ in files.values())
        archive_bytes += len(data)
    if converted or (environment / "install.py").read_text() != _INSTALL:
        # Keep temporary writes inside the authorized dependency-source scope.
        staging = environment / "dependency-source"
        staging.mkdir(parents=True, exist_ok=True)
        for name, content in (
                ("install.py", _INSTALL),
                ("environment.json", json.dumps(config, indent=2, sort_keys=True) + "\n")):
            temporary = staging / ("." + name + ".tmp")
            _write(temporary, content)
            temporary.replace(environment / name)
    for directory in directories:
        shutil.rmtree(directory)
    return {"task": Path(task_dir).name, "converted_layers": converted,
            "source_files": files_count, "source_bytes": source_bytes,
            "archive_bytes": archive_bytes}


def migrate_task_environments(tasks_root) -> dict:
    """Migrate all split/task/environment directories under an exported tasks root."""
    results = [migrate_dependency_sources(path.parent.parent)
               for path in sorted(Path(tasks_root).glob("*/*/environment/environment.json"))]
    return {"tasks": len(results), **{
        key: sum(row[key] for row in results)
        for key in ("converted_layers", "source_files", "source_bytes", "archive_bytes")}}


_DISPATCH = r'''#!/usr/bin/python3
import json, os, pathlib, sys
cfg = json.loads(pathlib.Path("/opt/ssb/environment.json").read_text())
cwd = pathlib.Path.cwd()
ws = os.environ.get("SSB_WORKSPACE", cfg.get("focus_workspace", "w00"))
for candidate in cwd.parents:
    if candidate.parent == pathlib.Path("/work") and candidate.name in cfg["profiles"]:
        ws = candidate.name
if cwd.parent == pathlib.Path("/work") and cwd.name in cfg["profiles"]:
    ws = cwd.name
profile = cfg["profiles"][ws]
env = dict(os.environ)
env.update(cfg["env"])
env.update(profile["env"])
prefix = "/opt/python/" + profile["python"]
env["PYTHONHOME"] = prefix
env["LD_LIBRARY_PATH"] = prefix + "/lib:" + env.get("LD_LIBRARY_PATH", "")
root = pathlib.Path("/work") / ws
if root != cwd and root not in cwd.parents:
    root = cwd
paths = [str(root / "src"), str(root)] + profile["paths"]
if env.get("PYTHONPATH"):
    paths.append(env["PYTHONPATH"])
env["PYTHONPATH"] = ":".join(paths)
env["PATH"] = "/opt/ssb/bin:" + prefix + "/bin:" + ":".join(
    p + "/bin" for p in profile["paths"]) + ":/usr/local/bin:/usr/bin:/bin"
args = sys.argv[1:]
if pathlib.Path(sys.argv[0]).name == "pytest":
    args = ["-m", "pytest"] + args
os.execve(prefix + "/bin/python3", [prefix + "/bin/python3"] + args, env)
'''


_CHECKOUT = r'''import hashlib, json, os, pathlib, shutil, subprocess
cfg = json.loads(pathlib.Path("/opt/ssb/environment.json").read_text())
def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()
for row in cfg["workspaces"]:
    root = pathlib.Path("/work") / row["workspace"]
    root.mkdir(parents=True)
    git(root, "init", "-q")
    (root / ".git/info/attributes").write_text(
        "* -text -eol -ident -filter -working-tree-encoding\n")
    git(root, "remote", "add", "origin", row["url"])
    git(root, "fetch", "--depth=1", "origin", row["commit"])
    git(root, "checkout", "--detach", "FETCH_HEAD")
    if git(root, "rev-parse", "HEAD") != row["commit"]:
        raise RuntimeError("Public checkout commit mismatch")
    if row["workspace"] == cfg["focus_workspace"]:
        shutil.copytree(root, "/opt/focus-base", symlinks=True)
    for item in row["overlays"]:
        target = root / item["path"]
        if not target.resolve().is_relative_to(root):
            raise RuntimeError("Overlay escapes checkout")
        if item["mode"] == "delete":
            if target.is_symlink() or target.is_file():
                target.unlink()
            elif target.is_dir():
                shutil.rmtree(target)
            continue
        data = (pathlib.Path("/opt/ssb/overlay-blobs") / item["sha256"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise RuntimeError("Overlay digest mismatch")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            target.unlink()
        elif target.is_dir():
            shutil.rmtree(target)
        if item["mode"] == "120000":
            link = data.decode()
            if not (target.parent / link).resolve().is_relative_to(root):
                raise RuntimeError("Unsafe overlay symlink")
            target.symlink_to(link)
        else:
            target.write_bytes(data)
            target.chmod(int(item["mode"], 8) & 0o777)
    # Keep HEAD at ORIGINAL base. git diff HEAD includes the initial overlay,
    # which is required when the final patch is applied to /opt/focus-base.
    git(root, "add", "--intent-to-add", "--all", "--force")
'''


_INSTALL = r'''import json, os, pathlib, shutil, subprocess, tarfile

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
'''


_NATIVE = r'''#!/usr/bin/python3
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
'''


def export_environment(case, source_root, task_dir) -> dict:
    """Write an environment/Dockerfile and its bounded source assets.

    ``case`` is an unchanged effective-cases.json switched row. ``source_root``
    may be the benchmark root or its candidate release; the catalog is resolved
    from its ancestors. Returns JSON-serializable build information. A nonempty
    ``blockers`` list intentionally makes the Docker build fail, rather than
    quietly substituting an incomplete environment.
    """
    return _environment(case, source_root, task_dir)


def inspect_environment(case, source_root) -> dict:
    """Return the same build information without writing any files."""
    return _environment(case, source_root, None)


def _environment(case, source_root, task_dir):
    trial, release, roots = _context(case, source_root)
    spec = trial["launch_spec"]
    output = Path(task_dir) / "environment" if task_dir is not None else None
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)

    def emit(name, data, mode=None):
        if output is not None:
            _write(output / name, data)
            if mode is not None:
                (output / name).chmod(mode)

    def emit_json(name, data):
        emit(name, json.dumps(data, indent=2, sort_keys=True) + "\n")
    blockers, evidence = [], []
    targets = {_canonical(m.split(".")[0]) for m in spec["target_modules"]}
    targets.add(_canonical(spec["import_module"]))
    targets.add(_canonical(trial["family"].split("/")[-1]))
    recipe = spec["verifier"]["recipe"]
    base_python = ".".join(map(str, spec["python_runtime"]["version"]))
    cfg = {"case_id": case["case_id"], "focus_workspace": case["focus_workspace"],
           "env": dict(recipe.get("env", {})), "profiles": {}, "layers": [],
           "base_layers": [], "workspaces": [], "native_build_paths": [],
           "native_aliases": {}}
    if "TERMINFO_DIRS" in cfg["env"]:
        cfg["env"]["TERMINFO_DIRS"] = "/usr/share/terminfo:/lib/terminfo"
    source_bytes = 0
    layer_cache = {}

    def add_layer(ref, version, hidden=()):
        nonlocal source_bytes
        identity = (ref["tar_sha256"], version, ref.get("target_metadata_only", False), tuple(sorted(hidden)))
        if identity in layer_cache:
            return layer_cache[identity]
        path = _resolve_input(ref["tar_path"], roots)
        data = _archive(str(path), ref["tar_sha256"])
        label = ref["tar_sha256"][:16] + "-" + version + "-" + _digest(
            json.dumps(identity).encode())[:8]
        destination = "/opt/ssb/deps/" + label
        packages = data["packages"]
        selected = {k: v for k, v in packages.items()
                    if k not in targets | _BOOTSTRAP | set(hidden)}
        incompatible = [v for v in selected.values()
                        if not _supports_python(v["requires_python"], version)]
        selected = {k: v for k, v in selected.items()
                    if _supports_python(v["requires_python"], version)}
        requirements = "\n".join(v["name"] + "==" + v["version"]
                                 for _, v in sorted(selected.items()))
        req = "requirements/" + label + ".txt"
        emit(req, requirements + ("\n" if requirements else ""))
        assets = "dependency-source/" + label + ".tar.gz"
        source_files = {}
        for name, (content, mode, owner) in data["payload"].items():
            top = PurePosixPath(name).parts[0]
            if owner in targets | set(hidden) or _canonical(top.removesuffix(".py")) in targets:
                continue
            source_files[name] = (content, mode)
            source_bytes += len(content)
        if ref.get("target_metadata_only"):
            # Isort's generated version metadata belongs to the checked-out
            # source; it is not a published PyPI package version.
            with tarfile.open(path) as archive:
                for member in archive:
                    name = member.name.removeprefix("./")
                    if member.isfile() and PurePosixPath(name).name in (
                            "METADATA", "WHEEL", "entry_points.txt", "top_level.txt"):
                        source_files[_relative(name)] = (archive.extractfile(member).read(), 0o644)
        if output is not None:
            emit(assets, _source_archive(source_files))
        blockers.extend(f"{label}: {issue}" for issue in data["blockers"])
        row = {"destination": destination, "python": version, "requirements": req, "source": assets}
        cfg["layers"].append(row)
        evidence.append({"archive_sha256": ref["tar_sha256"], "python": version,
                         "packages": [{k: v for k, v in p.items() if k != "root"}
                                      for p in selected.values()],
                         "native_tools_replaced_by_apt": data["native_tools"],
                         "shadowed_packages": sorted(set(hidden) & packages.keys()),
                         "unusable_on_selected_python": [
                             {"name": p["name"], "version": p["version"],
                              "requires_python": p["requires_python"]} for p in incompatible]})
        layer_cache[identity] = destination
        return destination

    def add_stack(refs, version):
        paths, hidden = [], set()
        for ref in reversed(refs):
            paths.append(add_layer(ref, version, hidden))
            path = _resolve_input(ref["tar_path"], roots)
            hidden.update(_archive(str(path), ref["tar_sha256"])["packages"])
        return list(reversed(paths))

    base_refs = _layers(spec["verifier"].get("dependencies"))
    cfg["base_layers"] = add_stack(base_refs, base_python)
    overlays_path = release / "private/workspace-overlays.json"
    if _digest(overlays_path.read_bytes()) != spec["overlays_sha256"]:
        raise ValueError("Frozen workspace overlays digest mismatch")
    overlays = _json(str(overlays_path))[case["case_id"]]
    source_inputs = {w["workspace"]: w for w in spec["source_inputs"]}
    for workspace in case["workspaces"]:
        ws = workspace["workspace"]
        profile = spec.get("agent_workspace_environments", {}).get(ws, {})
        version = ".".join(map(str, profile.get("python_runtime", spec["python_runtime"])["version"]))
        # Workspace overlays supplement, rather than replace, the base layers.
        # Install base wheels for this interpreter to avoid crossing cp39/cp312.
        paths = add_stack(base_refs + _layers(profile.get("dependencies")), version)
        cfg["profiles"][ws] = {"python": version, "env": profile.get("env", {}),
                               "paths": list(reversed(paths))}
        repo, commit = workspace["repo"], workspace["commit"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ValueError(f"Invalid public repository: {repo}")
        if not re.fullmatch(r"[a-f0-9]{40}", commit):
            raise ValueError(f"Invalid base commit: {commit}")
        row = {"workspace": ws, "repo": repo, "commit": commit,
               "url": "https://github.com/" + repo + ".git", "overlays": []}
        for name, overlay in sorted(overlays.get(ws, {}).items()):
            name = _relative(name)
            if overlay is None or overlay.get("delete"):
                row["overlays"].append({"path": name, "mode": "delete"})
                continue
            mode = str(overlay.get("mode", "100644"))
            if mode not in ("100644", "100755", "120000"):
                raise ValueError(f"Unsupported overlay mode {mode}")
            blob = release / _relative(overlay["content_path"])
            content = blob.read_bytes()
            if _digest(content) != overlay["sha256"]:
                raise ValueError(f"Overlay blob digest mismatch: {name}")
            emit("overlay-blobs/" + overlay["sha256"], content)
            source_bytes += len(content)
            row["overlays"].append({"path": name, "mode": mode, "sha256": overlay["sha256"]})
        cfg["workspaces"].append(row)
        mirror = _resolve_input(source_inputs[ws]["repo_path"], roots)
        # Small evidence only: source requirements stay in the fetched checkout.
        evidence.append({"workspace": ws, "base_commit": commit,
                         "dependency_file_git_blob_ids": _dependency_files(str(mirror), commit)})
    native = recipe.get("native_build")
    if native:
        if native.get("kind") != "pandas-wheel":
            blockers.append("Unsupported native build recipe: " + str(native.get("kind")))
        for ref in spec["verifier"].get("native_assets", []):
            if ref["destination"] == "/work/native/build-deps":
                cfg["native_build_paths"].append(add_layer(ref, base_python))
            elif ref["destination"] == "/work/native/optional-arrow":
                cfg["native_aliases"][ref["destination"]] = add_layer(ref, base_python)
        if not cfg["native_build_paths"]:
            blockers.append("Pandas has no frozen native build dependency metadata")
    for env in [cfg["env"]] + [p["env"] for p in cfg["profiles"].values()]:
        for key, value in env.items():
            if not re.fullmatch(r"[A-Z_][A-Z_0-9]*", key) or not isinstance(value, str):
                raise ValueError("Invalid frozen environment entry")
            if any(s in value for s in ("/mnt/", "/home/", "shaipower", "basemind")):
                blockers.append("Environment value requires a portable replacement: " + key)
    emit_json("environment.json", cfg)
    emit("dispatch.py", _DISPATCH)
    emit("checkout.py", _CHECKOUT)
    emit("install.py", _INSTALL)
    if native:
        emit("rebuild-native.py", _NATIVE)
    versions = sorted({base_python} | {p["python"] for p in cfg["profiles"].values()})
    lines = [f"FROM python:{version}-slim-bookworm AS python_{version.replace('.', '_')}"
             for version in versions]
    lines += ["FROM debian:bookworm-slim", "ENV DEBIAN_FRONTEND=noninteractive",
              "RUN apt-get update && apt-get install -y --no-install-recommends "
              + " ".join(_APT + (["gcc-11", "g++-11"] if native else []))
              + " && rm -rf /var/lib/apt/lists/*"]
    for version in versions:
        lines.append(f"COPY --from=python_{version.replace('.', '_')} /usr/local/ /opt/python/{version}/")
    lines += ["COPY . /opt/ssb/", "WORKDIR /work"]
    if blockers:
        lines.append("RUN echo " + shlex.quote("Environment export blocked: "
                                               + "; ".join(sorted(set(blockers)))) + " >&2; exit 1")
    lines += ["RUN /usr/bin/python3 /opt/ssb/install.py",
              "RUN /usr/bin/python3 /opt/ssb/checkout.py",
              "RUN mkdir -p /opt/ssb/bin && chmod +x /opt/ssb/dispatch.py"
              " && ln -s /opt/ssb/dispatch.py /opt/ssb/bin/python"
              " && ln -s /opt/ssb/dispatch.py /opt/ssb/bin/python3"
              " && ln -s /opt/ssb/dispatch.py /opt/ssb/bin/pytest",
              'ENV PATH="/opt/ssb/bin:/usr/local/bin:/usr/bin:/bin"',
              "ENV PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1"]
    major_minor = ".".join(base_python.split(".")[:2])
    lines.append("RUN mkdir -p /opt/runtime/case-python/python/bin"
                 " && ln -s /opt/ssb/dispatch.py /opt/runtime/case-python/python/bin/python"
                 " && ln -s /opt/ssb/dispatch.py /opt/runtime/case-python/python/bin/python3"
                 f" && ln -s /opt/ssb/dispatch.py /opt/runtime/case-python/python/bin/python{major_minor}")
    if native:
        lines.append("RUN chmod +x /opt/ssb/rebuild-native.py")
        for ws in sorted(cfg["profiles"]):
            lines.append(f"RUN /opt/ssb/rebuild-native.py /work/{ws}")
    for ws in sorted(cfg["profiles"]):
        lines.append(f"RUN cd /work/{ws} && python -c "
                     + shlex.quote("import " + spec["import_module"]))
    lines += [
        "RUN useradd -m -s /bin/bash agent && chown -R agent:agent /work"
        " && chmod 700 /opt/focus-base",
        "RUN /usr/bin/python3 -c " + shlex.quote(
            "import json,pathlib; p=pathlib.Path('/opt/ssb/environment.json'); "
            "c=json.loads(p.read_text()); c.pop('focus_workspace',None); "
            "c.pop('case_id',None); p.write_text(json.dumps(c))"
        ) + " && rm -rf /opt/ssb/checkout.py /opt/ssb/overlay-blobs",
        "WORKDIR /work", "",
    ]
    emit("Dockerfile", "\n".join(lines))
    info = {"schema": 1, "case_id": case["case_id"], "dockerfile": "environment/Dockerfile",
            "harbor_commit": HARBOR_COMMIT, "build_status": "blocked" if blockers else "not_built",
            "blockers": sorted(set(blockers)), "python_versions": versions,
            "focus_workspace": case["focus_workspace"], "focus_base": "/opt/focus-base",
            "python_executable": "/opt/ssb/bin/python",
            "focus_commit": next(w["commit"] for w in case["workspaces"]
                                 if w["workspace"] == case["focus_workspace"]),
            "source_asset_bytes": source_bytes, "dependency_evidence": evidence,
            "native_rebuild_command": "/opt/ssb/rebuild-native.py CHECKOUT" if native else None,
            "limitations": [
                "Public images, apt packages and PyPI artifacts have not been build-verified.",
                "Dependency versions and source deltas are frozen; OS/image bytes are not.",
                "Private Python, compiler and native caches are replaced by public builds.",
                "Metadata-incompatible packages from a different Python runtime are not installed; see dependency_evidence.",
                "Workspace HEAD stays at the original commit; initial overlays remain in git diff.",
                "Pandas final-patch verification must rebuild extensions from the patched checkout."
            ]}
    return info
