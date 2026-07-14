# FastAPI Course Records

> JSON 파일의 수강기록을 조회하고 추가하는 오픈소스소프트웨어실습 4 프로젝트

| 제출자 | 학번 | 실행 모듈 | 실행 환경 |
|---|---:|---|---|
| 안하람 | 2023612016 | `main.py` | 로컬 FastAPI + Postman |

이 프로젝트는 별도 데이터베이스나 클라우드 배포 없이 `courses.json`을 읽고 수정합니다. `GET /courses`는 전체 수강기록을 반환하고, `POST /courses`는 검증된 과목을 list 마지막에 추가한 뒤 같은 JSON 파일에 영구 저장합니다.

## 과제 요구사항 대응

- FastAPI 서버와 `GET /courses`, `POST /courses`
- 코드에 하드코딩하지 않은 별도 `courses.json` list
- 문자열 필드 `course_name`, `year`, `semester`, `grade`
- POST 성공 시 `201 Created`
- 잘못된 body에 FastAPI/Pydantic `422 Unprocessable Entity`
- 파일 읽기·검증·저장 실패 시 일반화된 `500 Internal Server Error`
- 오류 이후에도 서버 프로세스와 후속 요청 유지
- UTF-8 JSON 읽기와 `ensure_ascii=False` 저장
- 동시 요청의 read-modify-write 손실 방지를 위한 thread lock + file lock
- 같은 디렉터리 임시 파일의 flush/fsync 후 `os.replace` 원자적 교체
- Postman 컬렉션, 자동 테스트, GitHub Actions, 영상 대본과 제출 체크리스트

## 빠른 실행

Python 3.10 이상을 권장합니다.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

서버 주소는 `http://127.0.0.1:8000`, 자동 API 문서는 `http://127.0.0.1:8000/docs`입니다. 이번 과제는 로컬 실행이 기준이며 EC2 배포는 필요하지 않습니다.

## API

### `GET /courses`

`courses.json`의 전체 list를 반환합니다.

```http
GET http://127.0.0.1:8000/courses
```

### `POST /courses`

```http
POST http://127.0.0.1:8000/courses
Content-Type: application/json
```

```json
{
  "course_name": "인간로봇상호작용",
  "year": "2026",
  "semester": "2",
  "grade": "A+"
}
```

성공하면 `201 Created`와 저장된 객체를 반환합니다. 이어서 GET을 호출하고 `courses.json`을 직접 열면 같은 항목을 확인할 수 있습니다.

## 입력 검증

| 필드 | 형식 |
|---|---|
| `course_name` | 공백 제거 후 1–100자의 문자열 |
| `year` | 공백 제거 후 1–10자의 문자열 |
| `semester` | 공백 제거 후 1–20자의 문자열 |
| `grade` | 공백 제거 후 1–10자의 문자열 |

모든 필드는 필수이며 정의하지 않은 추가 필드는 허용하지 않습니다. 숫자 `2026`처럼 문자열이 아닌 값, 누락 필드, 빈 값은 422 응답을 만들지만 서버를 종료시키지 않습니다. 과제에서 연도·학기 값의 구체적인 범위를 지정하지 않았으므로 문자열이라는 계약 밖의 제한은 두지 않습니다.

## Postman

1. Postman에서 **Import**를 선택합니다.
2. [`postman/FastAPI_Courses.postman_collection.json`](postman/FastAPI_Courses.postman_collection.json)을 가져옵니다.
3. 컬렉션 변수 `base_url`의 기본값 `http://127.0.0.1:8000`을 그대로 사용합니다.
4. `GET /courses` → `POST /courses` → 다시 `GET /courses` 순서로 실행합니다.
5. `Invalid POST /courses (422)`를 호출한 뒤 정상 GET이 계속 되는지도 확인합니다.

컬렉션에는 인증 토큰, 키, 쿠키 또는 계정 정보가 없습니다.

## 파일 저장 안전성

POST는 다음 순서로 처리됩니다.

1. 동일 프로세스의 thread lock을 획득합니다.
2. 같은 JSON 경로를 사용하는 다른 프로세스와 조정하는 file lock을 획득합니다.
3. 현재 JSON list를 읽고 전체 항목을 스키마로 검증합니다.
4. 새 과목을 list 마지막에 추가합니다.
5. 같은 디렉터리의 임시 파일에 새 JSON을 기록하고 flush/fsync합니다.
6. `os.replace`로 기존 파일을 원자적으로 교체합니다.

따라서 여러 요청이 동시에 들어와도 한 요청의 추가 내용이 다른 요청에 의해 사라지지 않으며, 교체 전에 오류가 발생하면 원본 파일은 유지됩니다. 잠금 파일 `courses.json.lock`과 임시 파일은 Git에서 제외됩니다.

이 방식은 한 컴퓨터의 소규모 파일 기반 실습에 적합합니다. 여러 서버가 공유하는 운영 환경이나 빈번한 대규모 쓰기에는 데이터베이스가 적합합니다.

## 테스트

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

테스트는 실제 제출용 `courses.json`을 수정하지 않습니다. pytest의 임시 디렉터리에 JSON 파일을 만들고 다음을 검증합니다.

- GET 전체 목록
- POST 201과 실제 파일 반영
- 잘못된 POST 422 이후 정상 GET
- 손상된 JSON과 파일 입출력 오류의 500 처리
- 여러 repository 인스턴스의 동시 쓰기에서 데이터 유실 없음
- 원자적 교체 실패 시 원본 유지와 임시 파일 정리
- Postman 컬렉션의 변수와 세 요청 구성

## 프로젝트 구조

```text
fastapi-course-records/
├─ main.py
├─ courses.json
├─ postman/FastAPI_Courses.postman_collection.json
├─ tests/
│  ├─ conftest.py
│  ├─ test_api.py
│  ├─ test_postman_collection.py
│  └─ test_storage.py
├─ docs/
│  ├─ DEMO_SCRIPT.md
│  └─ SUBMISSION_CHECKLIST.md
├─ .github/workflows/tests.yml
├─ requirements.txt
├─ requirements-dev.txt
├─ .gitignore
├─ .gitattributes
└─ LICENSE
```

## 제출

- 실습 4 전용의 새로운 public GitHub 저장소 주소를 제출합니다.
- 영상은 YouTube 전체 공개(Public)로 업로드하고 KLAS에 링크를 제출합니다.
- 영상에는 터미널, Postman GET·POST·재GET, 실제 JSON 파일 반영이 모두 보여야 합니다.
- 과제 표기 마감은 `2026-07-08 23:59:59`, 영상 유지 기한은 `2026-07-20`입니다.

자세한 순서는 [데모 영상 대본](docs/DEMO_SCRIPT.md)과 [제출 체크리스트](docs/SUBMISSION_CHECKLIST.md)를 확인하세요.

## 라이선스

이 프로젝트는 [MIT License](LICENSE)로 공개합니다.
