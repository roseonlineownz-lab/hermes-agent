"""A module entrypoint must retain profile selection on canonical re-import."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("selected", ["default", "novamaster-desktop"])
def test_module_entrypoint_preserves_explicit_profile(tmp_path, selected):
    root = Path(__file__).resolve().parents[2]
    home = tmp_path / "home"
    named = home / "profiles" / "novamaster-desktop"
    named.mkdir(parents=True)
    (named / "config.yaml").write_text("{}\n", encoding="utf-8")
    (home / "active_profile").write_text("novamaster-desktop\n", encoding="utf-8")
    env = dict(os.environ, HERMES_HOME=str(home), HERMES_RUNTIME_DIR=str(tmp_path / "runtime"))
    code = r'''
import importlib, json, os, runpy, sys
from pathlib import Path
root, selected = sys.argv[1:]
sys.path.insert(0, root)
from hermes_cli import _early_recovery
_early_recovery.restore_interrupted_pull = lambda *a, **kw: False
class Done(BaseException):
    pass
def trace(frame, event, arg):
    if event == "call" and frame.f_code.co_name == "main" and Path(frame.f_code.co_filename) == Path(root) / "hermes_cli" / "main.py":
        sys.settrace(None)
        before = os.environ["HERMES_HOME"]
        module = importlib.import_module("hermes_cli.main")
        print(json.dumps({"before": before, "after": os.environ["HERMES_HOME"], "same": module.__dict__ is frame.f_globals, "explicit": module.explicit_cli_profile()}))
        raise Done()
    return trace
sys.argv = ["hermes", "--profile", selected, "gateway", "--help"]
sys.settrace(trace)
try:
    runpy.run_module("hermes_cli.main", run_name="__main__", alter_sys=True)
except Done:
    pass
finally:
    sys.settrace(None)
'''
    child = subprocess.run([sys.executable, "-I", "-c", code, str(root), selected],
                           env=env, capture_output=True, text=True, timeout=45)
    assert child.returncode == 0, child.stderr
    result = json.loads(child.stdout.strip().splitlines()[-1])
    expected = home if selected == "default" else named
    assert Path(result["before"]) == expected
    assert Path(result["after"]) == expected
    assert result["same"] is True
    assert result["explicit"] == selected
    assert (home / "active_profile").read_text() == "novamaster-desktop\n"
