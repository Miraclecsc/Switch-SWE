"""Public preparer integration tests using tiny, temporary bare repositories."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/prepare_workspaces.py"
spec = importlib.util.spec_from_file_location("prepare_workspaces", SCRIPT)
preparer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preparer)


def git(repo, *args, data=None, check=True):
    from switch_swe.materialize import clean_env

    return subprocess.run(
        ["git", "-C", str(repo), *args], input=data, capture_output=True,
        env=clean_env(), check=check,
    )


class PrepareWorkspacesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="prepare-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cache = self.root / "cache"
        self.repo = self.cache / "example/project.git"
        self.repo.mkdir(parents=True)
        git(self.repo, "init", "--bare", "--quiet", "--template=")
        self.base, self.base_blob = self.commit(b"original\r\n")
        self.future, self.future_blob = self.commit(b"future solution secret", parent=self.base)
        git(self.repo, "update-ref", "refs/heads/main", self.future)
        git(self.repo, "remote", "add", "origin", "https://example.invalid/private.git")
        self.data = self.root / "data"
        (self.data / "blobs").mkdir(parents=True)
        self.case_id = "sf001_switched"
        self.out = self.root / "prepared"
        self.cases = [{
            "case_id": self.case_id, "pair_id": "sf001", "condition": "switched",
            "workspaces": [
                {"workspace": name, "repo": "example/project", "commit": self.base}
                for name in ("w00", "w01")
            ],
            "turns": [{"prompt": "Preserve frozen input bytes."}],
        }]
        self.contents = b"public initial\0bytes\r\n\xff"
        self.entry = self.overlay(self.contents, mode="100755")
        self.overlays = {self.case_id: {
            "w00": {"source.txt": self.entry, "delete.txt": None,
                    "link": self.overlay(b"source.txt", mode="120000")},
            "w01": {},
        }}
        self.save()

    def commit(self, content, parent=None):
        blob = git(self.repo, "hash-object", "-w", "--stdin", data=content).stdout.strip().decode()
        tree = git(self.repo, "mktree", data=(
            f"100644 blob {blob}\tsource.txt\n"
            f"100644 blob {blob}\tdelete.txt\n"
        ).encode()).stdout.strip().decode()
        args = ["commit-tree", tree]
        if parent:
            args.extend(["-p", parent])
        commit = git(self.repo, *args, data=b"source history\n").stdout.strip().decode()
        return commit, blob

    def overlay(self, content, mode="100644"):
        digest = hashlib.sha256(content).hexdigest()
        (self.data / "blobs" / digest).write_bytes(content)
        return {"mode": mode, "sha256": digest, "content_path": "blobs/" + digest}

    def save(self):
        (self.data / "cases.json").write_text(
            json.dumps(self.cases, indent=3, ensure_ascii=False) + "\n", encoding="utf-8")
        (self.data / "workspace_overlays.json").write_text(
            json.dumps(self.overlays, indent=2), encoding="utf-8")

    def run_cli(self, *extra, data_dir=True):
        args = [sys.executable, "-B", str(SCRIPT), "--case-id", self.case_id,
                "--repo-cache", str(self.cache), "--out-dir", str(self.out)]
        if data_dir:
            args.extend(["--data-dir", str(self.data)])
        return subprocess.run([*args, *extra], cwd=self.root, capture_output=True, text=True)

    def prepare(self, **kwargs):
        return preparer.prepare_case(
            self.case_id, self.cache, self.out, data_dir=self.data, **kwargs)

    def assert_no_output(self):
        self.assertFalse(self.out.exists())
        self.assertEqual(list(self.root.glob(".prepare-workspaces-*")), [])
        self.assertEqual(list(self.root.glob(".materialize-*")), [])

    def test_cli_all_workspaces_bytes_modes_deletion_and_isolated_git(self):
        before = {
            str(path): (path.read_bytes(), path.stat().st_mtime_ns)
            for source in (self.data, self.cache)
            for path in source.rglob("*") if path.is_file()
        }
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual([w["workspace"] for w in report["workspaces"]], ["w00", "w01"])
        self.assertEqual({p.name for p in self.out.iterdir()}, {"w00", "w01"})
        a, b = self.out / "w00", self.out / "w01"
        self.assertEqual((a / "source.txt").read_bytes(), self.contents)
        self.assertEqual((a / "source.txt").stat().st_mode & 0o777, 0o755)
        self.assertFalse((a / "delete.txt").exists())
        self.assertEqual(os.readlink(a / "link"), "source.txt")
        self.assertEqual((b / "source.txt").read_bytes(), b"original\r\n")
        self.assertEqual((b / "source.txt").stat().st_mode & 0o777, 0o644)
        self.assertTrue((b / "delete.txt").exists())
        for workspace in (a, b):
            self.assertEqual(git(workspace, "rev-list", "--count", "--all").stdout.strip(), b"1")
            self.assertEqual(git(workspace, "status", "--porcelain").stdout, b"")
            self.assertEqual(git(workspace, "remote").stdout, b"")
            for oid in (self.base, self.future, self.future_blob):
                self.assertNotEqual(git(workspace, "cat-file", "-e", oid, check=False).returncode, 0)
            self.assertFalse((workspace / ".git/objects/info/alternates").exists())
            reachable = {
                line.split()[0] for line in
                git(workspace, "rev-list", "--objects", "--all").stdout.splitlines()
            }
            objects = set(git(workspace, "cat-file", "--batch-all-objects",
                              "--batch-check=%(objectname)").stdout.splitlines())
            self.assertEqual(objects, reachable)
        after = {
            str(path): (path.read_bytes(), path.stat().st_mtime_ns)
            for source in (self.data, self.cache)
            for path in source.rglob("*") if path.is_file()
        }
        self.assertEqual(before, after)
        (a / "source.txt").write_bytes(b"local edit")
        self.assertEqual((b / "source.txt").read_bytes(), b"original\r\n")
        git(a, "update-ref", "refs/heads/local", "HEAD")
        self.assertNotEqual(git(b, "show-ref", "--verify", "refs/heads/local",
                               check=False).returncode, 0)

    def test_dry_run_missing_cache_prints_requirements_without_git_or_writes(self):
        self.cache = self.root / "missing cache"
        self.out = self.root / "missing parent" / "case"
        before = sorted(str(p) for p in self.root.rglob("*"))
        with patch("subprocess.run", side_effect=AssertionError("dry-run must not call git")):
            report = self.prepare(dry_run=True)
        self.assertEqual(sorted(str(p) for p in self.root.rglob("*")), before)
        self.assertTrue(report["dry_run"])
        self.assertEqual(len(report["repositories"]), 1)
        repository = report["repositories"][0]
        self.assertFalse(repository["cache_exists"])
        self.assertEqual(repository["commits"], [self.base])
        self.assertIn("git clone --bare", repository["clone_command"])
        self.assertIn("https://github.com/example/project.git", repository["clone_command"])
        self.assertEqual(len(report["workspaces"]), 2)
        self.assertFalse(self.cache.exists())
        result = self.run_cli("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), report)

    def test_missing_cache_never_clones(self):
        self.cache = self.root / "missing-cache"
        with patch("subprocess.run", side_effect=AssertionError("must not fetch or clone")):
            with self.assertRaisesRegex(preparer.MaterializeError, "Missing bare"):
                self.prepare()
        self.assertFalse(self.cache.exists())
        self.assert_no_output()

    def test_late_bad_digest_rolls_back_entire_case(self):
        self.overlays[self.case_id]["w01"] = {
            "source.txt": dict(self.entry, sha256="0" * 64, content_path="blobs/" + "0" * 64),
        }
        (self.data / "blobs" / ("0" * 64)).write_bytes(b"incorrect digest")
        self.save()
        result = self.run_cli()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("bytes do not match", result.stderr)
        self.assert_no_output()

    def test_reuse_and_competing_output_are_refused(self):
        self.prepare()
        sentinel = self.out / "w00/source.txt"
        sentinel.write_bytes(b"user edits")
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(sentinel.read_bytes(), b"user edits")
        self.out = self.root / "racing-output"
        publish = preparer.publish

        def competing_creator(source, destination):
            destination.mkdir()
            (destination / "sentinel").write_bytes(b"concurrent writer")
            publish(source, destination)

        with patch.object(preparer, "publish", side_effect=competing_creator):
            with self.assertRaises(preparer.MaterializeError):
                self.prepare()
        self.assertEqual(list(p.name for p in self.out.iterdir()), ["sentinel"])
        self.assertEqual((self.out / "sentinel").read_bytes(), b"concurrent writer")
        self.assertEqual(list(self.root.glob(".prepare-workspaces-*")), [])

    def test_missing_or_wrong_commit_fails_without_partial_case(self):
        for commit in ("0" * 40, self.base_blob):
            with self.subTest(commit=commit):
                self.cases[0]["workspaces"][1]["commit"] = commit
                self.save()
                with self.assertRaises(preparer.MaterializeError):
                    self.prepare()
                self.assert_no_output()

    def test_non_bare_repository_rejected(self):
        work = self.cache / "example/work.git"
        work.mkdir()
        git(work, "init", "--quiet", "--template=")
        self.cases[0]["workspaces"][0]["repo"] = "example/work"
        self.save()
        with self.assertRaises(preparer.MaterializeError):
            self.prepare()
        self.assert_no_output()

    def test_unknown_case_and_missing_overlay_workspace_rejected(self):
        with self.assertRaisesRegex(preparer.MaterializeError, "Unknown case_id"):
            preparer.prepare_case("absent", self.cache, self.out, data_dir=self.data)
        del self.overlays[self.case_id]["w01"]
        self.save()
        with self.assertRaisesRegex(preparer.MaterializeError, "Missing overlay map"):
            self.prepare()
        self.assert_no_output()

    def test_duplicate_case_and_workspace_rejected(self):
        self.cases.append(self.cases[0])
        self.save()
        with self.assertRaisesRegex(preparer.MaterializeError, "Duplicate case_id"):
            self.prepare()
        self.cases.pop()
        self.cases[0]["workspaces"][1]["workspace"] = "w00"
        self.save()
        with self.assertRaisesRegex(preparer.MaterializeError, "Duplicate workspace"):
            self.prepare()
        self.assert_no_output()

    def test_rejects_unsafe_names_and_noncanonical_public_blob_paths(self):
        for key, value in (("workspace", "../escape"), ("workspace", ".git"),
                           ("repo", "../../escape"), ("repo", "example/../../escape"),
                           ("commit", "main")):
            with self.subTest(key=key, value=value):
                original = self.cases[0]["workspaces"][0][key]
                self.cases[0]["workspaces"][0][key] = value
                self.save()
                with self.assertRaises(preparer.MaterializeError):
                    self.prepare()
                self.cases[0]["workspaces"][0][key] = original
                self.assert_no_output()
        self.overlays[self.case_id]["w00"]["source.txt"]["content_path"] = "../secret"
        self.save()
        with self.assertRaises(preparer.MaterializeError):
            self.prepare()
        self.assert_no_output()

    def test_output_inside_inputs_and_symlink_output_rejected(self):
        for self.out in (self.cache / "case", self.data / "case"):
            with self.assertRaisesRegex(preparer.MaterializeError, "outside"):
                self.prepare()
        self.out = self.root / "link-output"
        self.out.symlink_to(self.root / "missing")
        with self.assertRaises(preparer.MaterializeError):
            self.prepare()
        self.assertTrue(self.out.is_symlink())

    def test_symlink_blob_and_duplicate_json_key_rejected(self):
        blob = self.data / self.entry["content_path"]
        original = self.root / "original"
        original.write_bytes(blob.read_bytes())
        blob.unlink()
        blob.symlink_to(original)
        with self.assertRaises(preparer.MaterializeError):
            self.prepare()
        self.assert_no_output()
        (self.data / "workspace_overlays.json").write_text('{"duplicate": {}, "duplicate": {}}')
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("Duplicate JSON key", result.stderr)
        self.assert_no_output()


if __name__ == "__main__":
    unittest.main()
