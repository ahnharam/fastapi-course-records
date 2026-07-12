"""HTTP-level assignment behavior tests using a temporary JSON file."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

import main
from main import STORE_ERROR_DETAIL, create_app


def test_get_courses_returns_complete_json_list(
    client: TestClient, initial_records: list[dict[str, str]]
) -> None:
    response = client.get("/courses")

    assert response.status_code == 200
    assert response.json() == initial_records


def test_post_course_returns_201_and_persists_to_real_file(
    client: TestClient,
    data_path: Path,
    initial_records: list[dict[str, str]],
) -> None:
    new_course = {
        "course_name": "인간로봇상호작용",
        "year": "2026",
        "semester": "2",
        "grade": "A+",
    }

    post_response = client.post("/courses", json=new_course)

    assert post_response.status_code == 201
    assert post_response.json() == new_course

    stored_payload = json.loads(data_path.read_text(encoding="utf-8"))
    assert stored_payload == [*initial_records, new_course]

    get_response = client.get("/courses")
    assert get_response.status_code == 200
    assert get_response.json()[-1] == new_course


def test_invalid_post_returns_422_and_server_still_accepts_get(
    client: TestClient, initial_records: list[dict[str, str]]
) -> None:
    invalid_course = {
        "course_name": "",
        "year": 2026,
        "semester": "",
        "grade": "A+",
    }

    invalid_response = client.post("/courses", json=invalid_course)

    assert invalid_response.status_code == 422
    assert invalid_response.json()["detail"]

    follow_up_response = client.get("/courses")
    assert follow_up_response.status_code == 200
    assert follow_up_response.json() == initial_records


def test_extra_fields_are_rejected_with_422(client: TestClient) -> None:
    response = client.post(
        "/courses",
        json={
            "course_name": "오픈소스소프트웨어실습",
            "year": "2026",
            "semester": "1",
            "grade": "A+",
            "student_name": "should-not-be-stored",
        },
    )

    assert response.status_code == 422


def test_corrupted_json_returns_500_then_recovers_after_file_is_fixed(
    data_path: Path,
) -> None:
    data_path.write_text("{not valid json", encoding="utf-8")

    with TestClient(create_app(data_path)) as test_client:
        failed_response = test_client.get("/courses")
        assert failed_response.status_code == 500
        assert failed_response.json() == {"detail": STORE_ERROR_DETAIL}

        data_path.write_text("[]\n", encoding="utf-8")
        recovered_response = test_client.get("/courses")
        assert recovered_response.status_code == 200
        assert recovered_response.json() == []


def test_file_io_error_returns_generic_500(tmp_path: Path) -> None:
    directory_instead_of_file = tmp_path / "courses.json"
    directory_instead_of_file.mkdir()

    with TestClient(create_app(directory_instead_of_file)) as test_client:
        response = test_client.get("/courses")

    assert response.status_code == 500
    assert response.json() == {"detail": STORE_ERROR_DETAIL}


def test_post_write_error_returns_500_preserves_file_and_server_survives(
    client: TestClient,
    data_path: Path,
    initial_records: list[dict[str, str]],
    monkeypatch: MonkeyPatch,
) -> None:
    original_bytes = data_path.read_bytes()

    def fail_replace(_source: str | Path, _destination: str | Path) -> None:
        raise OSError("simulated write failure")

    monkeypatch.setattr(main.os, "replace", fail_replace)
    response = client.post(
        "/courses",
        json={
            "course_name": "운영체제",
            "year": "2026",
            "semester": "1",
            "grade": "A0",
        },
    )

    assert response.status_code == 500
    assert response.json() == {"detail": STORE_ERROR_DETAIL}
    assert data_path.read_bytes() == original_bytes

    follow_up_response = client.get("/courses")
    assert follow_up_response.status_code == 200
    assert follow_up_response.json() == initial_records
