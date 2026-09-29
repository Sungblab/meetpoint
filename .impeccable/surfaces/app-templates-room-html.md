---
version: 1
slug: "app-templates-room-html"
primary_target: "app/templates/room.html"
related_targets: ["app/templates/join.html","app/templates/host.html","app/templates/index.html","app/templates/screen.html","app/templates/message.html","app/static/app.css"]
---

## Scope

Meetpoint 전체 화면 6개의 비주얼 교체(리디자인). 추천 목록(`room.html`)이 핵심 표면이고, 입장·내 정보(`join.html`), 주최자 관리(`host.html`), 첫 화면(`index.html`), 프로젝터(`screen.html`), 안내(`message.html`)가 같은 세계를 공유한다.

- 추천 목록, 입장, 내 정보, 관리: Operate
- 첫 화면: Persuade (주최자가 방을 만들게 한다)
- 프로젝터: Experience (강의실 뒤에서도 QR과 코드가 읽혀야 한다)

## Audience and job

창업·IT 밋업 참가자가 강연 뒤 네트워킹 시간에 서서 한 손으로 본다. 누구에게 걸어갈지, 왜, 첫마디는 무엇인지, 그 사람이 어디 있는지를 몇 초 안에 알아야 한다. 주최자는 노트북으로 QR을 띄우고 현황을 본다.

## Constraints

기능, 문구 규칙(해요체), 개인정보 규칙은 그대로. 사용자 입력은 textContent로만. 빌드 단계 없음. 사용자가 피하라고 한 것: 흔한 SaaS·AI 앱 느낌.

## Direction contract

THESIS: 추천 목록은 등록 데스크 위에 놓인 명찰들이다. 한 사람은 명찰 한 장: 멀리서도 읽히는 큰 이름, 관계 종류를 알리는 머리띠 색, 안내문처럼 적힌 찾는 법. 흰 카드·파란 버튼·작은 파스텔 태그로 된 SaaS 목록을 거부한다.

OWN-WORLD: 검정 테이블보 바탕(#131313) 위 흰 명찰 용지, 머리띠에 뚫린 펀칭 슬롯. 인쇄 머리띠 4색: 같은 분야 고수 노랑(#FFD21F), 다른 분야 도움 보라(#5B3DF5), 참가자 회색(#D9D9D4), 서로 연결 주홍(#FF4A1C). 색은 관계와 연결 상태에만 쓴다. Wanted Sans 한 가족, 이름은 800 굵기 큰 크기, 숫자는 고정폭. 그림자 대신 용지와 바탕의 명도 대비.

STORY: 참가자는 명찰을 훑어 머리띠 색으로 관계를 알고, 이유와 첫마디를 읽고, 찾는 법을 보고 걸어간다. 만나고 싶어요를 누르고, 서로 연결되면 명찰이 뒤집혀 뒷면의 전자 명함이 나오고, 한 번 눌러 휴대폰 연락처에 저장한다. 입장할 때는 적는 동안 내 명찰이 인쇄되듯 채워진다.

FIRST VIEWPORT: 휴대폰 390px. 상단 검정 바탕에 행사 이름과 '내 명찰' 버튼, 그 아래 머리띠 색 표시가 달린 필터 탭. 첫 명찰이 좌우 16px 여백으로 화면 폭을 채운다: 40px 머리띠(관계 이름, 슬롯), 34px 이름, 한 줄 소개, 17px 굵은 이유, 첫마디 패널, 위치 아이콘이 달린 찾는 법, 52px 만나고 싶어요 버튼까지 첫 화면 안에 들어온다.

FORM: 컨퍼런스 명찰(목걸이 명찰, Hello my name is 스티커 계열), 내 후보 목록 1순위, IMPECCABLE'S PICK으로 사용자가 선택. seed key d6468cc5. 시그니처 인터랙션: 서로 연결되는 순간 명찰이 한 번 뒤집혀 뒷면(전자 명함)이 드러난다. 모션은 이 한 번과 상태 전환(150~250ms)뿐.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Memorable moment

서로 연결될 때 명찰이 뒤집히며 전자 명함이 적힌 뒷면이 나온다.

## Unresolved

- 행사별 머리띠 색 커스터마이징은 하지 않는다(여러 주최자 서비스지만 지금은 Meetpoint 한 가지 세계).
