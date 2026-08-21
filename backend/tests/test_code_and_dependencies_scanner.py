import os
import stat
import shutil
import tempfile
from pathlib import Path

import pytest

from app.scanners.code_and_dependencies import CodeAndDependencyScanner
from app.models.asset import Asset, AssetType


def make_asset(target):
    return Asset(name="test", target=target, type=AssetType.SOURCE_CODE)


def run_scan_on_target(tmp_path, target_path):
    import asyncio

    scanner = CodeAndDependencyScanner()
    asset = make_asset(str(target_path))
    result = asyncio.run(scanner.execute(asset))
    return result


def test_directory_scanning_reads_files(tmp_path):
    d = tmp_path / "proj"
    d.mkdir()
    # create python file
    py = d / "app.py"
    py.write_text('''API_KEY = "AbCdEf1234567890XyZ987654"\nprint('hello')\n''')
    # create requirements
    req = d / "requirements.txt"
    req.write_text("Flask==2.2.4\n")

    res = run_scan_on_target(tmp_path, d)
    # should return findings from files, not from directory name
    assert res.success
    assert any(f.category.name == "SECRETS" or f.category.name == "DEPENDENCY" for f in res.findings)


def test_secret_detection_and_masking(tmp_path):
    d = tmp_path / "secretproj"
    d.mkdir()
    py = d / "settings.py"
    secret = 'API_KEY = "AbCdEf1234567890XyZ987654"\n'
    py.write_text(secret)

    res = run_scan_on_target(tmp_path, d)
    secrets = [f for f in res.findings if f.category.name == "SECRETS"]
    assert len(secrets) >= 1
    # evidence should not contain full secret value
    for s in secrets:
        ev = s.evidence
        if isinstance(ev, dict):
            joined = " ".join(str(v) for v in ev.values())
            assert "AbCdEf1234567890XyZ987654" not in joined


def test_dependency_vulnerability_detected(tmp_path):
    d = tmp_path / "depvuln"
    d.mkdir()
    (d / "requirements.txt").write_text("Flask==2.2.4\n")

    res = run_scan_on_target(tmp_path, d)
    deps = [f for f in res.findings if f.category.name == "DEPENDENCY"]
    assert any("CVE-2023-30861" in (f.cve or "") or "Flask" in (f.evidence.get("package") if isinstance(f.evidence, dict) else "") for f in deps)


def test_fixed_dependency_not_reported(tmp_path):
    d = tmp_path / "depfixed"
    d.mkdir()
    (d / "requirements.txt").write_text("Flask==3.1.1\n")

    res = run_scan_on_target(tmp_path, d)
    deps = [f for f in res.findings if f.category.name == "DEPENDENCY"]
    assert not any("CVE-2023-30861" in (f.cve or "") for f in deps)


def test_ignored_directories_not_scanned(tmp_path):
    d = tmp_path / "proj2"
    d.mkdir()
    # create ignored dirs
    git = d / ".git"
    git.mkdir()
    (git / "secret.txt").write_text("API_KEY=SHOULD_NOT_BE_FOUND\n")

    venv = d / ".venv"
    venv.mkdir()
    (venv / "secret2.txt").write_text("API_KEY=SHOULD_NOT_BE_FOUND\n")

    cache = d / "__pycache__"
    cache.mkdir()
    (cache / "secret3.txt").write_text("API_KEY=SHOULD_NOT_BE_FOUND\n")

    # create a real file that should be scanned
    (d / "main.py").write_text('print("ok")\n')

    res = run_scan_on_target(tmp_path, d)
    joined_evidence = " ".join(str(f.evidence) for f in res.findings if isinstance(f.evidence, dict))
    assert "SHOULD_NOT_BE_FOUND" not in joined_evidence


def test_unreadable_file_does_not_break_scan(tmp_path):
    d = tmp_path / "proj3"
    d.mkdir()
    good = d / "good.py"
    good.write_text('print("good")\n')
    bad = d / "bad.py"
    bad.write_text('print("bad")\n')
    # make unreadable
    os.chmod(bad, stat.S_IWUSR)

    try:
        res = run_scan_on_target(tmp_path, d)
        assert res.success
    finally:
        # restore so temp cleanup can remove
        os.chmod(bad, stat.S_IWUSR | stat.S_IRUSR)


def test_single_file_asset_scanned(tmp_path):
    f = tmp_path / "single.py"
    f.write_text('API_KEY = "AbCdEf1234567890XyZ987654"\n')
    res = run_scan_on_target(tmp_path, f)
    secrets = [f for f in res.findings if f.category.name == "SECRETS"]
    assert len(secrets) >= 1


def test_fallback_nonexistent_target_scanned_as_content(tmp_path):
    # pass a string that is not a path
    import asyncio
    scanner = CodeAndDependencyScanner()
    asset = make_asset("print(1)\nSECRET = 'X'\n")
    res = asyncio.run(scanner.execute(asset))
    assert res.success
