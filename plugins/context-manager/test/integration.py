#!/usr/bin/env python3
"""Exercise the actual upstream CLI with a loopback-only provider."""
import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time


EXPECTED_BINARY_SHA256 = "14d26f3eee4a0770e8a5c27103bee0998f79a91c052eb6629cd7f0e8bcdae1b9"


def run(root, mode, binary, output_dir=None):
    binary = binary.expanduser().resolve()
    if not binary.is_file():
        raise SystemExit("Set OPENCODE_TEST_BINARY or --binary to the pinned OpenCode 1.18.2 executable")
    with binary.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != EXPECTED_BINARY_SHA256:
        raise SystemExit("OpenCode binary SHA-256 does not match the measured 1.18.2 executable")
    destination = Path(tempfile.mkdtemp(prefix="context-integration-" + mode + "-", dir=output_dir)).resolve()
    print(f"Integration evidence: {destination}", flush=True)
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(body)
            messages = body.get("messages", [])
            system = str(messages[0].get("content", "")) if messages else ""
            if "You manage the context" in system:
                data = json.loads(messages[-1]["content"])
                text = data["current"]["text"]
                topic = "csv" if "CSV" in text else "login"
                content = json.dumps({
                    "context_id": topic, "title": topic, "confidence": 0.98,
                    "related_context_ids": [], "shared_turn_ids": [], "evidence_turn_ids": [],
                })
                kind = "route"
            elif "You maintain evidence-bearing" in system:
                data = json.loads(messages[-1]["content"])
                first = data["completed_interactions"][0]
                content = json.dumps({
                    "goal": data["context"]["title"],
                    "constraints": [{"text": "Preserve the stated interface", "source_ids": [first["user_id"]]}],
                    "progress": [{"text": "The earlier assistant supplied a response", "source_ids": [first["messages"][-1]["id"]]}],
                    "pending": ["Verify the next requested change"], "files": [], "uncertainties": [],
                })
                kind = "memory"
            elif "You are a title generator" in system:
                content = "Local context integration"
                kind = "native_title"
            else:
                content = "Acknowledged. The requested development work has been considered."
                kind = "main"
            body["_probe_kind"] = kind
            (destination / "requests.json").write_text(json.dumps(requests, indent=2))
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream" if body.get("stream") else "application/json")
            self.end_headers()
            common = {"id": "chatcmpl-local", "created": int(time.time()), "model": body["model"]}
            if body.get("stream"):
                chunks = [
                    {**common, "object": "chat.completion.chunk", "choices": [{"index": 0, "delta": {"role": "assistant", "content": content}, "finish_reason": None}]},
                    {**common, "object": "chat.completion.chunk", "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}},
                ]
                for chunk in chunks:
                    self.wfile.write(("data: " + json.dumps(chunk) + "\n\n").encode())
                self.wfile.write(b"data: [DONE]\n\n")
            else:
                self.wfile.write(json.dumps({
                    **common, "object": "chat.completion",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 100, "completion_tokens": 20},
                }).encode())

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    home = destination / "home"
    workspace = destination / "workspace"
    workspace.mkdir()
    subprocess.run(["git", "init", "-q", str(workspace)], check=True)
    config = {
        "model": "deepseek/deepseek-flash", "share": "disabled", "autoupdate": False,
        "provider": {"deepseek": {
            "options": {"baseURL": f"http://127.0.0.1:{server.server_port}/v1", "apiKey": "FAKE_LOCAL_KEY"},
            "models": {"deepseek-flash": {"name": "Loopback", "limit": {"context": 1000000, "output": 8192}, "tool_call": True}},
        }},
    }
    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / "config"), "XDG_DATA_HOME": str(home / "data"),
        "XDG_CACHE_HOME": str(home / "cache"), "XDG_STATE_HOME": str(home / "state"),
        "OPENCODE_CONFIG_CONTENT": json.dumps(config), "OPENCODE_CONTEXT_MODE": mode,
        "OPENCODE_PLUS_ROOT": str(root),
        "OPENCODE_UPSTREAM_BIN": str(binary),
        "OPENCODE_DISABLE_AUTOUPDATE": "true", "OPENCODE_DISABLE_MODELS_FETCH": "true",
        "OPENCODE_DISABLE_DEFAULT_PLUGINS": "true", "NO_COLOR": "true",
        "OPENCODE_DISABLE_PROJECT_CONFIG": "true",
        "npm_config_offline": "true",
    }
    session = None
    prompts = [
        "Investigate authentication. Preserve the stated interface. LOGIN_ORIGINAL_MARKER.",
        "Investigate CSV quoting instead. CSV_DISTRACTOR_MARKER.",
        "Return to authentication. LOGIN_RETURN_MARKER.",
    ]
    try:
        version = subprocess.run([str(binary), "--version"], env=env, cwd=workspace,
                                 capture_output=True, text=True, timeout=30)
        assert version.returncode == 0 and version.stdout.strip() == "1.18.2", version
        for index, prompt in enumerate(prompts):
            args = [str(root / "opencode_plus"), "run", "--format", "json", "--model", config["model"], "--auto"]
            if session:
                args += ["--session", session]
            args += ["--", prompt]
            try:
                completed = subprocess.run(args, cwd=workspace, env=env, capture_output=True, timeout=90)
            except subprocess.TimeoutExpired as error:
                (destination / f"turn-{index}.stdout").write_bytes(error.stdout or b"")
                (destination / f"turn-{index}.stderr").write_bytes(error.stderr or b"")
                (destination / "requests.json").write_text(json.dumps(requests, indent=2))
                raise
            (destination / f"turn-{index}.stdout").write_bytes(completed.stdout)
            (destination / f"turn-{index}.stderr").write_bytes(completed.stderr)
            events = []
            for line in completed.stdout.decode(errors="replace").splitlines():
                try:
                    events.append(json.loads(line))
                except ValueError:
                    continue
            sessions = {row.get("sessionID") for row in events if row.get("sessionID")}
            assert completed.returncode == 0, f"CLI exit {completed.returncode}; evidence {destination}"
            assert len(sessions) == 1, f"Missing native session; evidence {destination}"
            next_session = sessions.pop()
            assert session is None or next_session == session
            session = next_session
        main = [r for r in requests if r["_probe_kind"] == "main" and r.get("stream")]
        assert len(main) == 3, (len(main), destination)
        last = json.dumps(main[-1]["messages"])
        assert "LOGIN_RETURN_MARKER" in last
        assert "LOGIN_ORIGINAL_MARKER" in last
        assert ("CSV_DISTRACTOR_MARKER" in last) == (mode == "off")
        if mode == "x":
            assert "Historical context state" in last
        else:
            assert "Historical context state" not in last
        if mode == "off":
            assert not any(r["_probe_kind"] in {"route", "memory"} for r in requests)
        exported = subprocess.run([str(root / "opencode_plus"), "export", session],
                                  cwd=workspace, env=env, capture_output=True, timeout=30)
        assert exported.returncode == 0
        export = json.loads(exported.stdout)
        (destination / "native-export.json").write_text(json.dumps(export))
        assert "CSV_DISTRACTOR_MARKER" in json.dumps(export)
        assert "Historical context state" not in json.dumps(export)
        result = {"passed": True, "mode": mode, "session": session, "real_upstream_model_calls": 0,
                  "requests": {kind: sum(r["_probe_kind"] == kind for r in requests) for kind in ["route", "memory", "main"]},
                  "raw_history_preserved": True, "provider_projection_verified": True,
                  "upstream_version": version.stdout.strip(), "upstream_sha256": digest}
        (destination / "requests.json").write_text(json.dumps(requests, indent=2))
        (destination / "result.json").write_text(json.dumps(result, indent=2))
        print(json.dumps({"directory": str(destination), **result}), flush=True)
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["a", "x", "off"], default="x")
    parser.add_argument("--binary", type=Path, default=Path(os.environ.get(
        "OPENCODE_TEST_BINARY", str(Path(__file__).resolve().parents[1] / ".runtime/upstream/opencode"))))
    parser.add_argument("--output-dir", type=Path, help="Existing parent directory for temporary evidence")
    args = parser.parse_args()
    run(Path(__file__).resolve().parents[1], args.mode, args.binary, args.output_dir)
