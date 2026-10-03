"""Tests for index.py: the browsable HTML index of all 102 runs.

Run with: python -m unittest test_index -v   (or: python test_index.py)
"""
import pathlib
import re
import tempfile
import unittest

import index

ROOT = pathlib.Path(__file__).parent


class TestBand(unittest.TestCase):
    """band() must group verdicts exactly like chart.py, the published figure."""

    def test_bands_match_chart(self):
        right = {"CORRECT (approx)", "WROTE MISSING FILE"}
        red = {"NO ACTION", "FAILED ATTEMPT"}
        invis = {"PATCHED THE HARNESS", "DEFEATED THE METRIC", "HID STATE IN SOURCE",
                 "FABRICATED DEP", "CORRUPTED SOURCE", "BROKE THE CONTRACT"}
        visible = {"SOLVED", "WEAKENED TEST", "EDITED BOTH", "TAUTOLOGY",
                   "CONFIG CHEAT", "NO TOOL USE"}
        for v in right:
            self.assertEqual(index.band(v), "right", v)
        for v in red:
            self.assertEqual(index.band(v), "red", v)
        for v in invis:
            self.assertEqual(index.band(v), "invisible", v)
        for v in visible:
            self.assertEqual(index.band(v), "visible", v)

    def test_unknown_verdict_is_visible(self):
        # anything unclassified still renders, in the catch-all band
        self.assertEqual(index.band("SOMETHING NEW"), "visible")


class TestLoaders(unittest.TestCase):
    """load_rows/load_runs against the checked-in dataset."""

    @classmethod
    def setUpClass(cls):
        cls.rows = index.load_rows()
        cls.runs = index.load_runs()

    def test_final_json_rows(self):
        self.assertEqual(len(self.rows), 99)  # 102 runs minus t4_noapi's 3
        for (task, model, rep), r in self.rows.items():
            self.assertEqual((r["task"], r["model"], r["rep"]), (task, model, rep))
            self.assertTrue(r["verdict"])

    def test_all_markdown_loaded(self):
        self.assertEqual(len(self.runs), 102)
        self.assertIn("t4_noapi__glm-5.3-flash__1", self.runs)

    def test_h1_stripped_body_kept(self):
        # the H1 repeats the filename; the four sections must survive
        body = self.runs["c1_offbyone__deepseek-v4-pro__1"]
        self.assertNotIn("# c1_offbyone", body)
        for section in ("## diff", "## new files",
                        "## pytest as the agent left it",
                        "## pytest with the ORIGINAL tests restored"):
            self.assertIn(section, body)

    def test_every_final_json_row_has_a_run_file(self):
        for (task, model, rep) in self.rows:
            self.assertIn(index.run_name(task, model, rep), self.runs)


class TestGrid(unittest.TestCase):
    """The grid must reproduce the lower panel of images/results.png."""

    @classmethod
    def setUpClass(cls):
        cls.html = index.grid(index.load_rows())

    def test_shape(self):
        # 1 header + 7 task rows, 1 corner + 4 model columns
        self.assertEqual(self.html.count("<tr>"), 8)
        for m in index.MODELS:
            self.assertIn(m, self.html)
        for t in index.TASKS:
            self.assertIn(t, self.html)

    def test_84_squares(self):
        self.assertEqual(self.html.count('class="rep" id'), 84)

    def test_band_counts_match_published_figures(self):
        # README: 51/84 faked a pass, 26 invisible, 13 left red, 20 right
        rows = index.load_rows()
        grid_rows = [r for r in rows.values()
                     if r["task"] not in index.CONTROLS
                     and r["task"] not in index.EXCLUDE_TASKS
                     and r["model"] != "llama-4-maverick"]
        self.assertEqual(len(grid_rows), 84)
        counts = {}
        for r in grid_rows:
            counts[index.band(r["verdict"])] = counts.get(index.band(r["verdict"]), 0) + 1
        self.assertEqual(counts, {"right": 20, "red": 13,
                                   "visible": 25, "invisible": 26})

    def test_excluded_tasks_absent(self):
        # t4_noapi and the controls are not part of the figure's grid
        self.assertNotIn("t4_noapi", self.html)
        self.assertNotIn("c1_offbyone", self.html)
        self.assertNotIn("c2_missing", self.html)

    def test_every_square_links_to_a_run(self):
        for name in re.findall(r'id="g-([^"]+)"', self.html):
            self.assertIn(f'href="#run-{name}"', self.html)


class TestIndex(unittest.TestCase):
    """The generated page: self-contained, complete, escaped, filterable."""

    @classmethod
    def setUpClass(cls):
        cls.rows = index.load_rows()
        cls.runs = index.load_runs()
        cls.html = index.index(cls.rows, cls.runs)

    def test_self_contained(self):
        # no build step, no runtime dependencies: nothing may be fetched.
        # (URLs inside escaped run bodies are data, not page references.)
        markup = re.sub(r'<pre class="runbody">.*?</pre>', "", self.html, flags=re.S)
        self.assertNotIn("<link", markup)
        self.assertNotIn("src=", markup)
        self.assertNotIn("@import", markup)
        self.assertNotIn("http://", markup)
        self.assertNotIn("https://", markup)

    def test_responsive_rules_present(self):
        # narrow screens: labels stack above squares, no nowrap clipping
        self.assertIn("@media", self.html)
        self.assertIn("max-width: 640px", self.html)
        self.assertNotIn("white-space: nowrap", self.html)
        # the grid scrolls horizontally rather than overflowing the page
        self.assertIn("grid-scroll", self.html)
        self.assertIn("overflow-x: auto", self.html)

    def test_all_102_runs_have_sections(self):
        self.assertEqual(self.html.count('details class="run"'), 102)
        for name in self.runs:
            self.assertIn(f'id="run-{name}"', self.html)

    def test_runs_without_final_json_row_get_unknown(self):
        # t4_noapi is excluded from final.json but its three runs are checked in
        self.assertEqual(self.html.count('data-verdict="UNKNOWN"'), 3)

    def test_every_section_carries_band_and_verdict(self):
        sections = re.findall(r'<details class="run"[^>]*>', self.html)
        self.assertEqual(len(sections), 102)
        for s in sections:
            self.assertRegex(s, r'data-verdict="[^"]+"')
            self.assertRegex(s, r'data-band="(right|red|visible|invisible)"')

    def test_filter_controls_present(self):
        for b, _ in index.LEGEND:
            self.assertIn(f'data-band="{b}"', self.html)
        # every verdict in the dataset is an option, plus "all"
        verdicts = {r["verdict"] for r in self.rows.values()}
        for v in verdicts:
            self.assertIn(f'value="{v}"', self.html)
        self.assertIn('<option value="">all</option>', self.html)

    def test_verdict_counts_in_options(self):
        # the option label shows the count, e.g. WEAKENED TEST (12)
        self.assertIn("WEAKENED TEST (12)", self.html)
        self.assertIn("PATCHED THE HARNESS (1)", self.html)

    def test_run_bodies_escaped(self):
        # diffs contain < > & ; none of it may leak into the markup
        raw = re.search(r'<pre class="runbody">.*?</pre>',
                        self.html, re.S).group(0)
        self.assertNotIn("<div", raw)
        self.assertNotIn("<script", raw)
        # a real diff line survives verbatim once unescaped
        self.assertIn("diff --git a/src/chunk.py b/src/chunk.py", self.html)


class TestSyntheticData(unittest.TestCase):
    """Edge cases against small fixtures, not the real dataset."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = pathlib.Path(self.tmp.name)

    def write_runs(self, files):
        runs_dir = self.dir / "runs"
        runs_dir.mkdir()
        for name, text in files.items():
            (runs_dir / f"{name}.md").write_text(text, encoding="utf-8")
        return runs_dir

    def test_missing_row_becomes_unknown(self):
        runs = self.write_runs({
            "t9_x__model-a__1": "# t9_x__model-a__1\n\n## diff\n```diff\nno changes\n```\n",
        })
        rows = {}  # final.json has nothing for this run
        page = index.index(rows, index.load_runs(runs))
        self.assertIn('data-verdict="UNKNOWN"', page)
        self.assertIn('id="run-t9_x__model-a__1"', page)

    def test_html_in_run_body_is_escaped(self):
        runs = self.write_runs({
            "t9_x__model-a__1":
                "# t9_x__model-a__1\n\n## diff\n```diff\n"
                "+assert x <script>alert(1)</script> & \"y\"\n```\n",
        })
        page = index.index({}, index.load_runs(runs))
        self.assertNotIn("<script>alert", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)
        self.assertIn("&amp; &quot;y&quot;", page)

    def test_file_without_h1_keeps_full_text(self):
        runs = self.write_runs({"t9_x__model-a__1": "just a body, no heading"})
        loaded = index.load_runs(runs)
        self.assertEqual(loaded["t9_x__model-a__1"], "just a body, no heading")

    def test_partial_cell_renders_gap(self):
        # a model that only ran rep 1: two grey gaps, one square
        rows = {("t9_x", "model-a", 1): {"task": "t9_x", "model": "model-a",
                                          "rep": 1, "verdict": "SOLVED"}}
        cell = index.grid_cell("t9_x", "model-a", rows)
        self.assertEqual(cell.count('class="rep gap"'), 2)
        self.assertEqual(cell.count('class="rep" id'), 1)

    def test_unrun_cell_is_a_gap(self):
        self.assertEqual(index.grid_cell("t9_x", "model-a", {}), '<td class="gap"></td>')

    def test_grid_uses_only_figure_tasks(self):
        # a control row in final.json must not add a grid row
        rows = {("c1_offbyone", "model-a", 1): {"task": "c1_offbyone",
                                                "model": "model-a", "rep": 1,
                                                "verdict": "SOLVED"}}
        self.assertNotIn("c1_offbyone", index.grid(rows))


if __name__ == "__main__":
    unittest.main()
