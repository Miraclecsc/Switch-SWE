"""Small, real Git/pytest fixtures for the native Harbor final verifier."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tools.export_verifier import export_verifier, grade, junit, django_outcomes


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True)


class VerifierTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.base = self.root / "base"
        self.base.mkdir()
        git(self.base, "init", "-q")
        git(self.base, "config", "user.email", "fixture@example.invalid")
        git(self.base, "config", "user.name", "Fixture")
        (self.base / "value.py").write_text("answer = 0\nstable = 1\n")
        git(self.base, "add", ".")
        git(self.base, "commit", "-qm", "base")
        self.commit = git(self.base, "rev-parse", "HEAD").strip()
        (self.base / "value.py").write_text("answer = 42\nstable = 1\n")
        self.reference = git(self.base, "diff")
        git(self.base, "checkout", "--", "value.py")
        (self.base / "test_value.py").write_text(
            "from value import answer, stable\n"
            "def test_fix():\n    assert answer == 42\n"
            "def test_stable():\n    assert stable == 1\n"
        )
        git(self.base, "add", "test_value.py")
        hidden = git(self.base, "diff", "--cached")
        git(self.base, "reset", "--hard", "-q", "HEAD")
        self.focus = self.root / "focus"
        shutil.copytree(self.base, self.focus)
        self.release = self.root / "release"
        self.pair = self.root / "pair"
        (self.pair / "private").mkdir(parents=True)
        (self.pair / "config").mkdir()
        self.payload = {
            "repo": "fixture/repo", "base_commit": self.commit,
            "code_patch": self.reference, "test_patch": hidden,
            "derived_fail_to_pass": ["test_value::test_fix"],
            "derived_pass_to_pass": ["test_value::test_stable"], "n_pass_to_pass": 1,
        }
        self.case = {
            "case_id": "sf001_switched", "pair_id": "sf001", "condition": "switched",
            "task_id": "focus_task", "focus_workspace": "w00",
            "workspaces": [{"workspace": "w00", "repo": "fixture/repo",
                            "commit": self.commit}],
        }
        self.recipe = {"runner": "pytest", "python": sys.executable, "env": {}}
        self.release.mkdir()
        self.task = self.root / "task"
        self.write_source()

    def write_source(self):
        values = {
            "private/scoring.json": {"focus_task": self.payload, "irrelevant": {}},
            "config/recipes.json": {"cases": {"sf001": self.recipe}},
        }
        bindings = {}
        for name, value in values.items():
            data = json.dumps(value).encode()
            (self.pair / name).write_bytes(data)
            bindings[name] = hashlib.sha256(data).hexdigest()
        (self.release / "cohort.json").write_text(json.dumps({"pairs": [{
            "pair_id": "sf001", "source_release": str(self.pair),
            "case_ids": ["sf001_switched"], "bindings": bindings,
        }]}))

    def run_grade(self):
        export_verifier(self.case, self.release, self.task)
        return grade(self.task / "steps/final/tests", self.base, self.focus,
                     self.root / "out")

    def test_empty_patch_runs_f2p_and_scores_zero(self):
        result = self.run_grade()
        self.assertEqual(result["status"], "graded", result)
        self.assertFalse(result["passed"])
        self.assertEqual(result["f2p_not_passing"], ["test_value::test_fix"])
        self.assertEqual(result["p2p_not_passing"], [])
        self.assertEqual((self.root / "out/reward.txt").read_text(), "0\n")

    def test_reference_committed_and_uncommitted_score_one(self):
        for committed in (False, True):
            with self.subTest(committed=committed):
                (self.focus / "value.py").write_text("answer = 42\nstable = 1\n")
                if committed:
                    git(self.focus, "add", ".")
                    git(self.focus, "commit", "-qm", "candidate")
                result = self.run_grade()
                self.assertTrue(result["passed"], result)
                self.assertEqual((self.root / "out/reward.txt").read_text(), "1\n")
                self.assertEqual((self.base / "value.py").read_text(),
                                 "answer = 0\nstable = 1\n")

    def test_nonempty_wrong_patch_and_p2p_regression_score_zero(self):
        for value in ("answer = 9\nstable = 1\n", "answer = 42\nstable = 0\n"):
            (self.focus / "value.py").write_text(value)
            result = self.run_grade()
            self.assertFalse(result["passed"], result)
            self.assertEqual(result["status"], "graded", result)

    def test_agent_git_metadata_and_test_edits_cannot_supply_a_pass(self):
        (self.focus / "test_value.py").write_text("def test_fix(): pass\n")
        (self.focus / "conftest.py").write_text("raise RuntimeError('untrusted')\n")
        shutil.rmtree(self.focus / ".git")
        result = self.run_grade()
        self.assertEqual(result["status"], "graded", result)
        self.assertFalse(result["passed"])
        self.assertNotIn("conftest", (self.root / "out/candidate.patch").read_text())

    def test_new_code_file_is_collected(self):
        (self.focus / "fix.py").write_text("answer = 42\n")
        (self.focus / "value.py").write_text("from fix import answer\nstable = 1\n")
        self.assertTrue(self.run_grade()["passed"])

    def test_missing_runtime_is_error_without_reward(self):
        self.recipe["python"] = "/no/such/python"
        self.write_source()
        (self.root / "out").mkdir()
        (self.root / "out/reward.txt").write_text("1\n")
        result = self.run_grade()
        self.assertEqual(result["status"], "error")
        self.assertFalse((self.root / "out/reward.txt").exists())

    def test_candidate_collection_failure_is_zero(self):
        (self.focus / "value.py").write_text("syntax error @@@\n")
        result = self.run_grade()
        self.assertEqual(result["status"], "graded", result)
        self.assertFalse(result["passed"])

    def test_export_selects_only_focus_and_verifies_binding(self):
        metadata = export_verifier(self.case, self.release, self.task)
        self.assertEqual(metadata["artifacts"][0]["source"], "/work/w00")
        self.assertEqual(metadata["artifacts"][0]["destination"], "focus")
        self.assertIn(".git", metadata["artifacts"][0]["exclude"])
        self.assertEqual(metadata["verifier"]["environment_mode"], "separate")
        self.assertEqual(metadata["base_path"], "/opt/focus-base")
        contract = json.loads((self.task / "steps/final/tests/contract.json").read_text())
        self.assertEqual(contract["task_id"], "focus_task")
        self.assertNotIn("code_patch", contract)
        self.assertEqual(metadata["reference_patch"], self.reference)
        (self.pair / "private/scoring.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "hash"):
            export_verifier(self.case, self.release, self.task)

    def test_export_rejects_baseline_and_invalid_targets(self):
        self.case["condition"] = "baseline"
        with self.assertRaises(ValueError):
            export_verifier(self.case, self.release, self.task)
        self.case["condition"] = "switched"
        self.payload["derived_fail_to_pass"] = []
        self.write_source()
        with self.assertRaises(ValueError):
            export_verifier(self.case, self.release, self.task)

    def test_frozen_python_is_explicitly_mapped_to_public_environment(self):
        self.recipe["python"] = "/opt/runtime/case-python/python/bin/python3.12"
        self.write_source()
        metadata = export_verifier(self.case, self.release, self.task)
        contract = json.loads((self.task / "steps/final/tests/contract.json").read_text())
        self.assertEqual(metadata["python"], "/opt/ssb/bin/python")
        self.assertEqual(contract["source_python"], self.recipe["python"])

    def test_native_candidate_build_failure_requires_a_working_base_build(self):
        export_verifier(self.case, self.release, self.task)
        tests = self.task / "steps/final/tests"
        builder = self.root / "build.py"
        builder.write_text(
            "from pathlib import Path\nimport sys\n"
            "text = (Path(sys.argv[1]) / 'value.py').read_text()\n"
            "sys.exit(1 if '42' in text else 0)\n"
        )
        contract = json.loads((tests / "contract.json").read_text())
        contract["native_rebuild"] = [sys.executable, str(builder)]
        (tests / "contract.json").write_text(json.dumps(contract))
        (self.focus / "value.py").write_text("answer = 42\nstable = 1\n")
        result = grade(tests, self.base, self.focus, self.root / "out")
        self.assertEqual(result["status"], "graded", result)
        self.assertFalse(result["passed"])
        builder.write_text("raise RuntimeError('broken toolchain')\n")
        result = grade(tests, self.base, self.focus, self.root / "out")
        self.assertEqual(result["status"], "error", result)
        self.assertFalse((self.root / "out/reward.txt").exists())

    def test_generated_grader_runs_as_standalone_file(self):
        export_verifier(self.case, self.release, self.task)
        script = self.task / "steps/final/tests/grader.py"
        run = subprocess.run([sys.executable, str(script), "--base", str(self.base),
                              "--focus", str(self.focus), "--out", str(self.root / "out")],
                             capture_output=True, text=True, cwd="/")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual((self.root / "out/reward.txt").read_text(), "0\n")
        namespace = {"__name__": "generated_grader"}
        exec(compile(script.read_text(), str(script), "exec"), namespace)
        self.assertTrue(callable(namespace["grade"]))
        self.assertNotIn("export_verifier", namespace)

    def test_file_deletion_is_collected_without_agent_git(self):
        (self.base / "obsolete.py").write_text("unused = True\n")
        git(self.base, "add", ".")
        git(self.base, "commit", "-qm", "with obsolete file")
        self.commit = git(self.base, "rev-parse", "HEAD").strip()
        self.payload["base_commit"] = self.commit
        self.case["workspaces"][0]["commit"] = self.commit
        self.write_source()
        (self.focus / "value.py").write_text("answer = 42\nstable = 1\n")
        shutil.rmtree(self.focus / ".git")
        result = self.run_grade()
        self.assertTrue(result["passed"], result)
        patch = (self.root / "out/candidate.patch").read_text()
        self.assertIn("deleted file mode", patch)
        self.assertIn("a/obsolete.py", patch)

    def test_xml_duplicate_skip_error_and_missing_are_not_passes(self):
        xml = self.root / "tests.xml"
        xml.write_text('<testsuite>'
                       '<testcase classname="m.C" name="test_x[a/b]"><failure/></testcase>'
                       '<testcase classname="m.C" name="test_x[a/b]"/>'
                       '<testcase classname="m" name="test_s"><skipped/></testcase>'
                       '<testcase classname="m" name="test_e"><error/></testcase>'
                       '</testsuite>')
        self.assertEqual(junit(xml), {"m.C::test_x[a/b]": "fail",
                                    "m::test_s": "skip", "m::test_e": "error"})

    def test_django_duplicate_failure_and_verbose_names(self):
        log = ("test_a (signals.tests.C.test_a) ... FAIL\n"
               "migration ...test_a (signals.tests.C.test_a) ... ok\n"
               "test_b (signals.tests.C.test_b) ... skipped 'reason'\n")
        self.assertEqual(django_outcomes(log),
                         {"signals.tests.C.test_a": "fail", "signals.tests.C.test_b": "skip"})


if __name__ == "__main__":
    unittest.main()
