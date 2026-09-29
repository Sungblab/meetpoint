# Meetpoint

행사 네트워킹 시간에 **만나야 할 사람부터 만나게** 해주는 웹앱입니다.

참가자는 QR을 찍고 2분만 적습니다. 앱 설치와 회원가입은 없습니다. Meetpoint는 두 가지 축으로 오늘 만나면 좋을 사람을 추천하고, 왜 만나야 하는지와 첫마디까지 알려줍니다.

- **같은 분야 고수.** 나와 같은 일을 더 잘하는 사람에게 막힌 걸 묻습니다. 예: AI 서비스를 만드는 개발자가 "LLM 비용을 어떻게 줄였는지" 물어볼 사람.
- **다른 분야 도움.** 내가 못 하는 걸 하는 사람을 찾습니다. 예: 개발자가 마케팅을 물어볼 마케터.

소극적인 사람도 부담 없이 다가갈 수 있게, 서로 "만나고 싶어요"를 눌렀을 때만 양쪽에 알립니다. 한쪽만 누른 건 상대에게 보이지 않습니다.

## 흐름

1. 주최자가 첫 화면에서 방을 만들면 참가 QR과 관리 주소를 받습니다.
2. 주최자는 프로젝터 화면을 띄웁니다. 이 화면에는 관리 주소가 나오지 않습니다.
3. 참가자는 QR로 들어와 이름, 자기소개, 같은 분야에 묻고 싶은 것, 다른 분야에서 필요한 것을 적습니다. 명함 사진으로 앞부분을 채울 수 있습니다.
4. 방 화면에 모든 참가자가 추천순으로 보입니다. 새 사람이 들어오면 새로고침 없이 바로 나타납니다.
5. 둘 다 "만나고 싶어요"를 누르면 서로에게 알림이 가고 연락처가 열립니다. "나를 찾는 법"은 처음부터 모두에게 보입니다.

## 화면과 주소

| 주소 | 누가 | 내용 |
| --- | --- | --- |
| `/` | 주최자 | 방 만들기, 참가 코드로 입장 |
| `/h/{관리토큰}` | 주최자 | QR, 참가자 수, 연결 수, 입장 마감, 방 지우기 |
| `/s/{코드}` | 프로젝터 | 큰 QR과 참가자 수 |
| `/r/{코드}` | 참가자 | 입장 양식, 들어온 뒤에는 추천 목록 |
| `/r/{코드}/me` | 참가자 | 내 정보 고치기, 내 정보 지우기 |

## 추천 방식

새 참가자가 들어오거나 소개를 고치면, 그 사람과 방의 나머지 모두를 **양방향으로 한 번에** 평가합니다. 후보 20명을 한 묶음으로 보내므로 50명 방에서도 입장당 호출은 3번 이하입니다.

- **AI 추천.** `GEMINI_API_KEY`가 있으면 Gemini가 관계 종류, 점수, 한 문장 이유, 첫마디를 만듭니다. 기본 모델은 `gemini-3.8-flash`이고, 현장에서 기다리는 시간을 줄이려고 thinking level은 `low`로 둡니다. 응답은 JSON 스키마로 강제하고 서버에서 한 번 더 검증합니다.
- **키워드 대체 추천.** AI 키가 없거나, 호출이 실패하거나, 응답이 이상하면 그 묶음은 키워드 비교로 추천합니다. 한국어 조사를 고려해 두 글자 조각으로 비교합니다. 추천이 비어 있는 일은 없습니다.
- **목록에서 지우지 않습니다.** 연결점이 없어도 목록 아래쪽에 남깁니다. 추천 이유가 틀릴 수 있으니 판단은 사람이 합니다.

명함 사진은 브라우저에서 줄인 뒤 Gemini가 글자만 읽고 버립니다. 서버에 저장하지 않습니다.

## 개인정보

- 소개와 찾는 법은 같은 방 참가자에게 보입니다. 연락처는 서로 연결된 사람에게만 보입니다.
- 방은 만든 지 30일이 지나면 참가자, 추천, 연결 기록과 함께 자동으로 지워집니다. `ROOM_RETENTION_DAYS`로 바꿉니다.
- 참가자는 언제든 "내 정보 지우기"로, 주최자는 "방 지우기"로 바로 지울 수 있습니다.
- 백업 스크립트는 덤프를 7일간 보관하므로, 지운 데이터가 백업에는 최대 7일 남습니다.
- 참가자가 적은 내용과 명함 사진은 추천을 위해 Gemini API로 보냅니다. 무료 등급 키는 Google이 입력을 서비스 개선에 쓸 수 있으니, 실제 행사에는 결제가 연결된 프로젝트의 키를 씁니다.

## 로컬에서 실행

Python 3.12와 [uv](https://docs.astral.sh/uv/)가 필요합니다. 기본 DB는 SQLite 파일입니다.

```bash
uv sync
cp .env.example .env   # GEMINI_API_KEY만 채워도 됩니다. 비워도 동작합니다.
uv run uvicorn --factory app.main:create_app --reload --port 8000
```

`http://localhost:8000`을 열고, 참가자 두 명은 다른 브라우저나 시크릿 창으로 들어가 보면 됩니다.

## 테스트

```bash
uv run pytest
```

Postgres에서도 돌리려면 빈 DB를 하나 만들고 주소를 넘깁니다. 테스트마다 테이블을 지우고 다시 만듭니다.

```bash
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@127.0.0.1:5432/meetpoint_test uv run pytest
```

## OCI VM에 배포

Docker Compose로 앱과 Postgres를 띄우고, 이미 있는 Nginx와 Certbot에 서브도메인 하나를 붙이는 구성입니다. 이미지는 ARM64와 AMD64를 모두 지원합니다.

```bash
# 1. 코드 받기
git clone https://github.com/Sungblab/meetpoint.git ~/apps/meetpoint
cd ~/apps/meetpoint

# 2. 설정
cp .env.example .env
nano .env   # POSTGRES_PASSWORD, GEMINI_API_KEY, PUBLIC_BASE_URL, APP_PORT

# 3. 실행
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

도메인의 DNS A 레코드는 VM 공인 IP를 가리켜야 합니다. 이미 다른 사이트가 80과 443으로 서비스 중이라면 OCI 보안 목록과 방화벽은 따로 열 필요가 없습니다.

### 운영 메모

- **worker는 1개입니다.** 실시간 알림과 요청 제한을 프로세스 메모리에 두기 때문입니다. 수백 명 규모 행사에는 충분합니다.
- **실시간 알림은 SSE입니다.** Nginx에서 버퍼링을 끄지 않으면 알림이 늦게 옵니다. 앱이 `X-Accel-Buffering: no` 헤더도 보내지만 설정 파일의 SSE 블록을 그대로 쓰는 게 안전합니다.
- **백업.** `deploy/backup.sh`를 cron에 걸어두세요. 복원은 `deploy/restore.sh 백업파일`입니다.
- **업데이트.** `git pull && docker compose up -d --build --wait`
- **로그.** `docker compose logs -f app`
- **지우면 안 되는 것.** `docker compose down -v`는 DB 볼륨을 지웁니다. 재시작에는 쓰지 마세요.
- **행사 전날 점검.** 실제 휴대폰 두세 대로 입장, 추천, 서로 연결까지 한 번 끝까지 해보세요.

## AI 비용 조절

| 설정 | 기본값 | 설명 |
| --- | --- | --- |
| `AI_MODEL` | `gemini-3.8-flash` | 추천과 명함 읽기에 쓰는 모델 |
| `AI_EFFORT` | `low` | 추천의 thinking level(`minimal`, `low`, `medium`, `high`). 이유의 질이 아쉬우면 `medium`으로 올립니다 |
| `AI_CARD_EFFORT` | `low` | 명함 읽기의 thinking level |
| `AI_BATCH_SIZE` | `20` | 한 번에 평가할 후보 수 |
| `AI_CONCURRENCY` | `6` | 동시에 보내는 AI 요청 수 |

호출 수는 인원의 제곱에 비례해 늘어납니다. 모든 쌍을 한 번씩 평가하므로 100명이 차례로 들어오면 약 300번, 300명이면 약 2,400번 호출합니다. 첫 행사에서 Google AI Studio의 사용량과 요청 한도를 보고 모델과 thinking level을 정하세요. 한도를 넘어 실패한 묶음은 키워드 추천으로 채워집니다.

thinking level을 받지 않는 `gemini-2.5-flash` 같은 모델을 쓰려면 `AI_EFFORT=`와 `AI_CARD_EFFORT=`를 비워 둡니다. 모델을 바꾼 뒤에는 추천 이유의 질을 실제 입력으로 확인해 보세요.

## 구조

```
app/
  main.py            앱 생성, 시작 시 테이블 생성과 오래된 방 정리
  config.py          환경 변수 설정
  models.py          Room, Participant, Recommendation, Like
  broker.py          방 단위 실시간 알림
  routes/pages.py    입장, 내 정보, 명함 읽기, 프로젝터 화면
  routes/api.py      방 상태, 만나고 싶어요, SSE
  routes/host.py     주최자 화면
  matching/ai.py     Gemini 호출과 응답 검증
  matching/heuristic.py  키워드 대체 추천
  matching/service.py    추천 작업 실행과 저장
  templates/, static/    화면
deploy/              Nginx 설정, 백업·복원 스크립트
tests/               흐름, AI 호출, 단위 테스트
```
