"""FastAPI course-record service backed by an atomic JSON file store."""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from contextlib import contextmanager
from json import JSONDecodeError
from pathlib import Path
from typing import Annotated, Iterator

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from filelock import FileLock, Timeout as FileLockTimeout
from pydantic import BaseModel, ConfigDict, Field, StrictStr, ValidationError


LOGGER = logging.getLogger("course_records")
DEFAULT_DATA_PATH = Path(__file__).with_name("courses.json")
STORE_ERROR_DETAIL = "수강기록 파일을 처리할 수 없습니다. 서버 로그를 확인하세요."

NonEmptyText = Annotated[StrictStr, Field(min_length=1, max_length=100)]
YearText = Annotated[StrictStr, Field(min_length=1, max_length=10)]
SemesterText = Annotated[StrictStr, Field(min_length=1, max_length=20)]
GradeText = Annotated[StrictStr, Field(min_length=1, max_length=10)]


class Course(BaseModel):
    """One completed-course record stored in ``courses.json``."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    course_name: NonEmptyText
    year: YearText
    semester: SemesterText
    grade: GradeText


class CourseStoreError(RuntimeError):
    """Raised when the JSON store cannot be read, validated, locked, or saved."""


class CourseRepository:
    """Serialize JSON read-modify-write operations and replace files atomically.

    ``threading.RLock`` protects concurrent requests sharing one repository object,
    while ``FileLock`` coordinates other repository instances or worker processes
    that point at the same JSON file. Writes are flushed and fsynced to a temporary
    file in the same directory before ``os.replace`` swaps it into place.
    """

    def __init__(self, data_path: str | Path, *, lock_timeout: float = 10.0) -> None:
        self.data_path = Path(data_path).expanduser().resolve()
        self.lock_path = self.data_path.with_name(f"{self.data_path.name}.lock")
        self._thread_lock = threading.RLock()
        self._file_lock = FileLock(str(self.lock_path), timeout=lock_timeout)

    @contextmanager
    def _locked(self) -> Iterator[None]:
        try:
            with self._thread_lock:
                with self._file_lock:
                    yield
        except FileLockTimeout as exc:
            raise CourseStoreError("수강기록 파일 잠금 대기 시간이 초과되었습니다.") from exc
        except OSError as exc:
            raise CourseStoreError("수강기록 파일 잠금을 사용할 수 없습니다.") from exc

    def list_courses(self) -> list[Course]:
        """Return a validated snapshot of every stored course."""

        with self._locked():
            return self._read_unlocked()

    def add_course(self, course: Course) -> Course:
        """Append one course and persist the complete list before returning."""

        with self._locked():
            courses = self._read_unlocked()
            courses.append(course)
            self._atomic_write_unlocked(courses)
        return course

    def _read_unlocked(self) -> list[Course]:
        try:
            payload = json.loads(self.data_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise CourseStoreError("수강기록 JSON 파일을 읽을 수 없습니다.") from exc
        except JSONDecodeError as exc:
            raise CourseStoreError("수강기록 파일이 올바른 JSON이 아닙니다.") from exc

        if not isinstance(payload, list):
            raise CourseStoreError("수강기록 JSON의 최상위 값은 list여야 합니다.")

        try:
            return [Course.model_validate(item) for item in payload]
        except ValidationError as exc:
            raise CourseStoreError("수강기록 JSON에 잘못된 항목이 있습니다.") from exc

    def _atomic_write_unlocked(self, courses: list[Course]) -> None:
        temporary_path: Path | None = None
        try:
            if not self.data_path.parent.is_dir():
                raise OSError(f"Data directory does not exist: {self.data_path.parent}")

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                prefix=f".{self.data_path.name}.",
                suffix=".tmp",
                dir=self.data_path.parent,
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                json.dump(
                    [course.model_dump(mode="json") for course in courses],
                    temporary_file,
                    ensure_ascii=False,
                    indent=2,
                )
                temporary_file.write("\n")
                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            os.replace(temporary_path, self.data_path)
            temporary_path = None
            try:
                self._fsync_parent_directory()
            except OSError:
                # The replace above already committed the new JSON. Reporting a
                # failed POST here could make a client retry and append a duplicate.
                LOGGER.warning(
                    "수강기록 교체 후 디렉터리 fsync에 실패했습니다.",
                    exc_info=True,
                )
        except OSError as exc:
            raise CourseStoreError("수강기록 JSON 파일을 저장할 수 없습니다.") from exc
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    LOGGER.warning("임시 파일을 삭제하지 못했습니다: %s", temporary_path)

    def _fsync_parent_directory(self) -> None:
        """Persist the directory entry on POSIX; Windows has no equivalent here."""

        if os.name != "posix" or not hasattr(os, "O_DIRECTORY"):
            return
        directory_fd = os.open(self.data_path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)


def resolve_data_path() -> Path:
    """Allow tests and local experiments to select a different JSON file."""

    configured_path = os.getenv("COURSES_FILE")
    return Path(configured_path) if configured_path else DEFAULT_DATA_PATH


def create_app(data_path: str | Path | None = None) -> FastAPI:
    """Create an application with one shared repository instance."""

    repository = CourseRepository(data_path or resolve_data_path())
    application = FastAPI(
        title="수강기록 API",
        description="JSON 파일에서 수강기록을 조회하고 새 과목을 추가하는 REST API",
        version="1.0.0",
    )
    application.state.repository = repository

    @application.exception_handler(CourseStoreError)
    async def handle_store_error(
        _request: Request, exc: CourseStoreError
    ) -> JSONResponse:
        LOGGER.error(
            "[COURSES-API] storage_error: %s",
            exc,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": STORE_ERROR_DETAIL},
        )

    @application.get(
        "/courses",
        response_model=list[Course],
        summary="전체 수강기록 조회",
    )
    def get_courses() -> list[Course]:
        courses = repository.list_courses()
        LOGGER.info("[COURSES-API] GET /courses count=%d", len(courses))
        return courses

    @application.post(
        "/courses",
        response_model=Course,
        status_code=status.HTTP_201_CREATED,
        summary="새 수강기록 추가",
    )
    def post_course(course: Course) -> Course:
        stored_course = repository.add_course(course)
        LOGGER.info("[COURSES-API] POST /courses status=201")
        return stored_course

    return application


app = create_app()
