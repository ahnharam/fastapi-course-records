# 실습 4 FastAPI 데모 영상 대본

권장 길이는 약 4–6분입니다. 과제에 영상 길이 제한은 없으며, Postman과 로컬 FastAPI 터미널이 함께 보이는 구성을 우선합니다.

## 촬영 전 준비

- 새 실습 4 GitHub 저장소가 public인지 확인
- `courses.json`을 제출용 초기 상태로 복원
- Postman에 `postman/FastAPI_Courses.postman_collection.json` import
- 컬렉션 변수 `base_url`이 `http://127.0.0.1:8000`인지 확인
- 터미널과 Postman을 좌우로 배치
- AWS 키, 토큰, 쿠키, 개인 메시지 등 민감정보가 화면에 없는지 확인

## 0:00–0:40 · 과제 소개와 파일

1. `main.py`, `courses.json`, `requirements.txt`가 있는 프로젝트 폴더를 보여 줍니다.
2. `courses.json`을 열어 현재 list와 초기 과목 수를 보여 줍니다.
3. 다음처럼 설명합니다.

> 오픈소스소프트웨어실습 4 FastAPI 과제입니다. 로컬 서버가 별도의 JSON 파일에서 수강기록을 읽고, POST 요청을 파일에 영구 저장하는 과정을 확인하겠습니다.

## 0:40–1:10 · 로컬 서버 실행

터미널에서 실행합니다.

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload
```

터미널의 `Uvicorn running on http://127.0.0.1:8000` 메시지를 보여 주고, 이후에도 이 터미널을 Postman과 함께 보이게 둡니다.

## 1:10–1:50 · 첫 번째 GET

1. Postman의 **GET /courses**를 엽니다.
2. URL `{{base_url}}/courses`와 GET 메서드를 보여 줍니다.
3. **Send**를 누릅니다.
4. `200 OK`와 전체 JSON list를 보여 줍니다.
5. 터미널의 `GET /courses ... 200 OK` 로그도 같은 화면에서 확인합니다.

## 1:50–2:50 · POST로 새 과목 추가

1. Postman의 **POST /courses**를 엽니다.
2. Body가 raw JSON이고 다음 네 문자열 필드를 포함하는지 보여 줍니다.

```json
{
  "course_name": "인간로봇상호작용",
  "year": "2026",
  "semester": "2",
  "grade": "A+"
}
```

3. **Send**를 누릅니다.
4. `201 Created`와 반환된 과목을 보여 줍니다.
5. 터미널의 `POST /courses ... 201 Created` 로그를 보여 줍니다.

## 2:50–3:40 · 재GET과 실제 파일 반영

1. 다시 **GET /courses**를 호출합니다.
2. 방금 추가한 `인간로봇상호작용`이 list 마지막에 있는지 보여 줍니다.
3. 터미널을 계속 보이게 한 채 에디터에서 `courses.json`을 다시 엽니다.
4. 같은 과목이 실제 파일에 저장된 것을 보여 줍니다.

이 장면이 핵심입니다. 단순 GET·POST만 보여 주지 말고, POST 이후 재GET과 파일 반영을 모두 증명합니다.

## 3:40–4:30 · 잘못된 요청에도 서버 유지

이 장면은 평가 기준의 오류 내구성을 명확히 보여 주는 권장 증빙입니다.

1. **Invalid POST /courses (422)**를 호출합니다.
2. `422 Unprocessable Entity` 응답을 보여 줍니다.
3. 터미널 프로세스가 종료되지 않았는지 확인합니다.
4. 정상 **GET /courses**를 한 번 더 호출해 `200 OK`를 보여 줍니다.

## 4:30–끝 · GitHub와 마무리

1. 새 public GitHub 저장소를 엽니다.
2. `main.py`, `courses.json`, Postman 컬렉션과 테스트 파일을 짧게 보여 줍니다.
3. 다음처럼 마무리합니다.

> GET으로 JSON 전체 기록을 조회하고, POST로 새 과목을 파일에 저장한 뒤, 재GET과 파일 내용으로 반영을 확인했습니다. 잘못된 요청 후에도 FastAPI 서버가 계속 동작하는 것을 확인했습니다.

## 촬영 후

- YouTube 공개 범위를 **일부 공개(Unlisted)**로 설정
- 로그아웃 또는 시크릿 창에서 링크 접근 확인
- 링크는 공개 README가 아니라 KLAS에 제출
- 영상은 2026-07-20까지 유지
- 데모로 변경된 `courses.json`은 필요하면 제출용 초기 상태로 복원하되, 녹화에서는 실제 변경 장면을 유지
