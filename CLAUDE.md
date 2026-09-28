# Meetpoint 작업 메모

- FastAPI + SQLAlchemy async + Jinja 템플릿 + 순수 JS. 빌드 단계 없음.
- 테스트: `uv run pytest`. Postgres 확인은 `TEST_DATABASE_URL`을 준다.
- 사용자 입력을 화면에 넣을 때 JS는 `textContent`만 쓴다. `innerHTML` 금지.
- 추천은 `matching/service.py`가 참가자 입장·수정 때 한 사람 대 방 전체를 양방향으로 평가한다. AI 실패 시 `heuristic.py`로 채운다.
- 실시간 알림(`broker.py`)과 요청 제한은 프로세스 메모리에 있다. uvicorn worker는 1개로 유지한다.
- 연락처는 서로 좋아요한 경우에만 API 응답에 넣는다. 이 규칙을 바꾸면 `tests/test_flow.py`의 연결 테스트를 같이 고친다.
- 화면 디자인 규칙은 `DESIGN.md`, 제품 정보는 `PRODUCT.md`를 따른다. 색은 관계와 연결 상태에만 쓴다.
