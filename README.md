# Meetpoint

행사 네트워킹 시간에 **만나야 할 사람부터 만나게** 해주는 웹앱입니다. 참가자가 QR을 찍고 2분 동안 자기소개를 적으면, AI가 오늘 먼저 만나면 좋을 사람과 그 이유, 건넬 첫마디까지 추천합니다.

2026년 9월 28일부터 10월 3일까지 혼자 기획하고 만들어 배포했습니다. 지금은 개발을 멈추고 2026년 10월 15일에 서비스를 내렸습니다. 코드는 MIT 라이선스로 공개합니다.

- 시연 영상: https://youtu.be/pQxVPFrZzW0

[![Meetpoint 시연 영상](https://img.youtube.com/vi/pQxVPFrZzW0/hqdefault.jpg)](https://youtu.be/pQxVPFrZzW0)

## 왜 만들었나

20~80명 규모 창업·IT 밋업은 강연이 끝나면 30분 남짓 네트워킹 시간이 있습니다. 그런데 누구에게 말을 걸지 고르고, 만나는 사람마다 자기소개를 반복하다 보면 그 시간이 금방 지나가죠. 소극적인 사람은 아예 아무에게도 못 가고 끝나기도 하고요.

Meetpoint는 추천을 두 가지로 나눕니다.

- **같은 분야 고수.** 나와 같은 일을 먼저, 더 잘한 사람에게 막힌 걸 묻습니다. 예: 지원사업 서류를 처음 쓰는 예비창업자와 먼저 합격한 대표.
- **다른 분야 도움.** 내가 못 하는 걸 하는 사람을 찾습니다. 예: 법인 설립과 세금이 막막한 창업자와 세무사.

## 흐름

1. 주최자가 이메일만 적고 방을 만듭니다. 회원가입은 없고, 관리 주소는 화면과 메일로 받습니다.
2. 프로젝터에 큰 참가 QR을 띄웁니다.
3. 참가자는 앱 설치 없이 QR로 들어와 이름, 소개, 같은 분야에 묻고 싶은 것, 다른 분야에서 필요한 것을 적습니다. 명함 사진을 찍으면 앞부분이 채워집니다.
4. 방 화면에 모든 참가자가 추천순으로 보이고, 새 사람이 들어오면 새로고침 없이 바로 나타납니다.
5. 둘 다 "만나고 싶어요"를 눌렀을 때만 서로에게 알림이 갑니다. 한쪽만 누른 건 상대에게 보이지 않습니다. 연결되면 명찰 뒷면에 전자 명함이 열리고, 한 번 눌러 만난 이유와 함께 휴대폰 연락처에 저장할 수 있습니다.

## 기술적으로 신경 쓴 것

**스택:** Python 3.12, FastAPI, SQLAlchemy async(SQLite·PostgreSQL), Jinja 템플릿, 순수 CSS/JS, SSE, Gemini API, Docker Compose, Nginx. 빌드 단계가 없습니다.

### 추천을 사람 수의 제곱만큼 부르지 않기

새 참가자가 들어오면 그 사람과 방의 나머지 모두를 **양방향으로 한 번에** 평가합니다. 후보 20명을 한 묶음으로 보내기 때문에 50명 방에서도 입장 한 번에 AI 호출은 3번 이하입니다. 응답은 JSON 스키마로 강제하고, 서버에서 한 번 더 검증합니다. 요청하지 않은 후보 id는 버리고, 빠진 후보는 대체 추천으로 채우는 식이죠.

### AI가 실패해도 추천이 비지 않게

키가 없거나 호출이 실패하거나 응답이 이상하면, 그 묶음은 키워드 비교로 추천합니다([`heuristic.py`](app/matching/heuristic.py)). 한국어는 조사가 붙으면 형태가 바뀌기 때문에("마케팅을", "마케팅") 한글 단어는 두 글자 조각으로 나눠 비교합니다. 현장에서 추천 목록이 비어 있는 일은 없습니다.

### 참가자 입력은 믿지 않기

추천 이유와 첫마디는 참가자가 쓴 소개를 바탕으로 AI가 만듭니다. 그래서 누군가 소개에 지시문을 심어 다른 사람 화면에 링크나 연락처를 띄우려 할 수 있습니다. AI 응답에서 주소, 이메일, 전화번호 모양은 서버가 지우고 나서 저장합니다. 화면에 사용자 입력을 넣을 때는 `textContent`만 쓰고요.

### 연락처는 서로 원할 때만

전화, 이메일, vCard는 서로 "만나고 싶어요"를 누른 경우에만 내보냅니다. 운영자 화면(`/admin`)에도 참가자 연락처는 나오지 않습니다. 명함 사진은 브라우저에서 줄인 뒤 글자만 읽고 버립니다. 이 규칙들은 테스트로 고정해 두었습니다.

### 현장에서 버티기

- 방 코드 추측을 늦추고, 교차 사이트 폼 전송을 막습니다.
- AI 호출은 참가자, 방, 하루 단위로 상한을 둡니다. 넘으면 키워드 추천으로 넘어갑니다.
- 실시간 연결(SSE)도 참가자별, 전체 수에 상한을 둡니다.
- 실시간 알림과 요청 제한을 프로세스 메모리에 둔 대신 uvicorn worker는 1개로 고정했습니다. 수백 명 규모 행사에는 충분합니다.

테스트는 80개이고, SQLite와 PostgreSQL 양쪽에서 돌립니다.

## 만들고 나서

만든 뒤에는 첫 행사 세 곳을 찾으려고 창업·IT 행사 주최측에 무료로 써보라고 제안했습니다. 돌아온 답은 정식 제휴로 진행하자는 것, 그러니까 이쪽이 제휴비를 내라는 거였죠.

거기서 구조가 보이더라고요. 참가자는 30분 네트워킹에 돈을 낼 이유가 없고, 주최자는 오히려 행사에 들어오는 도구에게 돈을 받는 쪽입니다. 20~80명 밋업에는 돈을 낼 사람이 없다고 판단해서 개발을 멈췄습니다.

저는 이번에 제품을 만드는 것과 그 제품이 쓰일 자리에 들어가는 것이 전혀 다른 일이라는 걸 배운 것 같습니다. 다음에는 만들기 전에 누가 돈을 내는지부터 확인하려고 합니다.

## 로컬에서 실행

Python 3.12와 [uv](https://docs.astral.sh/uv/)가 필요합니다. 기본 DB는 SQLite 파일입니다.

```bash
uv sync
cp .env.example .env   # GEMINI_API_KEY만 채워도 됩니다. 비워도 키워드 추천으로 동작합니다.
uv run uvicorn --factory app.main:create_app --reload --port 8000
```

`http://localhost:8000`을 열고, 참가자 두 명은 다른 브라우저나 시크릿 창으로 들어가 보면 됩니다.

## 테스트

```bash
uv run pytest
```

PostgreSQL에서도 돌리려면 빈 DB를 하나 만들고 주소를 넘깁니다. 테스트마다 테이블을 지우고 다시 만듭니다.

```bash
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@127.0.0.1:5432/meetpoint_test uv run pytest
```

## 구조

```
app/
  main.py            앱 생성, 시작 시 테이블 생성과 30일 약속으로 만든 옛 방 정리
  config.py          환경 변수 설정
  models.py          Room, Participant, Recommendation, Like
  broker.py          방 단위 실시간 알림
  routes/pages.py    입장, 내 정보, 명함 읽기, 프로젝터 화면
  routes/api.py      방 상태, 만나고 싶어요, SSE
  routes/host.py     주최자 화면
  routes/admin.py    운영자 화면
  matching/ai.py     Gemini 호출과 응답 검증
  matching/heuristic.py  키워드 대체 추천
  matching/service.py    추천 작업 실행과 저장
  templates/, static/    화면
deploy/              Nginx 설정, 백업·복원 스크립트
tests/               흐름, AI 호출, 단위 테스트
```

| 주소 | 누가 | 내용 |
| --- | --- | --- |
| `/` | 주최자 | 방 만들기, 참가 코드로 입장 |
| `/h/{관리토큰}` | 주최자 | QR, 참가자 수, 연결 수, 입장 마감, 방 지우기 |
| `/s/{코드}` | 프로젝터 | 큰 QR과 참가자 수. 관리 주소는 나오지 않습니다 |
| `/r/{코드}` | 참가자 | 입장 양식, 들어온 뒤에는 추천 목록 |
| `/r/{코드}/me` | 참가자 | 내 정보 고치기, 내 정보 지우기 |
| `/admin` | 운영자 | 주최자별 방 수, 모든 방과 참가자, 연결 수. `ADMIN_PASSWORD`로 열고, 비워두면 꺼집니다 |

## 개인정보

- 소개와 찾는 법은 같은 방 참가자에게 보입니다. 연락처는 서로 연결된 사람에게만 보입니다.
- 방과 참가자 정보는 참가자나 주최자가 지울 때까지 보관합니다. 2026-09-30 전에 만든 방만 안내했던 대로 30일 뒤 자동으로 지웁니다.
- 참가자는 언제든 "내 정보 지우기"로, 주최자는 "방 지우기"로 바로 지울 수 있습니다.
- 백업 스크립트는 덤프를 7일간 보관하므로, 지운 데이터가 백업에는 최대 7일 남습니다.
- 참가자가 적은 내용과 명함 사진은 추천을 위해 Gemini API로 보냅니다. 무료 등급 키는 Google이 입력을 서비스 개선에 쓸 수 있으니, 실제 행사에는 결제가 연결된 프로젝트의 키를 씁니다.

## 직접 띄우기 (OCI VM 기준)

Docker Compose로 앱과 PostgreSQL을 띄우고, 이미 있는 Nginx와 Certbot에 서브도메인 하나를 붙이는 구성입니다. 이미지는 ARM64와 AMD64를 모두 지원합니다.

```bash
git clone https://github.com/Sungblab/meetpoint.git ~/apps/meetpoint
cd ~/apps/meetpoint
cp .env.example .env
nano .env   # POSTGRES_PASSWORD, GEMINI_API_KEY, ADMIN_PASSWORD, SMTP_HOST, SMTP_USER, SMTP_PASSWORD, MAIL_FROM, PUBLIC_BASE_URL, APP_PORT
docker compose up -d --build --wait
curl http://127.0.0.1:8010/health
```

Nginx 설정은 `deploy/nginx-meetpoint.conf`를 복사해 도메인과 포트만 바꿉니다.

```bash
sudo cp deploy/nginx-meetpoint.conf /etc/nginx/sites-available/meetpoint
sudo ln -s /etc/nginx/sites-available/meetpoint /etc/nginx/sites-enabled/meetpoint
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d meetpoint.example.com
```

<details>
<summary>운영 메모</summary>

- **worker는 1개입니다.** 실시간 알림과 요청 제한을 프로세스 메모리에 두기 때문입니다.
- **실시간 알림은 SSE입니다.** Nginx에서 버퍼링을 끄지 않으면 알림이 늦게 옵니다. 앱이 `X-Accel-Buffering: no` 헤더도 보내지만 설정 파일의 SSE 블록을 그대로 쓰는 게 안전합니다.
- **백업.** `deploy/backup.sh`를 cron에 걸어두세요. 복원은 `deploy/restore.sh 백업파일`입니다.
- **업데이트.** `git pull && docker compose up -d --build --wait`
- **로그.** `docker compose logs -f app`
- **지우면 안 되는 것.** `docker compose down -v`는 DB 볼륨을 지웁니다. 재시작에는 쓰지 마세요.
- **행사 전날 점검.** 실제 휴대폰 두세 대로 입장, 추천, 서로 연결까지 한 번 끝까지 해보세요.
- DNS A 레코드는 VM 공인 IP를 가리켜야 합니다. 이미 다른 사이트가 80과 443으로 서비스 중이라면 OCI 보안 목록과 방화벽은 따로 열 필요가 없습니다.

</details>

<details>
<summary>AI 비용 조절</summary>

| 설정 | 기본값 | 설명 |
| --- | --- | --- |
| `AI_MODEL` | `gemini-3.8-flash` | 추천과 명함 읽기에 쓰는 모델 |
| `AI_EFFORT` | `low` | 추천의 thinking level(`minimal`, `low`, `medium`, `high`). 이유의 질이 아쉬우면 `medium`으로 올립니다 |
| `AI_CARD_EFFORT` | `low` | 명함 읽기의 thinking level |
| `AI_BATCH_SIZE` | `20` | 한 번에 평가할 후보 수 |
| `AI_CONCURRENCY` | `6` | 동시에 보내는 AI 요청 수 |
| `AI_DAILY_LIMIT` | `10000` | 하루 AI 호출 상한(추천과 명함 읽기를 합친 수). 넘으면 추천은 키워드로 채우고 명함 읽기는 멈춥니다 |
| `AI_ROOM_DAILY_LIMIT` | `3000` | 방 하나의 하루 추천 호출 상한 |

호출 수는 인원의 제곱에 비례해 늘어납니다. 모든 쌍을 한 번씩 평가하므로 100명이 차례로 들어오면 약 300번, 300명이면 약 2,400번 호출합니다. 첫 행사에서 Google AI Studio의 사용량과 요청 한도를 보고 모델과 thinking level을 정하세요. 참가자 한 명의 추천 작업은 한 번에 하나만 돌고, 소개 수정은 1분에 두 번까지 받습니다.

thinking level을 받지 않는 `gemini-2.5-flash` 같은 모델을 쓰려면 `AI_EFFORT=`와 `AI_CARD_EFFORT=`를 비워 둡니다.

</details>

## 라이선스

[MIT](LICENSE)
