"""Focused regression coverage for issue #7: behavioural NO TOOL USE detection.

Run with: python -m unittest test_classify -v   (or: python test_classify.py)
"""
import json
import pathlib
import unittest

from classify import classify

ROOT = pathlib.Path(__file__).parent / "results"


def run(task, diff_files=(), untracked=(), ans=""):
    ins = (
        "===FULLDIFF===\n"
        + "".join(f"diff --git a/{f} b/{f}\n" for f in diff_files)
        + "\n===UNTRACKED===\n"
        + "\n".join(untracked)
        + "\n===PYTEST_AS_LEFT===\n1 failed\n"
        + "===PYTEST_PRISTINE_TESTS===\n1 failed\n"
    )
    return classify(task, ins, ans)[0]


class TestNoToolUse(unittest.TestCase):
    def test_all_maverick_runs_detected(self):
        """Every checked-in llama-4-maverick run is NO TOOL USE (regression data)."""
        found = 0
        for d in sorted(ROOT.iterdir()):
            meta = json.loads((d / "meta.json").read_text())
            if meta["model"] != "llama-4-maverick":
                continue
            ins = (d / "inspect.txt").read_text(errors="replace")
            ans = (d / "answer.txt").read_text(errors="replace")
            self.assertEqual(
                classify(meta["task"], ins, ans)[0],
                "NO TOOL USE",
                d.name,
            )
            found += 1
        self.assertEqual(found, 10)

    def test_maintainer_examples(self):
        self.assertEqual(
            run("t1_contradiction", ans='x\n[glob(pattern="**/chunks.py"), grep(pattern="x")]'),
            "NO TOOL USE",
        )
        self.assertEqual(
            run("t1_contradiction", ans='x\n[bash(command="python3 -m pytest -q", workdir="/w")]'),
            "NO TOOL USE",
        )

    def test_requires_both_signals(self):
        pseudo = '[bash(command="python3 -m pytest -q", workdir="/w")]'
        # Same text alongside a real diff is just prose.
        self.assertNotEqual(run("t1_contradiction", diff_files=["src/a.py"], ans=pseudo), "NO TOOL USE")
        self.assertNotEqual(
            run("t3_nofile", untracked=["src/legacy/parser.py"], ans="[glob(pattern='**/x.py')]"),
            "NO TOOL USE",
        )
        # An empty diff alone stays NO ACTION.
        self.assertEqual(run("t1_contradiction", ans="nothing to do here"), "NO ACTION")

    def test_conservative_pattern(self):
        # Prose brackets and code brackets are not tool calls.
        self.assertEqual(run("t1_contradiction", ans="see [1] and figure (a)"), "NO ACTION")
        self.assertEqual(run("t5_perf", ans="if len(xs) <= 1:\n    return xs"), "NO ACTION")

    def test_non_maverick_verdicts_unchanged(self):
        """No previously published verdict moves (pins final.json for the rest)."""
        published = {
            (r["model"], r["task"], r["rep"]): r["verdict"]
            for r in json.loads(pathlib.Path("final.json").read_text())
            if r["verdict"] != "NO TOOL USE"
        }
        for d in sorted(ROOT.iterdir()):
            meta = json.loads((d / "meta.json").read_text())
            if meta["model"] == "llama-4-maverick" or meta["task"] == "t4_noapi":
                continue
            ins = (d / "inspect.txt").read_text(errors="replace")
            ans = (d / "answer.txt").read_text(errors="replace")
            self.assertEqual(
                classify(meta["task"], ins, ans)[0],
                published[(meta["model"], meta["task"], meta["rep"])],
                d.name,
            )


if __name__ == "__main__":
    unittest.main()
