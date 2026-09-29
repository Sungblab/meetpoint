---
name: Meetpoint
description: 등록 데스크 위의 명찰. 검정 테이블보 위 흰 명찰 용지와, 관계를 알리는 인쇄 머리띠 4색.
colors:
  table: "#131313"
  table-raised: "#1f1f1f"
  table-line: "#333331"
  on-table: "#f3f3f0"
  on-table-2: "#a7a7a2"
  stock: "#ffffff"
  stock-2: "#f0f0ec"
  stock-line: "#d6d6d0"
  ink: "#111111"
  ink-2: "#4f4f4a"
  ink-3: "#6b6b65"
  same: "#ffd21f"
  other: "#5b3df5"
  attendee: "#d9d9d4"
  match: "#ff4a1c"
  danger: "#c8261a"
  danger-wash: "#fff0ec"
  danger-ink: "#8f1d0e"
typography:
  display:
    fontFamily: '"Wanted Sans Variable", "Wanted Sans", -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif'
    fontSize: "40px"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.03em"
  projector:
    fontFamily: '"Wanted Sans Variable", "Wanted Sans", -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif'
    fontSize: "clamp(40px, 5.4vw, 96px)"
    fontWeight: 800
    lineHeight: 1.1
    letterSpacing: "-0.03em"
  name:
    fontFamily: '"Wanted Sans Variable", "Wanted Sans", -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif'
    fontSize: "34px"
    fontWeight: 800
    lineHeight: 1.12
    letterSpacing: "-0.025em"
  headline:
    fontFamily: '"Wanted Sans Variable", "Wanted Sans", -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif'
    fontSize: "24px"
    fontWeight: 800
    lineHeight: 1.25
    letterSpacing: "-0.02em"
  title:
    fontFamily: '"Wanted Sans Variable", "Wanted Sans", -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif'
    fontSize: "18px"
    fontWeight: 800
    lineHeight: 1.35
    letterSpacing: "-0.01em"
  reason:
    fontFamily: '"Wanted Sans Variable", "Wanted Sans", -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif'
    fontSize: "17px"
    fontWeight: 700
    lineHeight: 1.5
  body:
    fontFamily: '"Wanted Sans Variable", "Wanted Sans", -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif'
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
  button:
    fontFamily: '"Wanted Sans Variable", "Wanted Sans", -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif'
    fontSize: "16px"
    fontWeight: 800
    lineHeight: 1.2
  label:
    fontFamily: '"Wanted Sans Variable", "Wanted Sans", -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif'
    fontSize: "14px"
    fontWeight: 800
    lineHeight: 1.5
  band:
    fontFamily: '"Wanted Sans Variable", "Wanted Sans", -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif'
    fontSize: "13px"
    fontWeight: 800
    letterSpacing: "0.01em"
  caption:
    fontFamily: '"Wanted Sans Variable", "Wanted Sans", -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif'
    fontSize: "12px"
    fontWeight: 800
  numeral:
    fontFamily: '"Wanted Sans Variable", "Wanted Sans", -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif'
    fontSize: "36px"
    fontWeight: 800
    lineHeight: 1.1
    fontFeature: "tnum"
  code:
    fontFamily: '"Wanted Sans Variable", "Wanted Sans", -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif'
    fontSize: "40px"
    fontWeight: 800
    letterSpacing: "0.08em"
    fontFeature: "tnum"
rounded:
  radius: "14px"
  radius-sm: "10px"
  button: "12px"
  pill: "999px"
spacing:
  gap-sm: "8px"
  gap: "12px"
  gutter: "16px"
  card: "18px"
  sheet: "20px"
  section: "36px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.stock}"
    typography: "{typography.button}"
    rounded: "{rounded.button}"
    padding: "0 18px"
    height: "48px"
  button-primary-hover:
    backgroundColor: "#2b2b2b"
  button-secondary:
    backgroundColor: "{colors.stock-2}"
    textColor: "{colors.ink}"
    typography: "{typography.button}"
    rounded: "{rounded.button}"
    padding: "0 18px"
    height: "48px"
  button-secondary-hover:
    backgroundColor: "#e3e3de"
  button-secondary-desk:
    backgroundColor: "#2b2b29"
    textColor: "{colors.on-table}"
  button-secondary-desk-hover:
    backgroundColor: "#363634"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.button}"
    height: "48px"
  button-danger:
    backgroundColor: "transparent"
    textColor: "{colors.danger}"
    rounded: "{rounded.button}"
    height: "48px"
  button-danger-hover:
    backgroundColor: "{colors.danger-wash}"
  button-small:
    padding: "0 14px"
    height: "40px"
  like-button:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.stock}"
    typography: "{typography.button}"
    rounded: "{rounded.button}"
    height: "52px"
    width: "100%"
  like-button-liked:
    backgroundColor: "{colors.stock-2}"
    textColor: "{colors.ink}"
  like-button-matched:
    backgroundColor: "{colors.match}"
    textColor: "{colors.ink}"
  like-button-matched-hover:
    backgroundColor: "#ff6440"
  badge:
    backgroundColor: "{colors.stock}"
    textColor: "{colors.ink}"
    rounded: "{rounded.radius}"
    padding: "18px 18px 0"
  band:
    backgroundColor: "{colors.attendee}"
    textColor: "{colors.ink}"
    typography: "{typography.band}"
    padding: "0 16px"
    height: "40px"
  band-common:
    backgroundColor: "{colors.same}"
    textColor: "{colors.ink}"
  band-complement:
    backgroundColor: "{colors.other}"
    textColor: "{colors.stock}"
  band-matched:
    backgroundColor: "{colors.match}"
    textColor: "{colors.ink}"
  band-pending:
    backgroundColor: "{colors.attendee}"
    textColor: "{colors.ink-2}"
  opener:
    backgroundColor: "{colors.stock-2}"
    textColor: "{colors.ink}"
    rounded: "{rounded.radius-sm}"
    padding: "12px 14px"
  badge-back:
    backgroundColor: "{colors.stock-2}"
    textColor: "{colors.ink}"
    padding: "16px 18px 18px"
  sheet:
    backgroundColor: "{colors.stock}"
    textColor: "{colors.ink}"
    rounded: "{rounded.radius}"
    padding: "22px 20px"
  desk:
    backgroundColor: "transparent"
    textColor: "{colors.on-table}"
    rounded: "{rounded.radius}"
    padding: "20px"
  input:
    backgroundColor: "{colors.stock}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.radius-sm}"
    padding: "12px 14px"
    height: "48px"
  input-desk:
    backgroundColor: "{colors.table-raised}"
    textColor: "{colors.on-table}"
  ask-common-title:
    backgroundColor: "{colors.same}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    padding: "10px 14px"
  ask-complement-title:
    backgroundColor: "{colors.other}"
    textColor: "{colors.stock}"
    typography: "{typography.label}"
    padding: "10px 14px"
  chip:
    backgroundColor: "{colors.table-raised}"
    textColor: "{colors.on-table}"
    rounded: "{rounded.pill}"
    padding: "0 14px"
    height: "40px"
  chip-hover:
    backgroundColor: "#2a2a28"
  chip-active:
    backgroundColor: "{colors.stock}"
    textColor: "{colors.ink}"
  me-chip:
    backgroundColor: "{colors.stock}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.radius-sm}"
    padding: "12px 14px 8px"
    height: "44px"
  status:
    backgroundColor: "{colors.table-raised}"
    textColor: "{colors.on-table}"
    rounded: "{rounded.radius-sm}"
    padding: "12px 14px"
  alert:
    backgroundColor: "{colors.danger-wash}"
    textColor: "{colors.danger-ink}"
    rounded: "{rounded.radius-sm}"
    padding: "12px 14px"
  toast:
    backgroundColor: "{colors.stock}"
    textColor: "{colors.ink}"
    rounded: "{rounded.button}"
    padding: "14px 16px"
  toast-match:
    backgroundColor: "{colors.match}"
    textColor: "{colors.ink}"
---

# Design System: Meetpoint

## Overview

**Creative North Star: "등록 데스크 위의 명찰"**

Meetpoint의 모든 화면은 행사장 등록 데스크다. 바탕은 검정 테이블보이고, 그 위에 흰 명찰 용지가 놓인다. 한 사람은 명찰 한 장이다. 이름은 멀리서도 읽힐 만큼 크고, 명찰 머리의 인쇄 띠 색이 그 사람과 나의 관계를 알려 준다. 찾는 법은 안내문처럼 적혀 있다. 테이블에서 한 손으로 명찰을 훑고, 누구에게 갈지 정하고, 바로 걸어가는 흐름을 위한 세계다.

화면은 두 재질로만 이루어진다. 검정 테이블(어두운 면, 테두리만 있는 영역)과 흰 용지(명찰, 양식 시트)다. 깊이는 그림자가 아니라 두 재질의 명도 차이에서 나온다. 색은 거의 없다. 노랑·보라·회색·주홍의 인쇄 머리띠 4색이 관계와 연결 상태를 말할 때만 나오고, 나머지는 잉크와 용지의 무채색이다. 글꼴은 Wanted Sans 한 가족이며 굵기 800의 큰 글자로 위계를 세운다. 흰 카드, 파란 버튼, 작은 파스텔 태그로 된 SaaS 목록과는 다른 쪽을 택했다.

움직임은 한 번의 사건에 모았다. 서로 연결되는 순간 명찰이 한 번 뒤집히고, 뒷면(전자 명함)이 아래로 펼쳐진다. 그 밖의 움직임은 짧은 상태 전환뿐이고, 동작 줄이기 설정에서는 모두 꺼진다. 라이트 모드는 없다. 테이블은 언제나 검정이다(`color-scheme: dark`, `theme-color` #131313).

**Key Characteristics:**
- 검정 테이블(#131313) 위 흰 명찰 용지(#ffffff), 그림자 없는 명도 대비
- 명찰 머리의 40px 인쇄 띠와 가운데 뚫린 목걸이 슬롯
- 관계와 연결 상태에만 쓰는 머리띠 4색
- Wanted Sans Variable 한 가족, 이름과 제목은 800 굵기
- 주 행동은 잉크 버튼, 색 있는 CTA 없음
- 서로 연결될 때 한 번 뒤집히는 명찰이 유일한 연출

## Colors

무채색의 테이블과 용지 위에 인쇄 머리띠 4색만 얹는 팔레트다. 모든 값은 `app/static/app.css`의 `:root` 사용자 정의 속성이 원본이다.

### Primary
머리띠 4색은 서로 대등한 신호색이다. 브랜드 강조색이 아니라 관계를 표시하는 인쇄 잉크로 다룬다.

- **고수 노랑** (same): 같은 분야 고수. 명찰 머리띠, 같은 분야 필터 칩의 색 표시, 입장 양식의 "같은 분야 고수에게 묻고 싶은 것" 머리, 첫 화면 범례에 쓴다. 명찰 모양 워드마크와 파비콘의 머리띠도 이 색이다. 위에 올리는 글자는 잉크.
- **도움 보라** (other): 다른 분야 도움. 쓰임은 노랑과 짝을 이룬다. 네 색 중 유일하게 흰 글자(stock)를 올린다.
- **연결 주홍** (match): 서로 연결. 연결된 명찰의 머리띠, 연결된 뒤의 만나고 싶어요 버튼, 연결 알림(toast), 범례에 쓴다. 위 글자는 잉크.
- **참가자 회색** (attendee): 관계가 아직 없거나 분석 중인 참가자의 머리띠, 주최자 화면과 프로젝터 QR 명찰의 머리띠, 내 명찰 버튼의 띠, 텍스트 선택 배경. 분석 중일 때는 글자를 ink-2로 낮춘다.

### Neutral
- **테이블보 검정** (table): 모든 페이지 바탕, 상단 고정 바 바탕, 머리띠 슬롯의 구멍 색.
- **한 단 올라온 테이블** (table-raised): 테이블 위 컨트롤 면. 필터 칩, 상태 줄, 안내(notice), 테이블 위 입력칸 바탕.
- **테이블 선** (table-line): 테이블 위 영역(desk)의 1px 테두리, 목록 구분선, 통계 칸 구분선, 빈 목록의 점선 테두리.
- **테이블 위 글자** (on-table): 검정 바탕 위 본문과 제목.
- **테이블 위 보조 글자** (on-table-2): 검정 바탕 위 설명, 캡션, 통계 라벨.
- **명찰 용지** (stock): 명찰, 양식 시트, 입력칸, 선택된 칩, 알림.
- **뒷면 용지** (stock-2): 첫마디 패널, 명찰 뒷면, 보조 버튼, 두 가지 질문 입력칸, 읽기 전용 입력칸.
- **용지 선** (stock-line): 용지 위 입력칸 테두리, 소개 더 보기 위 구분선, 명찰 뒷면의 점선 절취선.
- **잉크** (ink): 용지 위 글자, 주 행동 버튼 바탕, 포커스 링 안쪽.
- **옅은 잉크** (ink-2): 한 줄 소개, 찾는 법 문장, 접힌 소개 요약.
- **흐린 잉크** (ink-3): 용지 위 캡션, placeholder, "선택" 같은 보조 표시. 흰 용지 위 대비 5.36:1.

### 오류
- **경고 빨강** (danger): 흰 용지 위 지우기 버튼 글자와 테두리. 검정 테이블 위에서는 대비가 3.3:1밖에 안 되므로 쓰지 않고, 테이블 위 지우기 버튼은 on-table 글자와 #4d4d4a 테두리로 바꾼다.
- **경고 바탕** (danger-wash)과 **경고 글자** (danger-ink): 양식 오류 알림(alert)과 흰 용지 위 지우기 버튼의 hover 바탕.

### Named Rules
**The Headband Rule.** 머리띠 4색은 관계와 연결 상태를 말할 때만 쓴다: 명찰 머리띠, 필터 칩의 색 표시, 두 가지 질문의 머리, 범례 견본, 연결된 뒤의 버튼과 알림, 전자 명함 위쪽 4px 띠(연결되면 주홍, 입장 미리보기에서는 회색). 예외는 명찰 모양 워드마크와 파비콘의 노란 띠 하나다. 링크, 아이콘, 장식 배경, 일반 버튼에는 쓰지 않는다. (현재 "추천 이유를 만들고 있어요" 상태 줄의 노란 점은 이 규칙에서 벗어나 있다.)

**The Ink Action Rule.** 주 행동은 잉크 바탕(#111111)에 흰 글자인 버튼이다. 색으로 부르는 CTA는 없다. 버튼이 색을 띠는 경우는 서로 연결된 상태를 보여 주는 주홍 만나고 싶어요 버튼 하나뿐이다.

**The Table and Stock Rule.** 화면의 모든 것은 검정 테이블 위에 있거나 흰 용지 위에 있다. 테이블 위 영역은 채우지 않고 1px 선으로만 두르며, 컨트롤만 table-raised 한 단으로 올린다. 회색 카드 층을 새로 만들지 않는다.

## Typography

**Display Font:** Wanted Sans Variable (Wanted Sans, -apple-system, Apple SD Gothic Neo, Malgun Gothic, sans-serif 순으로 대체)
**Body Font:** 같은 가족

**Character:** 한 가족을 굵기로만 나눈다. 이름, 제목, 버튼, 라벨, 머리띠 글자는 모두 800이라 명찰 인쇄처럼 단단하고, 추천 이유는 700, 본문은 400·600이다. 글꼴은 jsDelivr의 `wanteddev/wanted-sans@v1.0.3` 가변 분할 웹폰트 CSS로 불러온다. 본문에는 `word-break: keep-all`을 걸어 한국어가 어절 단위로 줄바꿈된다.

### Hierarchy
- **Display** (800, 40px에서 960px 이상 52px, 1.15, -0.03em): 첫 화면 제목 한 곳. `text-wrap: balance`.
- **Projector** (800, clamp(40px, 5.4vw, 96px), 1.1, -0.03em): 프로젝터 화면의 행사 이름. 강의실 뒤에서 읽히는 크기다.
- **Name** (800, 34px, 1.12, -0.025em): 명찰의 사람 이름. 첫 화면 예시 명찰에서는 28px, 입장 미리보기에서는 30px로 줄인다.
- **Headline** (800, 24px, 1.25, -0.02em): 입장·관리·안내 화면의 방 이름과 제목.
- **Title** (800, 18px, 1.35, -0.01em): 시트와 테이블 위 영역의 소제목.
- **Reason** (700, 17px, 1.5): 명찰 안의 추천 이유 한 문장. `text-wrap: pretty`.
- **Body** (400, 16px, 1.5): 기본 본문과 입력칸 글자. 첫마디·찾는 법·소개 내용은 15px로 한 단 작다.
- **Button** (800, 16px, 1.2): 모든 버튼. 작은 버튼은 14px.
- **Label** (800, 14px): 입력칸 이름, 두 가지 질문의 머리, 내 명찰 버튼.
- **Band** (800, 13px, 0.01em): 머리띠의 관계 이름.
- **Caption** (800, 12px, ink-3): 첫마디 패널의 "이렇게 말을 걸어보세요", 소개 항목 이름.
- **Numeral** (800, 36px, 1.1, tabular-nums): 관리 화면 통계. 프로젝터의 코드와 참가자 수는 clamp(40px, 5vw, 88px).
- **Code** (800, 40px, 0.08em, tabular-nums): 참가 코드. 코드 입력칸도 0.08em 자간에 대문자로 보여 준다.

### Named Rules
**The Name First Rule.** 명찰 안에서 가장 큰 글자는 이름이다(34px/800). 추천 목록 화면에서는 방 이름(20px)보다도 크다. 이유, 첫마디, 찾는 법은 이름 아래로 한 단씩 작아진다.

**The One Family Rule.** Wanted Sans Variable 한 가족만 쓴다. 위계는 크기와 굵기로 만들고, 두 번째 글꼴이나 기울임은 들이지 않는다.

**The Fixed Digits Rule.** 참가 코드, 참가자 수, 연결 수처럼 바뀌는 숫자는 `font-variant-numeric: tabular-nums`로 자리를 고정한다.

## Layout

휴대폰 한 열이 기준이다. `.page`는 좌우 16px 여백, 위 20px(760px 이상 28px), 아래 96px에 safe-area를 더한 여백을 둔다. 폭은 쓰임에 따라 세 가지다. 참가자 화면(추천 목록, 입장, 안내)은 540px, 관리 화면은 760px, 첫 화면은 1120px.

추천 목록은 명찰을 14px 간격으로 한 줄씩 쌓는다. 상단 바는 테이블색 바탕으로 `position: sticky` 고정되고, 음수 여백으로 페이지 여백까지 채운다. 필터 칩 줄은 가로로 스크롤되며 화면 끝까지 이어진다. 알림(toast)은 화면 아래 12px 위에 고정되고 최대 520px이다. 390px 휴대폰 첫 화면에는 상단 바, 필터, 그리고 첫 명찰의 머리띠부터 52px 만나고 싶어요 버튼까지가 들어온다.

간격은 8px(요소 사이), 12~14px(패널 안쪽, 목록 간격), 16px(페이지 여백, 섹션 간격), 18~20px(명찰·시트 안쪽), 36px(첫 화면 큰 구획)의 리듬을 쓴다. 터치 영역은 버튼 48px, 만나고 싶어요 52px, 칩과 작은 버튼 40px, 내 명찰 버튼과 소개 더 보기 44px 이상이다.

넓은 화면에서의 변화:
- **760px 이상**: 관리 화면은 QR 시트와 현황이 0.9 : 1.1 두 열.
- **960px 이상**: 첫 화면의 세 구획(첫 화면, 이렇게 연결돼요, 행사 방 만들기)이 같은 1 : 0.92 두 열(56px 간격)을 쓴다. 왼쪽은 글, 오른쪽은 예시 명찰·영상·방 만들기 시트. 예시 명찰은 한 줄로 쌓아 내 명찰 → 추천 두 장 → 서로 연결과 전자 명함 순서로 읽힌다. 화면 높이가 760px 이상이면 첫 화면 글(제목, 소개, 방 만들기, 참가 코드)이 `position: sticky`로 예시 명찰을 따라 내려온다. 구획 사이는 112px(좁은 화면 72px). 제목은 52px.
- **프로젝터**: 뷰포트 전체를 1.1 : 0.9 두 열(간격 6vw, 안쪽 6vh 6vw)로 쓰고, 759px 이하에서는 한 열로 접는다. QR 명찰은 min(38vw, 72vh)까지 커진다.

## Elevation & Depth

그림자로 띄우지 않는다. 깊이는 검정 테이블(#131313)과 흰 용지(#ffffff)의 명도 대비로만 나온다. 테이블 위에서는 table-raised(#1f1f1f)가 컨트롤을 한 단 올려 주고, 용지 위에서는 stock-2(#f0f0ec)가 첫마디 패널과 명찰 뒷면을 한 단 내려 준다. `box-shadow`는 아래 네 가지에만 쓴다. 모두 번짐이 없는 선이다.

### Shadow Vocabulary
- **두 겹 포커스 링** (`outline: 2px solid var(--ink); box-shadow: 0 0 0 5px var(--stock)`): 모든 `:focus-visible`. 안쪽 잉크와 바깥 흰 용지가 검정 테이블 위에서도 흰 용지 위에서도 보인다.
- **입력칸 포커스** (`border-color: var(--ink); box-shadow: 0 0 0 3px rgba(17, 17, 17, 0.16)`): 용지 위 입력칸. 테이블 위 입력칸은 on-table 테두리와 `rgba(243, 243, 240, 0.22)` 링.
- **안쪽 테두리** (`box-shadow: inset 0 0 0 1.5px currentColor`): 지우기 버튼의 선. 포커스 때도 이 선을 유지한 채 5px 흰 링을 더한다.
- **알림 떼어 놓기** (`box-shadow: 0 0 0 2px var(--table)`): 흰 알림이 흰 명찰 위에 떠도 경계가 보이게 하는 테이블색 링.

### Named Rules
**The No Drop Shadow Rule.** 번지는 그림자, 글로우, 오프셋 그림자를 쓰지 않는다. 한 면을 앞으로 보이게 하려면 테이블 대 용지의 명도 차이를 쓴다.

## Shapes

모서리는 명찰 카드처럼 둥글되 부드럽지는 않다. 명찰, 시트, 테이블 위 영역, 빈 목록은 14px(`--radius`), 입력칸·첫마디 패널·상태 줄·알림·내 명찰 버튼은 10px(`--radius-sm`), 버튼·두 가지 질문 칸·알림(toast)은 12px, 필터 칩만 완전한 알약형(999px)이다.

명찰은 `overflow: hidden`으로 머리띠와 뒷면을 모서리 안에 가둔다. 테두리 선은 테이블 위에서만 쓴다(1px table-line, 빈 목록은 1.5px 점선). 용지 위 입력칸은 1.5px stock-line 테두리다. 명찰 뒷면은 2px 점선(stock-line) 절취선으로 앞면과 나뉜다.

반복되는 실루엣은 **펀칭 슬롯**이다. 명찰 머리띠 가운데 위쪽에 가로로 긴 둥근 구멍(44×10px, 반경 5px)이 테이블색으로 뚫려 있어, 목걸이에 거는 명찰처럼 보인다. 같은 모양이 크기만 바뀌어 워드마크(12×16px 명찰), 내 명찰 버튼(18×4px), 범례 견본(26×8px), 프로젝터 QR 명찰(clamp로 확대)에 반복된다. 워드마크와 내 명찰 버튼의 띠는 하드 스톱 `linear-gradient`로 그린다.

### Named Rules
**The Punched Slot Rule.** 명찰 형식을 쓰는 곳에는 반드시 머리띠와 가운데 슬롯이 함께 있다. 슬롯은 언제나 테이블색(#131313)이고, 띠 위 글자는 왼쪽에 둔다.

## Components

### Buttons
단단하고 인쇄물 같은 버튼. 글자는 800 굵기이고 색 장식이 없다.
- **Shape:** 조금 둥근 모서리(12px), 높이 48px, 좌우 18px 안쪽. 작은 버튼은 40px, 14px 글자.
- **Primary:** 잉크 바탕에 흰 글자. hover는 #2b2b2b.
- **Secondary:** 용지 위에서는 stock-2 바탕에 잉크 글자(hover #e3e3de). 테이블 위 영역 안에서는 #2b2b29 바탕에 on-table 글자(hover #363634).
- **Ghost:** 투명 바탕, 글자색 상속, hover에 옅은 회색 막(rgba(127, 127, 120, 0.14)).
- **Danger:** 투명 바탕에 1.5px 안쪽 선. 용지 위에서는 danger 빨강, 테이블 위에서는 on-table 글자와 #4d4d4a 선.
- **Hover / Focus / Active:** 배경과 글자색은 0.18s `--ease`(cubic-bezier(0.2, 0.7, 0.2, 1))로 바뀌고, 누르면 1px 내려간다(0.12s). 포커스는 두 겹 링. 처리 중에는 불투명도 0.55에 `cursor: progress`.

### Chips
- **Style:** 테이블 위 필터 탭. table-raised 바탕, on-table 글자(15px/700), 40px 높이, 알약형. 관계 필터에는 10×10px(반경 3px) 머리띠색 네모가 앞에 붙는다. 전체·연결됨 칩은 개수를 고정폭 숫자, 불투명도 0.6으로 보여 준다.
- **State:** hover는 #2a2a28. 선택된 칩은 흰 용지 바탕에 잉크 글자로 뒤집힌다. `role="tab"`과 `aria-selected`로 상태를 알린다.

### Cards / Containers
- **명찰(badge, person):** 흰 용지, 14px 모서리, 머리띠 + 본문(안쪽 18px) + 행동 영역(12px 18px 18px). 아래 Signature 참조.
- **시트(sheet):** 양식과 QR을 담는 흰 용지. 14px 모서리, 안쪽 22px 20px. 관리 화면의 시트는 머리에 회색 머리띠("주최자 전용", "참가 QR")를 달아 명찰 형식을 이어 간다.
- **테이블 위 영역(desk):** 채우지 않은 영역. 1px table-line 테두리, 14px 모서리, 안쪽 20px. 코드 입장, 현황, 방 관리, 이 방에서 나가기처럼 부차적인 작업을 담는다.
- **Shadow Strategy:** 없음. Elevation & Depth 참조.

### Inputs / Fields
- **Style:** 흰 용지 바탕, 1.5px stock-line 테두리, 10px 모서리, 높이 48px, 안쪽 12px 14px, 16px 글자(휴대폰 확대 방지). 여러 줄 입력칸은 최소 88px, 세로로만 늘어난다. 라벨은 14px/800 잉크, "선택"·"모두에게 보여요" 같은 보조 표시는 13px/600 ink-3.
- **Hover:** 테두리 #b9b9b2.
- **Focus:** 테두리가 잉크로 바뀌고 3px 옅은 잉크 링이 둘린다.
- **Read-only:** stock-2 바탕에 ink-2 글자(관리 주소, 참가 주소 복사 칸).
- **테이블 위:** table-raised 바탕, table-line 테두리, on-table 글자. 포커스는 on-table 테두리와 흰 링.
- **두 가지 질문(ask):** 같은 분야는 노랑, 다른 분야는 보라 머리(10px 14px, 14px/800)를 단 stock-2 칸. 칸 안 입력칸은 테두리 없이 이어지고, 포커스 때 안쪽 2px 잉크 선이 생긴다. 명찰 머리띠와 같은 색이라 적는 내용이 어느 추천으로 이어지는지 보인다.
- **Error:** 양식 위 알림(alert). danger-wash 바탕, danger-ink 글자, 14px/600, 10px 모서리.

### Navigation
- **상단 바:** 추천 목록의 고정 바. 테이블색 바탕 위 왼쪽에 워드마크(14px/800)와 방 이름(20px/800, 한 줄 말줄임), 오른쪽에 내 명찰 버튼.
- **내 명찰 버튼(me-chip):** 작은 명찰. 위쪽 8px 회색 띠와 18×4px 슬롯, 흰 용지, 14px/800 잉크 글자, 44px 높이. hover는 용지만 #ecece7로 바뀐다.
- **워드마크(brand):** 12×16px 명찰 모양(노란 5px 띠와 슬롯) 옆 "Meetpoint" 14px/800. 모든 페이지 맨 위에 하나 있고, 제목 위에 놓이는 라벨은 이것뿐이다.
- **필터:** Chips 참조.

### 명찰 (Signature)
이 세계의 중심 컴포넌트. 한 사람을 명찰 한 장으로 보여 준다.
- **머리띠(band):** 높이 40px, 좌우 16px, 13px/800 관계 이름을 왼쪽에 두고 가운데 위에 슬롯이 뚫린다. 관계에 따라 같은 분야 고수(노랑), 다른 분야 도움(보라, 흰 글자), 서로 연결(주홍), 참가자(회색), 분석 중(회색, ink-2 글자). 내가 만나고 싶어요를 보냈으면 오른쪽에 체크 아이콘(15px, 선 2.4)과 "보냄"이 붙는다.
- **본문 순서:** 이름(34px/800), 직함 · 회사(16px/700 잉크, 둘 다 비면 없음), 한 줄 소개(15px/600 ink-2), 추천 이유(17px/700), 첫마디 패널(stock-2, 10px 모서리, 12px 캡션 + 따옴표로 감싼 15px 문장), 위치 아이콘이 달린 찾는 법(15px, 장소는 800 잉크), 소개 더 보기(44px 요약 줄, CSS로 그린 꺾쇠가 열리면 돌아간다).
- **행동:** 전체 폭 52px 만나고 싶어요 버튼. 보낸 뒤에는 stock-2 바탕으로 가라앉고("만나고 싶어요 보냄 · 누르면 취소"), 서로 연결되면 주홍 바탕("서로 만나고 싶어해요")이 된다. `aria-pressed`로 상태를 알린다.
- **뒷면(badge-back):** 서로 연결된 명찰에만 붙는다. 2px 점선 절취선 아래 stock-2 바탕에 전자 명함 한 장과 전체 폭 "연락처에 저장" 잉크 버튼(vCard 내려받기). 연락처를 하나도 안 적은 사람은 명함 대신 "연락처는 적지 않았어요" 안내 한 줄.
- **전자 명함(ecard):** 흰 용지, 12px 모서리, 1px stock-line 윤곽과 위쪽 4px 주홍 띠(둘 다 번지지 않는 inset 그림자). 이름 22px/800, 직함 · 회사 15px/700, 한 줄 소개 14px/600 ink-2, 그 아래 12px 띄워 아이콘(전화, 메일, 링크)이 달린 연락처 줄(15px/700, 30px 높이). 전화는 `tel:`, 메일은 `mailto:` 링크다. 오른쪽 아래에 11px/800 ink-3 "Meetpoint".
- **뒤집기:** 새로 연결된 명찰은 `badge-turn`(0.34s, perspective(1100px) rotateY(90deg)에서 0으로) 한 번 돌고, 0.3s 뒤 뒷면이 `back-open`(0.3s, 위쪽을 축으로 rotateX(-90deg)에서 펼침)으로 내려온다. 처음 불러온 목록에는 일어나지 않고, 불러온 뒤 새로 연결된 명찰에만 일어난다. 명찰은 알림에 가리지 않게 화면 안으로 스크롤된다.
- **불러오는 중:** 머리띠와 글줄이 옅은 회색 막대(#e8e8e4, #ecece8)인 빈 명찰 두 장.
- **미리보기:** 입장 양식 위에서 적는 대로 이름, 직함 · 회사, 한 줄 소개, 찾는 법이 채워지는 회색 머리띠 명찰(이름 30px). 비어 있는 칸은 흐린 글자로 "이름", "한 줄 소개"를 보여 준다. 양식의 전자 명함 칸 아래에는 같은 방식으로 채워지는 전자 명함 미리보기(위쪽 띠 회색)가 "서로 연결되면 상대에게 이렇게 보여요" 아래에 놓인다. 회사와 직함 칸은 한 줄에 반씩 나란히 둔다.

### 알림과 상태
- **알림(toast):** 화면 아래 고정, 흰 용지, 12px 모서리, 안쪽 14px 16px, 제목 16px/800 + 본문 15px. 서로 연결 알림은 주홍 바탕이고 8초, 나머지는 4초 머문다. 0.24s 동안 12px 아래에서 올라온다.
- **상태 줄(status):** 상단 바 아래 table-raised 줄(14px/600). 추천 계산 중이거나 입장이 마감됐을 때만 보인다. 앞에 8px 점이 깜박인다.
- **빈 목록(empty):** 1.5px 점선 table-line 테두리, 14px 모서리, 가운데 정렬 15px on-table-2 문장.

### 관리 화면 통계와 프로젝터
- **통계:** 위아래 1px 선과 칸 사이 세로선으로 나눈 세 칸. 13px/700 라벨 아래 36px/800 고정폭 숫자.
- **최근 들어온 사람:** 1px 선으로 나눈 줄 목록. 이름 16px/800, 소개 14px on-table-2 한 줄 말줄임.
- **프로젝터:** 왼쪽에 워드마크, 행사 이름, 안내 문장, 참가 코드와 참가 인원(프로젝터 숫자). 오른쪽에 회색 머리띠("참가 QR")를 단 큰 QR 명찰. 인원이 바뀌면 숫자가 0.24s 동안 위에서 내려온다(`tick`).

### 아이콘
`base.html`에 심은 SVG `<symbol>`(위치 핀 `i-pin`, 체크 `i-check`, 전화 `i-phone`, 메일 `i-mail`, 링크 `i-link`)을 `<use>`로 가져온다. 18px, 채움 없음, 선 1.8, 둥근 끝. 새 아이콘도 같은 선 굵기와 24px 뷰박스로 그려 이 목록에 더한다.

## Do's and Don'ts

### Do:
- **Do** 한 사람은 명찰 한 장으로 보여 준다: 흰 용지(stock), 14px 모서리, 40px 머리띠와 가운데 슬롯, 34px/800 이름.
- **Do** 관계는 명찰 머리 전체 폭의 띠 색으로 알린다. 보라 띠에만 흰 글자를 올리고, 노랑·주홍·회색 띠에는 잉크 글자를 올린다.
- **Do** 주 행동은 잉크 버튼 하나로 둔다. 높이는 48px 이상, 만나고 싶어요는 52px 전체 폭이다.
- **Do** 테이블 위 영역은 채우지 않고 1px table-line 선으로만 두른다. 컨트롤만 table-raised로 한 단 올린다.
- **Do** 포커스는 두 겹 링(2px 잉크 outline + 5px 흰 링)으로 둔다. 자체 안쪽 선이 있는 버튼도 흰 바깥 링을 유지한다.
- **Do** 상태 전환은 0.15~0.18s, `--ease`(cubic-bezier(0.2, 0.7, 0.2, 1))로 짧게 한다. 뒤집기는 서로 연결되는 순간에만 쓰고, `prefers-reduced-motion: reduce`에서는 모든 애니메이션과 전환을 끈다.
- **Do** 바뀌는 숫자와 참가 코드는 tabular-nums로 자리를 고정한다.

### Don't:
- **Don't** 머리띠 4색(same, other, match, attendee)을 링크, 아이콘, 장식 배경, 일반 버튼에 쓰지 않는다. 명찰 모양 워드마크의 노란 띠만 예외다.
- **Don't** 흰 카드에 파란 버튼, 작은 파스텔 태그를 단 SaaS 목록으로 사람을 보여 주지 않는다.
- **Don't** 번지는 그림자, 글로우, 오프셋 그림자, 부드러운 그라데이션 면을 쓰지 않는다. 띠를 그리는 하드 스톱 `linear-gradient`만 쓴다.
- **Don't** Wanted Sans 말고 다른 글꼴 가족이나 시스템 디스플레이 서체를 제목에 쓰지 않는다.
- **Don't** 제목 위에 작은 분류 라벨(키커, 아이브로)을 달지 않는다. 제목 위에는 워드마크만 온다.
- **Don't** 유니코드 글리프나 이모지를 아이콘 대신 쓰지 않는다. 아이콘은 base.html의 SVG 심볼로 그린다.
- **Don't** 경고 빨강(danger)을 검정 테이블 위 글자로 쓰지 않는다(대비 3.3:1). 테이블 위 지우기 버튼은 on-table 글자와 선으로 둔다.
