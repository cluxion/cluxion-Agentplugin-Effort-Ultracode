"""Skeleton contract."""

from __future__ import annotations

from cluxion_effort_ultracode import cli


def test_version(capsys):
    assert cli.main(["--version"]) == 0
    assert "cluxion-ultracode" in capsys.readouterr().out
