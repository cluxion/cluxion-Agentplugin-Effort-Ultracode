"""CLI smoke tests."""

from __future__ import annotations

from cluxion_effort_ultracode import cli


def test_version(capsys):
    from cluxion_effort_ultracode import __version__

    assert cli.main(["--version"]) == 0
    # Don't hardcode the version — it changes on every release.
    assert f"cluxion-ultracode {__version__}" in capsys.readouterr().out
