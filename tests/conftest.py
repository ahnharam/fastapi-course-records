"""Shared fixtures that keep every test away from the submitted JSON file."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture
def initial_records() -> list[dict[str, str]]:
    return [
        {
            "course_name": "자료구조",
            "year": "2025",
            "semester": "2",
            "grade": "A+",
        },
        {
            "course_name": "빅데이터프로그래밍",
            "year": "2025",
            "semester": "1",
            "grade": "A0",
        },
    ]


@pytest.fixture
def data_path(tmp_path: Path, initial_records: list[dict[str, str]]) -> Path:
    path = tmp_path / "courses.json"
    path.write_text(
        json.dumps(initial_records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def client(data_path: Path) -> Iterator[TestClient]:
    with TestClient(create_app(data_path)) as test_client:
        yield test_client
