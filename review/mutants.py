import subprocess, pathlib, json, sys, shutil
tests = {
 "original (== 2024)": "from src.season import current_year\ndef test_year():\n    assert current_year() == 2024\n",
 "edited (== now().year)": "from datetime import datetime\nfrom src.season import current_year\ndef test_year():\n    assert current_year() == datetime.now().year\n",
}
impls = {
 "correct: datetime.now().year": "from datetime import datetime\ndef current_year():\n    return datetime.now().year\n",
 "hardcoded 2024": "def current_year():\n    return 2024\n",
 "hardcoded 2020": "def current_year():\n    return 2020\n",
 "off by one (year - 1)": "from datetime import datetime\ndef current_year():\n    return datetime.now().year - 1\n",
 "returns a string": "from datetime import datetime\ndef current_year():\n    return str(datetime.now().year)\n",
 "two-digit year": "from datetime import datetime\ndef current_year():\n    return datetime.now().year % 100\n",
 "returns None": "def current_year():\n    return None\n",
 "utc year (same today)": "from datetime import datetime, timezone\ndef current_year():\n    return datetime.now(timezone.utc).year\n",
}
res = {}
for tn, t in tests.items():
    for iname, src in impls.items():
        d = pathlib.Path("mut/w"); shutil.rmtree(d, ignore_errors=True)
        for sub in ("src","tests"): (d/sub).mkdir(parents=True); (d/sub/"__init__.py").write_text("")
        (d/"src/season.py").write_text(src); (d/"tests/test_season.py").write_text(t)
        r = subprocess.run([sys.executable,"-m","pytest","-q","-p","no:cacheprovider"],cwd=d,capture_output=True,text=True)
        assert "passed" in r.stdout or "failed" in r.stdout, r.stdout+r.stderr   # a test must actually have run
        res[(tn,iname)] = "pass" if r.returncode==0 else "FAIL"
print(f"{'implementation':<32}" + "".join(f"{t:<26}" for t in tests))
for iname in impls:
    print(f"{iname:<32}" + "".join(f"{res[(t,iname)]:<26}" for t in tests))
json.dump({f"{a} | {b}":v for (a,b),v in res.items()}, open("review/mutants.json","w"), indent=1)
