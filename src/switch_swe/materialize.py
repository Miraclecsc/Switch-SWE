#!/usr/bin/env python3
"""Host-only, stdlib-only independent source snapshots.

Ported from SessionSwitchBench src/driver/independent_v1/materialize.py.
The snapshot, byte audit and synthetic Git implementation is retained unchanged.
See docs/workspaces.md for the public preparer's scope.
"""
from __future__ import annotations

import argparse
from collections import deque
import ctypes
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile


class MaterializeError(ValueError):
    """Invalid input, unsafe content, failed audit, or failed publication."""


MODES = {"100644", "100755", "120000"}
OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
GIT = shutil.which("git", path=os.defpath) or "/usr/bin/git"
RAW_ATTRIBUTES = "* -text -eol -ident -filter -working-tree-encoding\n"


def require(condition, message):
    if not condition:
        raise MaterializeError(message)


def clean_env():
    # No caller credentials, filters, templates, replace refs, or object paths.
    return {
        "PATH": os.defpath, "HOME": "/nonexistent", "LANG": "C.UTF-8",
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_ATTR_NOSYSTEM": "1", "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_TERMINAL_PROMPT": "0", "GIT_NO_LAZY_FETCH": "1",
        "GIT_AUTHOR_NAME": "Snapshot", "GIT_AUTHOR_EMAIL": "snapshot@localhost",
        "GIT_COMMITTER_NAME": "Snapshot", "GIT_COMMITTER_EMAIL": "snapshot@localhost",
        "GIT_AUTHOR_DATE": "2000-01-01T00:00:00 +0000",
        "GIT_COMMITTER_DATE": "2000-01-01T00:00:00 +0000",
    }


def git(args, *, env=None, data=None, stdout=None):
    try:
        result = subprocess.run(
            [GIT, "-c", "core.hooksPath=/dev/null", "-c", "core.attributesFile=/dev/null",
             "-c", "gc.auto=0", *map(str, args)],
            input=data, stdout=stdout or subprocess.PIPE, stderr=subprocess.PIPE,
            env=env or clean_env(), check=False, timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MaterializeError("Git operation failed or timed out") from exc
    # Do not echo Git stderr, which may contain private paths/content.
    require(result.returncode == 0, "Git operation failed (missing/invalid object or input)")
    return result.stdout


def relative(path):
    require(isinstance(path, str) and path and "\0" not in path and "\\" not in path,
            "Expected canonical relative POSIX path")
    require(all(p not in ("", ".", "..") for p in path.split("/")),
            "Path traversal or noncanonical path")
    return path


def metadata(path):
    return any(part.lower() == ".git" for part in path.split("/"))


def object_id(value):
    require(isinstance(value, str) and OID.fullmatch(value), "Expected full lowercase Git ID")
    return value


def canonical_host(path):
    path = Path(os.path.abspath(os.fspath(path)))
    require(path == path.resolve(), "Host path must not contain symlinks")
    return path


def normalize_overrides(overrides):
    if isinstance(overrides, list):
        pairs = []
        for entry in overrides:
            require(isinstance(entry, dict) and "path" in entry, "Overlay entry needs path")
            value = {k: v for k, v in entry.items() if k != "path"}
            if value == {"delete": True}:
                value = None
            pairs.append((entry["path"], value))
    else:
        require(isinstance(overrides, dict), "Overrides must be a map or entry list")
        pairs = list(overrides.items())
    result = {}
    for path, value in pairs:
        relative(path)
        require(not metadata(path), "Overlay may not create or delete Git metadata")
        require(path not in result, "Duplicate overlay path")
        if value is not None:
            require(isinstance(value, dict) and value.get("mode") in MODES,
                    "Unsupported overlay file mode")
            require(set(value) in ({"mode", "blob"}, {"mode", "sha256", "content_path"}),
                    "Overlay requires blob or sha256/content_path")
            if "blob" in value:
                blob = value["blob"]
                require(isinstance(blob, str), "Invalid blob ID")
                if blob.startswith("sha256:"):
                    require(SHA256.fullmatch(blob[7:]), "Invalid content digest")
                else:
                    object_id(blob)
            else:
                require(isinstance(value["sha256"], str) and SHA256.fullmatch(value["sha256"]),
                        "Invalid content digest")
                relative(value["content_path"])
            value = dict(value)
        result[path] = value
    return result


def source_store(repo, control, name):
    """Isolated read-only facade; never copy source config/refs/objects to output."""
    repo = canonical_host(repo)
    require(repo.is_dir(), "Trusted bare repository does not exist")
    args = ["-c", f"safe.directory={repo}", "--git-dir", repo]
    require(git([*args, "rev-parse", "--is-bare-repository"]).strip() == b"true",
            "Source must be a bare repository")
    fmt = git([*args, "rev-parse", "--show-object-format"]).decode().strip()
    require(fmt in {"sha1", "sha256"}, "Unsupported Git object format")
    objects = canonical_host(repo / "objects")
    require(objects.is_dir(), "Source object store is missing")
    facade = control / name
    git(["init", "--bare", "--quiet", "--template=", f"--object-format={fmt}", facade])
    # info/attributes has higher precedence than every tracked .gitattributes.
    (facade / "info").mkdir(exist_ok=True)
    (facade / "info/attributes").write_text(
        RAW_ATTRIBUTES + "* -export-ignore -export-subst\n")
    env = clean_env()
    env["GIT_DIR"] = str(facade)
    # Git accepts a C-quoted alternate path, including ':' or newline in host names.
    env["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = json.dumps(str(objects))
    return env, fmt


def source_manifest(env, commit, tree):
    require((commit is None) != (tree is None), "Specify exactly one commit or tree")
    oid = object_id(tree if tree is not None else commit)
    kind = git(["cat-file", "-t", oid], env=env).strip()
    require(kind == (b"tree" if tree is not None else b"commit"), "Wrong base object type")
    tree = git(["rev-parse", "--verify", oid + "^{tree}"], env=env).decode().strip()
    manifest, stripped = {}, []
    for row in git(["ls-tree", "-r", "-z", tree], env=env).split(b"\0"):
        if not row:
            continue
        header, raw_path = row.split(b"\t", 1)
        path = os.fsdecode(raw_path)
        relative(path)
        mode, kind, blob = header.decode("ascii").split()
        if metadata(path) or mode == "160000":
            stripped.append(path)
            continue
        require(mode in MODES and kind == "blob", "Unsupported source tree entry")
        require(path not in manifest, "Duplicate tree path")
        manifest[path] = {"path": path, "mode": mode, "blob": object_id(blob)}
    return tree, manifest, stripped


def final_manifest(base, overrides):
    final = {path: dict(entry) for path, entry in base.items()}
    # Deleting a directory deletes its descendants. Explicit delete is required
    # to replace a leaf with a directory; writes never follow leaf parents.
    for path, value in overrides.items():
        if value is None:
            final = {p: e for p, e in final.items() if p != path and not p.startswith(path + "/")}
    for path, value in sorted(overrides.items()):
        if value is None:
            continue
        parts = path.split("/")
        require(not any("/".join(parts[:i]) in final for i in range(1, len(parts))),
                "Overlay parent is a file or symlink; delete it explicitly first")
        final = {p: e for p, e in final.items() if not p.startswith(path + "/")}
        blob = value.get("blob", "sha256:" + value.get("sha256", ""))
        final[path] = {"path": path, "mode": value["mode"], "blob": blob}
    # Parent/child overlay assignments are ambiguous and must not depend on order.
    writes = {p for p, e in overrides.items() if e is not None}
    for path in writes:
        parts = path.split("/")
        require(not any("/".join(parts[:i]) in writes for i in range(1, len(parts))),
                "Conflicting parent/child overlays")
    return final


def sanitized_archive_tree(manifest, env):
    """Git archive rejects .git names even if extraction would omit them."""
    nested = {}
    for path, entry in manifest.items():
        parts = path.split("/")
        node = nested
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = entry
    # Writing with alternates attached can freshen upstream objects. mktree
    # --missing needs no blobs, so detach alternates during these local writes.
    detached = {k: v for k, v in env.items() if k != "GIT_ALTERNATE_OBJECT_DIRECTORIES"}

    def build(node):
        rows = []
        for name, value in node.items():
            if "path" in value and isinstance(value["path"], str):
                mode, kind, oid = value["mode"], "blob", value["blob"]
            else:
                mode, kind, oid = "040000", "tree", build(value)
            rows.append(f"{mode} {kind} {oid}\t".encode() + os.fsencode(name) + b"\0")
        return git(["mktree", "--missing", "-z"], env=detached, data=b"".join(rows)).decode().strip()
    return build(nested)


def file_hash(stream, size, sink=None):
    hashes = {"sha256": hashlib.sha256(), "git_sha1": hashlib.sha1(),
              "git_sha256": hashlib.sha256()}
    header = b"blob " + str(size).encode() + b"\0"
    hashes["git_sha1"].update(header)
    hashes["git_sha256"].update(header)
    count = 0
    while chunk := stream.read(1024 * 1024):
        count += len(chunk)
        for h in hashes.values():
            h.update(chunk)
        if sink is not None:
            sink.write(chunk)
    require(count == size, "File size changed during read")
    return {name: h.hexdigest() for name, h in hashes.items()}


def verify_hash(hashes, blob):
    if blob.startswith("sha256:"):
        actual, expected = hashes["sha256"], blob[7:]
    else:
        actual, expected = hashes["git_sha1" if len(blob) == 40 else "git_sha256"], blob
    require(actual == expected, "Final bytes do not match manifest blob")


def write_entry(root, entry, stream, size):
    path = root / entry["path"]
    path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    # The namespace was validated before creation; symlinks are added last.
    if entry["mode"] == "120000":
        require(size <= 4096, "Symlink target is too long")
        data = stream.read(size + 1)
        hashes = file_hash(io.BytesIO(data), size)
        target = os.fsdecode(data)
        require(target and "\0" not in target and "\\" not in target
                and not target.startswith("/") and not metadata(target),
                "Unsafe symlink target")
        entry["target"] = target
    else:
        with path.open("xb") as sink:
            hashes = file_hash(stream, size, sink)
        path.chmod(0o755 if entry["mode"] == "100755" else 0o644)
    verify_hash(hashes, entry["blob"])
    entry.update(sha256=hashes["sha256"], size=size)


def validate_links(manifest):
    # Resolve the final virtual namespace, including chains, '..' after links,
    # dangling links and cycles. Never consult files outside the staging tree.
    for path, entry in manifest.items():
        if entry["mode"] != "120000":
            continue
        pending = deque(entry["target"].split("/"))
        stack = path.split("/")[:-1]
        hops = 0
        while pending:
            part = pending.popleft()
            if part in ("", "."):
                continue
            if part == "..":
                require(bool(stack), "Symlink escapes workspace")
                stack.pop()
                continue
            require(part.lower() != ".git", "Symlink targets Git metadata")
            stack.append(part)
            target = manifest.get("/".join(stack))
            if target and target["mode"] == "120000":
                hops += 1
                require(hops <= 40, "Cyclic or excessively deep symlink chain")
                stack.pop()
                pending.extendleft(reversed(target["target"].split("/")))


def safe_open(root, relative_path):
    """Open a host content file without traversing symlinks at any component."""
    root = canonical_host(root)
    relative(relative_path)
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        parts = relative_path.split("/")
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        stream = os.fdopen(leaf, "rb")
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            stream.close()
            raise MaterializeError("Content source is not a regular file")
        return stream
    finally:
        os.close(fd)


def overlay_entry(root, entry, value, envs, control, blob_dir, overlay_root):
    if "content_path" in value:
        require(overlay_root is not None, "content_path requires overlay_root")
        with safe_open(overlay_root, value["content_path"]) as stream:
            write_entry(root, entry, stream, os.fstat(stream.fileno()).st_size)
        return
    blob = value["blob"]
    if not blob.startswith("sha256:"):
        for env in envs:
            try:
                kind = git(["cat-file", "-t", blob], env=env).strip()
            except MaterializeError:
                continue
            require(kind == b"blob", "Overlay object is not a blob")
            # Spool one blob, keeping RAM bounded even for large binary files.
            with tempfile.TemporaryFile(dir=control) as stream:
                git(["cat-file", "blob", blob], env=env, stdout=stream)
                size = stream.tell()
                stream.seek(0)
                write_entry(root, entry, stream, size)
            return
    require(blob_dir is not None, "Override blob is unavailable")
    with safe_open(blob_dir, blob.removeprefix("sha256:")) as stream:
        write_entry(root, entry, stream, os.fstat(stream.fileno()).st_size)


def scan(root, *, include_git=False):
    """lstat walk: no symlink dereferences, hardlinks, sockets or device files."""
    result = {}

    def walk(directory, prefix=""):
        for child in sorted(directory.iterdir()):
            name = prefix + child.name
            if not include_git and name == ".git":
                continue
            require(include_git or not metadata(name), "Unexpected nested Git metadata")
            info = child.lstat()
            if stat.S_ISDIR(info.st_mode):
                result[name] = {"kind": "dir", "mode": stat.S_IMODE(info.st_mode)}
                walk(child, name + "/")
            elif stat.S_ISLNK(info.st_mode):
                target = os.readlink(child)
                data = os.fsencode(target)
                result[name] = dict(kind="link", mode="120000", target=target,
                                    size=len(data), **file_hash(io.BytesIO(data), len(data)))
            else:
                require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
                        "Unexpected special file or hardlink")
                mode = stat.S_IMODE(info.st_mode)
                require(mode in (0o644, 0o755, 0o600, 0o444), "Unexpected file permissions")
                with child.open("rb") as stream:
                    hashes = file_hash(stream, info.st_size)
                result[name] = dict(kind="file", mode="100755" if mode & 0o111 else "100644",
                                    permissions=mode, size=info.st_size, **hashes)
    walk(root)
    return result


def audit(root, manifest):
    """Audit actual workspace paths, modes, bytes and links against a private manifest.

    The root synthetic .git is deliberately excluded; materialize audits it separately.
    """
    root = canonical_host(root)
    expected = {}
    directories = set()
    for row in manifest:
        entry = dict(row)
        path = relative(entry["path"])
        require(not metadata(path) and path not in expected and entry["mode"] in MODES,
                "Invalid audit manifest")
        expected[path] = entry
        parts = path.split("/")
        directories.update("/".join(parts[:i]) for i in range(1, len(parts)))
    actual = scan(root)
    require(set(actual) == set(expected) | directories, "Workspace paths differ from manifest")
    for path in directories:
        require(actual[path]["kind"] == "dir" and actual[path]["mode"] == 0o755,
                "Workspace parent is not a normal directory")
    for path, entry in expected.items():
        got = actual[path]
        require(got["mode"] == entry["mode"], "Workspace mode differs from manifest")
        require(got["kind"] == ("link" if entry["mode"] == "120000" else "file"),
                "Workspace entry type differs from manifest")
        if got["kind"] == "file":
            require(got["permissions"] == (0o755 if entry["mode"] == "100755" else 0o644),
                    "Workspace permission bits differ from manifest")
        verify_hash(got, entry["blob"])
        if "sha256" in entry:
            require(got["sha256"] == entry["sha256"], "Workspace digest differs from manifest")
        if "size" in entry:
            require(got["size"] == entry["size"], "Workspace size differs from manifest")
        if got["kind"] == "link":
            entry["target"] = got["target"]
            require(entry["target"] and not entry["target"].startswith("/")
                    and "\\" not in entry["target"] and not metadata(entry["target"]),
                    "Unsafe symlink in workspace")
    validate_links(expected)
    return {"files": len(expected), "bytes": sum(actual[p]["size"] for p in expected)}


def synthetic_git(root, manifest):
    git(["init", "--quiet", "--template=", "--initial-branch=snapshot",
         "--object-format=sha1", root])
    (root / ".git/info").mkdir(exist_ok=True)
    (root / ".git/info/attributes").write_text(RAW_ATTRIBUTES)
    env = clean_env()
    env.update(GIT_DIR=str(root / ".git"), GIT_WORK_TREE=str(root))
    # Plumbing avoids .gitignore, filters, LFS, EOL conversion and signing.
    records = []
    for path, entry in sorted(manifest.items()):
        if entry["mode"] == "120000":
            oid = git(["hash-object", "-w", "--stdin"], env=env,
                      data=os.fsencode(os.readlink(root / path))).strip()
        else:
            oid = git(["hash-object", "-w", "--no-filters", "--", root / path], env=env).strip()
        require(oid.decode() == scan_hash_id(entry, root / path),
                "Synthetic Git blob differs from manifest bytes")
        records.append(entry["mode"].encode() + b" " + oid + b"\t" + os.fsencode(path) + b"\0")
    git(["update-index", "-z", "--index-info"], env=env, data=b"".join(records))
    tree = git(["write-tree"], env=env).strip()
    commit = git(["-c", "commit.gpgSign=false", "commit-tree", tree.decode()],
                 env=env, data=b"Independent snapshot\n").strip()
    git(["-c", "core.logAllRefUpdates=false", "update-ref", "refs/heads/snapshot",
         commit.decode()], env=env)
    # Hash-object verified every index blob; check the resulting repository too.
    git(["update-index", "--refresh"], env=env)
    require(not git(["status", "--porcelain", "--untracked-files=all"], env=env).strip(),
            "Synthetic checkout does not start clean")
    require(git(["rev-list", "--count", "--all"], env=env).strip() == b"1",
            "Synthetic repository has inherited history")
    reachable = {line.split()[0] for line in
                 git(["rev-list", "--objects", "--all"], env=env).splitlines()}
    objects = set(git(["cat-file", "--batch-all-objects", "--batch-check=%(objectname)"],
                      env=env).splitlines())
    require(objects == reachable, "Synthetic repository has extra objects")
    require(not git(["remote"], env=env).strip(), "Synthetic repository has remotes")
    for forbidden in ("objects/info/alternates", "objects/info/http-alternates", "hooks",
                      "logs", "shallow", "commondir", "worktrees"):
        require(not (root / ".git" / forbidden).exists(), "Inherited Git metadata")
    return commit.decode()


def scan_hash_id(entry, path):
    # Compute independently from the newly written object rather than trusting
    # hash-object's return value, including when input used plain SHA-256 IDs.
    if entry["mode"] == "120000":
        data = os.fsencode(os.readlink(path))
        return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    with path.open("rb") as stream:
        return file_hash(stream, path.stat().st_size)["git_sha1"]


def snapshot_data_filter(member, destination):
    """Keep data-filter protections without rewriting Git symlink blob bytes.

    CPython's newer data filter normalizes link targets. A trailing slash is
    part of a Git symlink blob, so removing it dirties an otherwise exact tree.
    Only restore trailing slashes; other normalization changes fail closed.
    Call after the transport digest/namespace checks and retain Git clean checks.
    Imports are local so snapshot_data_filter_source() is standalone in a guest.
    """
    import copy
    import os
    import tarfile

    filtered = tarfile.data_filter(member, destination)
    if filtered is None or not member.issym() or filtered.linkname == member.linkname:
        return filtered
    if not member.linkname or member.linkname.rstrip("/") != filtered.linkname:
        raise tarfile.FilterError("Snapshot symlink normalization changes non-trailing components")
    root = os.path.realpath(destination)
    target = os.path.realpath(os.path.join(root, os.path.dirname(filtered.name), member.linkname))
    if os.path.commonpath([root, target]) != root:
        raise tarfile.FilterError("Original snapshot symlink target escapes destination")
    # Preserve all other safe-filter decisions, including permissions and owners.
    filtered = copy.copy(filtered)
    filtered.linkname = member.linkname
    return filtered


def snapshot_data_filter_source():
    """Embed this checked filter in a driver-v2 UNPACK_PROGRAM, without mounting code."""
    import inspect
    return inspect.getsource(snapshot_data_filter) + "\n"


def export_tar(root, target):
    expected = scan(root, include_git=True)
    with tarfile.open(target, "w", format=tarfile.PAX_FORMAT) as archive:
        for path, entry in expected.items():
            info = archive.gettarinfo(str(root / path), arcname=path)
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mtime = 0
            info.pax_headers = {}
            if info.isfile():
                with (root / path).open("rb") as stream:
                    archive.addfile(info, stream)
            else:
                archive.addfile(info)
    # Read the actual completed tar and compare bytes, targets, types and modes.
    seen = set()
    with tarfile.open(target, "r:") as archive:
        for member in archive:
            name = member.name.rstrip("/") if member.isdir() else member.name
            require(name in expected and name not in seen, "Tar namespace audit failed")
            seen.add(name)
            entry = expected[name]
            if entry["kind"] == "file":
                require(member.isfile() and member.mode == entry["permissions"],
                        "Tar file type or mode changed")
                with archive.extractfile(member) as stream:
                    hashes = file_hash(stream, member.size)
                require(member.size == entry["size"] and hashes["sha256"] == entry["sha256"],
                        "Tar bytes differ from audited checkout")
            elif entry["kind"] == "link":
                require(member.issym() and member.linkname == entry["target"],
                        "Tar symlink changed")
            else:
                require(member.isdir() and member.mode == entry["mode"], "Tar directory changed")
    require(seen == set(expected), "Tar omitted checkout entries")
    digest = hashlib.sha256()
    with target.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def publish(source, destination):
    # Linux renameat2 is atomic and refuses an existing destination even if a
    # competing creator appears after validation. No unsafe check+rename fallback.
    libc = ctypes.CDLL(None, use_errno=True)
    require(hasattr(libc, "renameat2"), "Atomic no-replace publication requires Linux renameat2")
    fn = libc.renameat2
    fn.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    fn.restype = ctypes.c_int
    if fn(-100, os.fsencode(source), -100, os.fsencode(destination), 1) != 0:
        code = ctypes.get_errno()
        raise MaterializeError("Output exists" if code == errno.EEXIST
                               else "Atomic output publication failed")


def materialize(repo, commit, overrides, out, *, tree=None, blob_repo=None,
                blob_dir=None, overlay_root=None, format="directory"):
    """Materialize exactly one sanitized snapshot; return a HOST-PRIVATE report."""
    try:
        require(format in {"directory", "tar"}, "Format must be directory or tar")
        overrides = normalize_overrides(overrides)
        out = canonical_host(out)
        require(out.parent.is_dir() and not os.path.lexists(out), "Output parent missing or output exists")
        source = canonical_host(repo)
        # Never place temporary files in the source repository or blob inputs.
        for input_root in (source, blob_repo, blob_dir, overlay_root):
            if input_root is not None:
                require(not out.is_relative_to(canonical_host(input_root)),
                        "Output must be outside private input roots")
        with tempfile.TemporaryDirectory(prefix=".materialize-", dir=out.parent) as scratch:
            control = Path(scratch)
            root = control / "checkout"
            root.mkdir(mode=0o755)
            env, _ = source_store(source, control, "source.git")
            selected_tree, base, stripped = source_manifest(env, commit, tree)
            final = final_manifest(base, overrides)
            if stripped:
                selected_tree = sanitized_archive_tree(base, env)
            # Archive selected base directly, but honor the independently derived
            # manifest rather than tar paths/permissions. Never extractall().
            archive_path = control / "base.tar"
            with archive_path.open("wb") as stream:
                git(["archive", "--format=tar", selected_tree], env=env, stdout=stream)
            needed = set(final) - {p for p, v in overrides.items() if v is not None}
            seen = set()
            with tarfile.open(archive_path, "r:") as archive:
                for member in archive:
                    path = member.name.rstrip("/") if member.isdir() else member.name
                    relative(path)
                    if metadata(path) or member.isdir():
                        continue
                    require(not member.islnk() and (member.isfile() or member.issym()),
                            "Unsupported archive entry")
                    if path not in needed:
                        continue
                    require(path not in seen, "Duplicate archive entry")
                    seen.add(path)
                    entry = final[path]
                    require(member.issym() == (entry["mode"] == "120000"), "Archive type mismatch")
                    if member.issym():
                        data = os.fsencode(member.linkname)
                        write_entry(root, entry, io.BytesIO(data), len(data))
                    else:
                        with archive.extractfile(member) as stream:
                            write_entry(root, entry, stream, member.size)
            require(seen == needed, "Archive omitted manifest files")
            archive_path.unlink()
            envs = [env]
            if blob_repo is not None:
                envs.append(source_store(blob_repo, control, "blobs.git")[0])
            for path, value in sorted(overrides.items()):
                if value is not None:
                    overlay_entry(root, final[path], value, envs, control, blob_dir, overlay_root)
            validate_links(final)
            for path, entry in final.items():
                if entry["mode"] == "120000":
                    (root / path).symlink_to(entry["target"])
            # Normalize directory permissions despite caller umask.
            for directory, _, _ in os.walk(root, followlinks=False):
                Path(directory).chmod(0o755)
            manifest = [final[p] for p in sorted(final)]
            report = audit(root, manifest)
            report["synthetic_commit"] = synthetic_git(root, final)
            audit(root, manifest)
            report["manifest"] = manifest
            report["stripped_paths"] = stripped
            if format == "tar":
                archive_path = control / "snapshot.tar"
                report["tar_sha256"] = export_tar(root, archive_path)
                archive_path.chmod(0o600)
                publish(archive_path, out)
            else:
                publish(root, out)
            return report
    except (OSError, tarfile.TarError, UnicodeError, RuntimeError) as exc:
        raise MaterializeError("Materialization failed: invalid filesystem or archive") from exc


def load_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    with open(path, encoding="utf-8") as stream:
        return json.load(stream, object_pairs_hook=pairs)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    base = parser.add_mutually_exclusive_group(required=True)
    base.add_argument("--commit")
    base.add_argument("--tree")
    parser.add_argument("--overrides", required=True, help="Host-private overrides JSON file")
    parser.add_argument("--out", required=True)
    parser.add_argument("--blob-repo")
    parser.add_argument("--blob-dir")
    parser.add_argument("--overlay-root")
    parser.add_argument("--format", choices=("directory", "tar"), default="directory")
    args = parser.parse_args(argv)
    try:
        report = materialize(args.repo, args.commit, load_json(args.overrides), args.out,
                             tree=args.tree, blob_repo=args.blob_repo, blob_dir=args.blob_dir,
                             overlay_root=args.overlay_root, format=args.format)
    except (MaterializeError, OSError, ValueError) as exc:
        parser.exit(2, f"materialize: {exc}\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"manifest", "stripped_paths"}},
                     sort_keys=True))


if __name__ == "__main__":
    main()
