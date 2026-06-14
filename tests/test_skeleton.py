"""CLI smoke tests."""

from __future__ import annotations

from cluxion_effort_ultracode import cli


def test_version(capsys):
    assert cli.main(["--version"]) == 0
    assert "cluxion-ultracode 0.1.0" in capsys.readouterr().out
