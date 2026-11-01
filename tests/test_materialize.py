"""Behavioral tests; all repositories and outputs are disposable."""
import hashlib
import importlib.util
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "src/switch_swe/materialize.py"


def git(repo, *args, data=None, check=True):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null",
               GIT_AUTHOR_NAME="Private Author", GIT_AUTHOR_EMAIL="secret@example.test",
               GIT_COMMITTER_NAME="Private Author", GIT_COMMITTER_EMAIL="secret@example.test")
    return subprocess.run(["git", "-C", str(repo), *args], input=data,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=env, check=check).stdout.strip()


class MaterializeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = None
        if MODULE.exists():
            spec = importlib.util.spec_from_file_location("materialize", MODULE)
            cls.api = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.api)

    def setUp(self):
        self.assertIsNotNone(self.api, "materialize.py API is not implemented")
        self.tmp = tempfile.TemporaryDirectory(prefix="materialize-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "source.git"
        subprocess.run(["git", "init", "--bare", "--quiet", "--template=", str(self.repo)],
                       check=True)
        secret_tree = self.tree({"old-secret.txt": ("100644", b"gold history secret")})
        self.old = git(self.repo, "commit-tree", secret_tree, data=b"private old message\n").decode()
        self.base = self.commit({
            "a.txt": ("100644", b"base\n"), "delete.txt": ("100644", b"remove\n"),
            "dir/run": ("100755", b"#!/bin/sh\nexit 0\n"),
            ".gitignore": ("100644", b"ignored.txt\n"),
            ".gitattributes": ("100644", b"a.txt export-ignore\n*.txt export-subst\n"),
            "format.txt": ("100644", b"$Format:%H$\n"),
        }, parent=self.old)
        git(self.repo, "update-ref", "refs/heads/private", self.base)
        git(self.repo, "remote", "add", "private", "https://secret.invalid/private.git")
        self.out = self.root / "checkout"

    def blob(self, data):
        return git(self.repo, "hash-object", "-w", "--stdin", data=data).decode()

    def tree(self, files):
        # mktree permits malicious names without involving a host checkout.
        nested = {}
        for path, (mode, value) in files.items():
            node = nested
            parts = path.split("/")
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node[parts[-1]] = (mode, value)

        def build(node):
            records = []
            for name, value in node.items():
                if isinstance(value, dict):
                    mode, kind, oid = "040000", "tree", build(value)
                else:
                    mode, content = value
                    kind = "commit" if mode == "160000" else "blob"
                    oid = content if mode == "160000" else self.blob(content)
                records.append(f"{mode} {kind} {oid}\t{name}".encode() + b"\0")
            return git(self.repo, "mktree", "--missing", "-z",
                       data=b"".join(records)).decode()
        return build(nested)

    def commit(self, files, parent=None):
        args = ["commit-tree", self.tree(files)]
        if parent:
            args += ["-p", parent]
        return git(self.repo, *args, data=b"private base message\n").decode()

    def run_materialize(self, overrides=None, **kwargs):
        return self.api.materialize(self.repo, self.base, overrides or {}, self.out, **kwargs)

    def assert_isolated(self, root):
        self.assertEqual(git(root, "rev-list", "--count", "--all"), b"1")
        self.assertEqual(git(root, "remote"), b"")
        self.assertEqual(git(root, "status", "--porcelain"), b"")
        self.assertEqual(git(root, "cat-file", "-e", self.old, check=False), b"")
        proc = subprocess.run(["git", "-C", str(root), "cat-file", "-e", self.old],
                              capture_output=True)
        self.assertNotEqual(proc.returncode, 0)
        reachable = set(git(root, "rev-list", "--objects", "--all").splitlines())
        reachable_ids = {line.split()[0] for line in reachable}
        all_ids = set(git(root, "cat-file", "--batch-all-objects",
                          "--batch-check=%(objectname)").splitlines())
        self.assertEqual(reachable_ids, all_ids, "No unreachable source objects may leak")
        self.assertFalse((root / ".git/objects/info/alternates").exists())
        self.assertFalse((root / ".git/hooks").exists())
        self.assertNotIn(b"secret@example.test", git(root, "cat-file", "commit", "HEAD"))
        self.assertNotIn(self.base.encode(), git(root, "cat-file", "commit", "HEAD"))

    def test_exact_overlay_bytes_modes_attributes_and_history_isolation(self):
        report = self.run_materialize({
            "a.txt": {"mode": "100755", "blob": self.blob(b"changed\0bytes\n")},
            "delete.txt": None,
            "ignored.txt": {"mode": "100644", "blob": self.blob(b"tracked even if ignored")},
        })
        self.assertEqual((self.out / "a.txt").read_bytes(), b"changed\0bytes\n")
        self.assertEqual((self.out / "a.txt").stat().st_mode & 0o777, 0o755)
        self.assertFalse((self.out / "delete.txt").exists())
        self.assertEqual((self.out / "format.txt").read_bytes(), b"$Format:%H$\n")
        self.assertEqual({r["path"] for r in report["manifest"]},
                         {"a.txt", "dir/run", ".gitignore", ".gitattributes",
                          "format.txt", "ignored.txt"})
        self.assert_isolated(self.out)
        (self.out / "a.txt").write_bytes(b"edit\n")
        self.assertIn(b"a.txt", git(self.out, "diff", "--name-only"))

    def test_archive_export_ignore_does_not_omit_base_files(self):
        self.run_materialize()
        self.assertEqual((self.out / "a.txt").read_bytes(), b"base\n")
        self.assert_isolated(self.out)

    def test_nested_git_and_gitlinks_are_stripped(self):
        tree = self.tree({
            "keep": ("100644", b"ok"),
            "nested/.git/config": ("100644", b"secret remote"),
            "nested/.GiT": ("100644", b"gitdir: /private"),
            "submodule": ("160000", self.old),
            ".git": ("120000", b"/private/source.git"),
        })
        report = self.api.materialize(self.repo, None, {}, self.out, tree=tree)
        self.assertEqual([r["path"] for r in report["manifest"]], ["keep"])
        self.assertFalse((self.out / "nested").exists())
        self.assertFalse((self.out / "submodule").exists())
        self.assert_isolated(self.out)

    def test_rejects_path_traversal_and_metadata_overrides(self):
        oid = self.blob(b"attack")
        for path in ("../escape", "/absolute", "a/../../escape", "a//b", "./x",
                     "a/./b", "a\\b", "a/.git/config", ".GIT/x", "a\0b"):
            with self.subTest(path=path), self.assertRaises(self.api.MaterializeError):
                self.run_materialize({path: {"mode": "100644", "blob": oid}})
            self.assertFalse(self.out.exists())

    def test_rejects_unsafe_symlinks_in_base_and_overlay(self):
        for target in (b"/etc/passwd", b"../../escape", b"../.git/config",
                       b"..\\escape", b""):
            with self.subTest(target=target):
                tree = self.tree({"dir/link": ("120000", target)})
                with self.assertRaises(self.api.MaterializeError):
                    self.api.materialize(self.repo, None, {}, self.out, tree=tree)
                with self.assertRaises(self.api.MaterializeError):
                    self.run_materialize({"dir/link": {
                        "mode": "120000", "blob": self.blob(target)}})
                self.assertFalse(self.out.exists())

    def test_safe_symlink_and_parent_symlink_overlay_rejection(self):
        tree = self.tree({"dir/link": ("120000", b"../a.txt"),
                          "a.txt": ("100644", b"target")})
        self.api.materialize(self.repo, None, {}, self.out, tree=tree)
        self.assertTrue((self.out / "dir/link").is_symlink())
        self.assertEqual((self.out / "dir/link").read_bytes(), b"target")
        other = self.root / "other"
        tree = self.tree({"link": ("120000", b"dir"), "dir/a": ("100644", b"ok")})
        with self.assertRaises(self.api.MaterializeError):
            self.api.materialize(self.repo, None, {
                "link/pwn": {"mode": "100644", "blob": self.blob(b"pwn")},
            }, other, tree=tree)
        self.assertFalse(other.exists())

    def test_symlink_chain_escape_and_cycles_rejected(self):
        for files in (
            {"a": ("120000", b"."), "b": ("120000", b"a/../escape")},
            {"a": ("120000", b"b"), "b": ("120000", b"a")},
        ):
            with self.assertRaises(self.api.MaterializeError):
                self.api.materialize(self.repo, None, {}, self.out, tree=self.tree(files))

    def test_cas_blob_bytes_verified_and_no_manifest_in_output(self):
        blobs = self.root / "blobs"
        blobs.mkdir()
        content = b"external overlay\n"
        digest = hashlib.sha256(content).hexdigest()
        (blobs / digest).write_bytes(content)
        report = self.run_materialize({"new": {"mode": "100644", "blob": "sha256:" + digest}},
                                      blob_dir=blobs)
        self.assertEqual((self.out / "new").read_bytes(), content)
        self.assertFalse((self.out / "manifest.json").exists())
        self.assert_isolated(self.out)
        self.api.audit(self.out, report["manifest"])
        (self.out / "new").write_bytes(b"tampered")
        with self.assertRaises(self.api.MaterializeError):
            self.api.audit(self.out, report["manifest"])

    def test_missing_corrupt_and_non_blob_objects_fail_atomically(self):
        blobs = self.root / "blobs"
        blobs.mkdir()
        digest = "0" * 64
        (blobs / digest).write_bytes(b"wrong")
        for oid in ("0" * 40, self.base, "sha256:" + digest):
            with self.subTest(oid=oid), self.assertRaises(self.api.MaterializeError):
                self.run_materialize({"new": {"mode": "100644", "blob": oid}}, blob_dir=blobs)
            self.assertFalse(self.out.exists())
        self.assertFalse(list(self.root.glob(".materialize-*")))

    def test_tree_source_and_separate_original_blob_repo(self):
        other = self.root / "isolated.git"
        subprocess.run(["git", "init", "--bare", "--quiet", "--template=", str(other)], check=True)
        tree = git(other, "mktree", data=b"").decode()
        oid = self.blob(b"only in original")
        self.api.materialize(other, None, {"a": {"mode": "100644", "blob": oid}},
                             self.out, tree=tree, blob_repo=self.repo)
        self.assertEqual((self.out / "a").read_bytes(), b"only in original")
        self.assert_isolated(self.out)

    def test_tar_cli_roundtrip_and_existing_destination_unchanged(self):
        overrides = self.root / "private.json"
        overrides.write_text(json.dumps([{"path": "a.txt", "mode": "100644",
                                         "blob": self.blob(b"tar bytes")}]))
        tar = self.root / "snapshot.tar"
        result = subprocess.run([sys.executable, "-B", str(MODULE), "--repo", str(self.repo),
                                 "--commit", self.base, "--overrides", str(overrides),
                                 "--out", str(tar), "--format", "tar"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertNotIn("manifest", summary)
        self.assertEqual(summary["tar_sha256"], hashlib.sha256(tar.read_bytes()).hexdigest())
        with tarfile.open(tar) as archive:
            self.assertNotIn("private.json", archive.getnames())
            self.assertTrue(all(not m.islnk() for m in archive))
            archive.extractall(self.out, filter="data")
        self.assertEqual((self.out / "a.txt").read_bytes(), b"tar bytes")
        self.assert_isolated(self.out)
        before = tar.read_bytes()
        with self.assertRaises(self.api.MaterializeError):
            self.api.materialize(self.repo, self.base, {}, tar, format="tar")
        self.assertEqual(tar.read_bytes(), before)
        with self.assertRaises(self.api.MaterializeError):
            self.run_materialize()
        self.assertEqual((self.out / "a.txt").read_bytes(), b"tar bytes")

    def test_git_environment_and_templates_cannot_contaminate_output(self):
        template = self.root / "template"
        (template / "hooks").mkdir(parents=True)
        (template / "hooks/post-checkout").write_text("private hook")
        with patch.dict(os.environ, {"GIT_DIR": str(self.repo),
                                    "GIT_OBJECT_DIRECTORY": str(self.repo / "objects"),
                                    "GIT_TEMPLATE_DIR": str(template),
                                    "GIT_CONFIG_COUNT": "1",
                                    "GIT_CONFIG_KEY_0": "core.bare", "GIT_CONFIG_VALUE_0": "true"}):
            self.run_materialize()
        self.assert_isolated(self.out)

    def test_audit_rejects_extra_files_modes_links_and_deleted_files(self):
        report = self.run_materialize()
        file = self.out / "a.txt"
        file.chmod(0o755)
        with self.assertRaises(self.api.MaterializeError):
            self.api.audit(self.out, report["manifest"])
        file.chmod(0o644)
        (self.out / "extra").write_bytes(b"x")
        with self.assertRaises(self.api.MaterializeError):
            self.api.audit(self.out, report["manifest"])
        (self.out / "extra").unlink()
        file.unlink()
        file.symlink_to("/etc/passwd")
        with self.assertRaises(self.api.MaterializeError):
            self.api.audit(self.out, report["manifest"])

    def test_duplicate_cli_paths_and_invalid_modes_are_rejected(self):
        for overrides in (
            [{"path": "a", "mode": "100644", "blob": self.blob(b"x")},
             {"path": "a", "delete": True}],
            {"a": {"mode": "160000", "blob": self.old}},
        ):
            with self.assertRaises(self.api.MaterializeError):
                self.run_materialize(overrides)

    def test_release_overlay_schema_and_sha_verification(self):
        release = self.root / "release"
        (release / "blobs").mkdir(parents=True)
        data = b"decontaminated focus preimage\n"
        digest = hashlib.sha256(data).hexdigest()
        content = release / "blobs" / digest
        content.write_bytes(data)
        entry = {"mode": "100644", "sha256": digest, "content_path": "blobs/" + digest}
        report = self.run_materialize({"a.txt": entry, "delete.txt": None},
                                      overlay_root=release)
        self.assertEqual((self.out / "a.txt").read_bytes(), data)
        self.assertEqual(next(r for r in report["manifest"] if r["path"] == "a.txt")["sha256"],
                         digest)
        self.assert_isolated(self.out)
        content.write_bytes(b"wrong")
        with self.assertRaises(self.api.MaterializeError):
            self.api.materialize(self.repo, self.base, {"a.txt": entry},
                                 self.root / "bad", overlay_root=release)

    def test_release_content_paths_cannot_escape_or_follow_symlinks(self):
        release = self.root / "release"
        release.mkdir()
        (release / "link").symlink_to(self.root, target_is_directory=True)
        (release / "file").symlink_to(self.root / "secret")
        (self.root / "secret").write_bytes(b"secret")
        digest = hashlib.sha256(b"secret").hexdigest()
        for path in ("../secret", "/etc/passwd", "link/secret", "file"):
            with self.subTest(path=path), self.assertRaises(self.api.MaterializeError):
                self.run_materialize({"a": {"mode": "100644", "sha256": digest,
                                           "content_path": path}}, overlay_root=release)
            self.assertFalse(self.out.exists())

    def test_raw_crlf_ident_and_encoding_attributes_start_clean(self):
        self.base = self.commit({
            ".gitattributes": ("100644", b"*.txt text eol=lf ident filter=private\n"
                                          b"wide.txt working-tree-encoding=UTF-16\n"),
            "raw.txt": ("100644", b"one\r\ntwo\r\n$Id: untouched $\r\n"),
            "wide.txt": ("100644", b"\xff\xfet\0e\0x\0t\0"),
        })
        self.run_materialize()
        self.assertEqual((self.out / "raw.txt").read_bytes(), b"one\r\ntwo\r\n$Id: untouched $\r\n")
        self.assertEqual((self.out / "wide.txt").read_bytes(), b"\xff\xfet\0e\0x\0t\0")
        self.assert_isolated(self.out)
        (self.out / "raw.txt").write_bytes(b"changed\r\n")
        self.assertIn(b"raw.txt", git(self.out, "diff", "--name-only"))

    def test_source_store_bytes_and_mtimes_unchanged_even_when_packed(self):
        git(self.repo, "repack", "-ad")
        def snapshot():
            return {str(p.relative_to(self.repo)):
                    (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
                    for p in self.repo.rglob("*") if p.is_file()}
        before = snapshot()
        self.run_materialize()
        self.assertEqual(snapshot(), before)

    def test_overlay_delete_then_replace_symlink_parent_without_following_it(self):
        tree = self.tree({"link": ("120000", b"/private"), "keep": ("100644", b"keep")})
        self.api.materialize(self.repo, None, {
            "link": None, "link/a": {"mode": "100644", "blob": self.blob(b"inside")},
        }, self.out, tree=tree)
        self.assertEqual((self.out / "link/a").read_bytes(), b"inside")
        self.assertFalse((self.out / "link").is_symlink())
        self.assert_isolated(self.out)

    def test_destination_symlink_and_atomic_race_are_refused(self):
        destination = self.root / "existing"
        destination.mkdir()
        self.out.symlink_to(destination, target_is_directory=True)
        with self.assertRaises(self.api.MaterializeError):
            self.run_materialize()
        self.assertTrue(self.out.is_symlink())
        self.assertEqual(list(destination.iterdir()), [])
        self.out.unlink()
        publish = self.api.publish
        def competing_creator(source, out):
            out.mkdir()
            (out / "sentinel").write_bytes(b"other creator")
            publish(source, out)
        with patch.object(self.api, "publish", side_effect=competing_creator):
            with self.assertRaises(self.api.MaterializeError):
                self.run_materialize()
        self.assertEqual((self.out / "sentinel").read_bytes(), b"other creator")
        self.assertFalse((self.out / ".git").exists())
        self.assertFalse(list(self.root.glob(".materialize-*")))

    def test_git_id_content_file_and_sha256_source_repository(self):
        other = self.root / "sha256.git"
        subprocess.run(["git", "init", "--bare", "--quiet", "--template=",
                        "--object-format=sha256", str(other)], check=True)
        blob = git(other, "hash-object", "-w", "--stdin", data=b"sha256 source\n").decode()
        tree = git(other, "mktree", data=f"100644 blob {blob}\tbase\n".encode()).decode()
        blobs = self.root / "blobs"
        blobs.mkdir()
        data = b"from loose content file"
        oid = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        (blobs / oid).write_bytes(data)
        self.api.materialize(other, None, {"overlay": {"mode": "100644", "blob": oid}},
                             self.out, tree=tree, blob_dir=blobs)
        self.assertEqual((self.out / "base").read_bytes(), b"sha256 source\n")
        self.assertEqual((self.out / "overlay").read_bytes(), data)
        self.assert_isolated(self.out)

    def test_overlay_root_cli_and_duplicate_json_key(self):
        release = self.root / "release"
        (release / "blobs").mkdir(parents=True)
        data = b"CLI content"
        digest = hashlib.sha256(data).hexdigest()
        (release / "blobs" / digest).write_bytes(data)
        private = release / "overrides.json"
        private.write_text(json.dumps({"a.txt": {"mode": "100644", "sha256": digest,
                                                "content_path": "blobs/" + digest}}))
        argv = [sys.executable, "-B", str(MODULE), "--repo", str(self.repo),
                "--commit", self.base, "--overrides", str(private), "--out", str(self.out),
                "--overlay-root", str(release)]
        result = subprocess.run(argv, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.out / "a.txt").read_bytes(), data)
        self.assertNotIn(b"blobs", result.stdout)
        private.write_text('{"a": null, "a": null}')
        result = subprocess.run(argv, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual((self.out / "a.txt").read_bytes(), data)

    def test_directory_export_ignore_and_unusual_filenames(self):
        tree = self.tree({
            ".gitattributes": ("100644", b"dir export-ignore\n"),
            "dir/space name\tline\n.txt": ("100644", b"exact"),
            "path/path": ("100644", b"another"),
            ".git/secret": ("100644", b"strip"),
        })
        self.api.materialize(self.repo, None, {}, self.out, tree=tree)
        self.assertEqual((self.out / "dir/space name\tline\n.txt").read_bytes(), b"exact")
        self.assertEqual((self.out / "path/path").read_bytes(), b"another")
        self.assert_isolated(self.out)

    def test_safe_data_unpack_preserves_trailing_slash_symlink_bytes(self):
        self.assertTrue(hasattr(self.api, "snapshot_data_filter_source"),
                        "Byte-preserving safe snapshot filter is not implemented")
        tree = self.tree({
            "tests/certs/expired/ca/cert.pem": ("100644", b"fixture certificate\n"),
            "tests/certs/mtls/client/ca": ("120000", b"../../expired/ca/"),
            "tests/certs/valid/ca": ("120000", b"../expired/ca"),
        })
        archive_path = self.root / "snapshot.tar"
        report = self.api.materialize(self.repo, None, {}, archive_path, tree=tree, format="tar")
        scope = {}
        exec(self.api.snapshot_data_filter_source(), scope)
        original_filter = tarfile.data_filter

        def modern_filter(member, destination):
            filtered = original_filter(member, destination)
            if filtered.issym():
                filtered = copy.copy(filtered)
                filtered.linkname = os.path.normpath(filtered.linkname)
            return filtered

        # Exercise modern CPython normalization even on older supported hosts.
        with patch.object(tarfile, "data_filter", side_effect=modern_filter):
            with tarfile.open(archive_path) as archive:
                archive.extractall(self.out, filter=scope["snapshot_data_filter"])
        self.assertEqual(os.readlink(self.out / "tests/certs/mtls/client/ca"), "../../expired/ca/")
        self.assertEqual((self.out / "tests/certs/mtls/client/ca/cert.pem").read_bytes(),
                         b"fixture certificate\n")
        self.api.audit(self.out, report["manifest"])
        self.assert_isolated(self.out)

    def test_snapshot_filter_keeps_data_security_checks_and_fails_closed(self):
        self.assertTrue(hasattr(self.api, "snapshot_data_filter"))
        destination = self.root / "extract"
        destination.mkdir()
        for target in ("/etc/passwd", "../../outside/"):
            with self.subTest(target=target), self.assertRaises(tarfile.FilterError):
                member = tarfile.TarInfo("link")
                member.type = tarfile.SYMTYPE
                member.linkname = target
                self.api.snapshot_data_filter(member, str(destination))
        with self.assertRaises(tarfile.FilterError):
            self.api.snapshot_data_filter(tarfile.TarInfo("../outside"), str(destination))
        member = tarfile.TarInfo("link")
        member.type = tarfile.SYMTYPE
        member.linkname = "dir/../target"
        normalized = copy.copy(member)
        normalized.linkname = "target"
        with patch.object(tarfile, "data_filter", return_value=normalized):
            with self.assertRaises(tarfile.FilterError):
                self.api.snapshot_data_filter(member, str(destination))


if __name__ == "__main__":
    unittest.main()
