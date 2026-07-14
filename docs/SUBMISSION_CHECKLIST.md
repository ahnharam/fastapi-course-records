# 실습 4 제출 체크리스트

## 프로젝트

- [x] 실습 3과 분리된 새로운 GitHub 저장소인가?
- [x] 저장소가 Public 상태인가?
- [x] `main.py`와 `courses.json`이 포함되어 있는가?
- [x] `courses.json`의 최상위 값이 list인가?
- [x] 각 항목에 `course_name`, `year`, `semester`, `grade` 문자열이 있는가?
- [x] `requirements.txt`, `.gitignore`, README가 있는가?
- [x] Postman 컬렉션이 있고 인증정보가 없는가?
- [x] 키, 토큰, 쿠키, `.env` 같은 비밀정보가 커밋되지 않았는가?
- [x] GitHub Actions가 통과했는가?

## API와 파일 저장

- [x] `GET /courses`가 전체 list와 200을 반환하는가?
- [x] `POST /courses`가 새 과목과 201을 반환하는가?
- [x] POST 이후 JSON list 마지막에 과목이 추가되는가?
- [x] POST 이후 재GET에도 같은 과목이 보이는가?
- [x] 잘못된 요청이 422를 반환하는가?
- [x] 잘못된 요청 후에도 정상 GET이 가능한가?
- [x] 파일 오류가 500으로 처리되고 서버가 종료되지 않는가?
- [x] `python -m pytest -q`가 통과하는가?

## 영상 필수 장면

- [x] 로컬 터미널에서 FastAPI 서버가 실행 중인가?
- [x] Postman과 로컬 터미널이 함께 보이는가?
- [x] Postman GET과 전체 기록 반환이 보이는가?
- [x] Postman POST와 새 과목 추가가 보이는가?
- [x] POST 뒤 다시 GET하여 새 과목을 확인하는가?
- [x] `courses.json`을 열어 실제 파일 반영을 확인하는가?
- [x] 가능하면 invalid POST 422와 이후 정상 GET도 보여 주는가?
- [x] 영상에 인증정보나 개인 비밀이 노출되지 않았는가?

## 최종 제출

- [ ] GitHub repository 주소를 KLAS에 입력했는가?
- [ ] YouTube 공개 범위가 전체 공개(Public)인가?
- [ ] 로그아웃 상태에서도 영상 링크가 열리는가?
- [ ] YouTube 링크를 KLAS에 입력했는가?
- [ ] 영상을 2026-07-20까지 유지할 수 있는가?
