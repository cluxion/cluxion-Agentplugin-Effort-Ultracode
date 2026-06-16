"""Tests for the cluxion-ultracode CLI."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from cluxion_effort_ultracode.cli import main


def test_consensus_mock_unanimous_adapter():
    exit_code = main(
        [
            "consensus",
            "--question",
            "Adopt?",
            "--adapter",
            "mock-unanimous",
            "--agents",
            "2",
            "--rounds",
            "1",
        ]
    )
    assert exit_code == 0


def test_consensus_hermes_adapter_uses_default_llm_factory():
    class _StubLlm:
        def __init__(self) -> None:
            self.outputs = [
                {"stance": "Yes", "rationale": "r1", "evidence": ["e1"], "confidence": 0.9},
                {"stance": "No", "rationale": "r2", "evidence": ["e2"], "confidence": 0.8},
                {
                    "stance": "Yes",
                    "rationale": "r1",
                    "evidence": ["e1"],
                    "confidence": 0.95,
                    "conceded": [{"point": "No", "reason": "Yes is stronger"}],
                    "maintained": [],
                },
                {
                    "stance": "Yes",
                    "rationale": "r2",
                    "evidence": ["e2"],
                    "confidence": 0.95,
                    "conceded": [{"point": "No", "reason": "Yes is stronger"}],
                    "maintained": [],
                },
            ]
            self.index = 0

        def complete(self, prompt: str, *, schema=None):
            output = self.outputs[self.index]
            self.index += 1
            return output

    with patch("cluxion_effort_ultracode.plugin._default_llm", return_value=_StubLlm()):
        exit_code = main(
            [
                "consensus",
                "--question",
                "Adopt?",
                "--adapter",
                "hermes",
                "--agents",
                "2",
                "--rounds",
                "1",
            ]
        )
    assert exit_code == 0


@pytest.mark.skipif(
    os.getenv("CLUXION_EFFORT_ULTRACODE_LIVE") != "1",
    reason="set CLUXION_EFFORT_ULTRACODE_LIVE=1 to run real hermes -z consensus via CLI",
)
def test_consensus_hermes_adapter_live_smoke():
    exit_code = main(
        [
            "consensus",
            "--question",
            "Use stance YES. Is YES correct?",
            "--adapter",
            "hermes",
            "--agents",
            "2",
            "--rounds",
            "0",
            "--context",
            "Keep evidence short.",
        ]
    )
    assert exit_code == 0
