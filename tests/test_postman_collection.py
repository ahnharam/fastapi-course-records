"""Ensure the submitted Postman collection stays reproducible and secret-free."""

from __future__ import annotations

import json
from pathlib import Path


COLLECTION_PATH = (
    Path(__file__).resolve().parents[1]
    / "postman"
    / "FastAPI_Courses.postman_collection.json"
)


def test_postman_collection_contains_required_requests_and_base_url() -> None:
    collection = json.loads(COLLECTION_PATH.read_text(encoding="utf-8"))

    variables = {item["key"]: item["value"] for item in collection["variable"]}
    requests = {item["name"]: item["request"] for item in collection["item"]}

    assert variables["base_url"] == "http://127.0.0.1:8000"
    assert requests["GET /courses"]["method"] == "GET"
    assert requests["GET /courses"]["url"]["raw"] == "{{base_url}}/courses"
    assert requests["POST /courses"]["method"] == "POST"
    assert requests["Invalid POST /courses (422)"]["method"] == "POST"

    valid_body = json.loads(requests["POST /courses"]["body"]["raw"])
    invalid_body = json.loads(requests["Invalid POST /courses (422)"]["body"]["raw"])
    assert set(valid_body) == {"course_name", "year", "semester", "grade"}
    assert invalid_body["year"] == 2026


def test_postman_collection_has_no_authentication_or_secret_fields() -> None:
    collection_text = COLLECTION_PATH.read_text(encoding="utf-8").lower()

    forbidden_terms = [
        '"auth"',
        "authorization",
        "bearer",
        "api_key",
        "access_token",
        "password",
    ]
    assert all(term not in collection_text for term in forbidden_terms)
