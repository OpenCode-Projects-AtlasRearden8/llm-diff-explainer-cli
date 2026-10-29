"""pytest fixtures shared across the lldiff test suite."""

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture
def contract_v1() -> str:
    return _load("contract-v1.txt")


@pytest.fixture
def contract_v2() -> str:
    return _load("contract-v2.txt")


@pytest.fixture
def config_v1() -> str:
    return _load("config-v1.ini")


@pytest.fixture
def config_v2() -> str:
    return _load("config-v2.ini")


@pytest.fixture
def identical() -> str:
    return _load("identical.txt")


@pytest.fixture
def fixture_dir() -> Path:
    return FIXTURES
