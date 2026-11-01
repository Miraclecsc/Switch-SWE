#!/usr/bin/python3
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
