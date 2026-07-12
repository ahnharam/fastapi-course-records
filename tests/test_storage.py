"""Persistence, atomicity, and concurrent-write tests for the JSON repository."""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

import main
from main import Course, CourseRepository, CourseStoreError


def test_concurrent_repository_instances_do_not_lose_writes(
    data_path: Path, initial_records: list[dict[str, str]]
) -> None:
    write_count = 24
    start = threading.Event()

    def append_course(index: int) -> None:
        repository = CourseRepository(data_path, lock_timeout=15)
        start.wait(timeout=5)
        repository.add_course(
            Course(
                course_name=f"동시성테스트-{index:02d}",
                year="2026",
                semester="2",
                grade="A+",
            )
        )

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(append_course, index) for index in range(write_count)]
        start.set()
        for future in futures:
            future.result(timeout=20)

    raw_payload = json.loads(data_path.read_text(encoding="utf-8"))
    names = {item["course_name"] for item in raw_payload}

    assert len(raw_payload) == len(initial_records) + write_count
    assert {f"동시성테스트-{index:02d}" for index in range(write_count)} <= names
    assert not list(data_path.parent.glob(".courses.json.*.tmp"))


def test_atomic_replace_failure_preserves_original_and_removes_temp_file(
    data_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = CourseRepository(data_path)
    original_bytes = data_path.read_bytes()

    def fail_replace(_source: str | Path, _destination: str | Path) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(main.os, "replace", fail_replace)

    with pytest.raises(CourseStoreError, match="저장할 수 없습니다"):
        repository.add_course(
            Course(
                course_name="운영체제",
                year="2026",
                semester="1",
                grade="A0",
            )
        )

    assert data_path.read_bytes() == original_bytes
    assert not list(data_path.parent.glob(".courses.json.*.tmp"))


def test_directory_fsync_failure_after_replace_keeps_committed_write(
    data_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    repository = CourseRepository(data_path)
    new_course = Course(
        course_name="분산시스템",
        year="2026",
        semester="여름학기",
        grade="P",
    )

    def fail_directory_fsync() -> None:
        raise OSError("simulated directory fsync failure")

    monkeypatch.setattr(repository, "_fsync_parent_directory", fail_directory_fsync)

    assert repository.add_course(new_course) == new_course
    persisted = json.loads(data_path.read_text(encoding="utf-8"))
    assert persisted[-1] == new_course.model_dump(mode="json")
    assert "디렉터리 fsync에 실패" in caplog.text


def test_repository_rejects_non_list_json(data_path: Path) -> None:
    data_path.write_text('{"course_name": "not-a-list"}\n', encoding="utf-8")

    with pytest.raises(CourseStoreError, match="최상위 값은 list"):
        CourseRepository(data_path).list_courses()
