import hashlib, json, os, pathlib, shutil, subprocess
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
