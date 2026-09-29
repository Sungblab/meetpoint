(() => {
  const el = window.el;
  const icon = window.icon;
  const glue = window.glue;
  const app = document.getElementById("app");
  const base = `/r/${app.dataset.code}`;
  const listEl = document.getElementById("list");
  const statusEl = document.getElementById("status");
  const toastsEl = document.getElementById("toasts");
  const KIND_LABEL = { common: "같은 분야 고수", complement: "다른 분야 도움" };
  const EMPTY = {
    all: "아직 다른 참가자가 없어요. 사람들이 들어오면 여기에 바로 보여요.",
    common: "같은 분야에서 연결되는 사람이 아직 없어요.",
    complement: "다른 분야에서 연결되는 사람이 아직 없어요.",
    matched: "아직 서로 연결된 사람이 없어요. 마음에 드는 사람에게 ‘만나고 싶어요’를 눌러보세요.",
  };

  let state = null;
  let filter = "all";
  const expanded = new Set();
  // 처음 불러온 뒤 새로 연결된 명찰만 뒤집는다.
  let matchedSeen = null;

  async function load() {
    const res = await fetch(`${base}/api/state`, { credentials: "same-origin", cache: "no-store" });
    if (res.status === 401) {
      location.reload();
      return;
    }
    if (!res.ok) throw new Error(String(res.status));
    state = await res.json();
    render();
  }

  let loadTimer = null;
  function scheduleLoad(delay = 400) {
    clearTimeout(loadTimer);
    loadTimer = setTimeout(() => load().catch(() => {}), delay);
  }

  function visible(p) {
    if (filter === "matched") return p.matched;
    if (filter === "common" || filter === "complement") return Boolean(p.rec && p.rec.kind === filter);
    return true;
  }

  function render() {
    const pending = state.me.recs_status === "pending";
    const messages = [];
    if (pending) messages.push("추천 이유를 만들고 있어요. 먼저 목록을 둘러보세요.");
    if (state.room.closed) messages.push("새 입장은 마감됐어요.");
    statusEl.hidden = messages.length === 0;
    statusEl.textContent = messages.join(" ");

    document.querySelector('[data-count="all"]').textContent = state.counts.people ? String(state.counts.people) : "";
    document.querySelector('[data-count="matched"]').textContent = state.counts.matches ? String(state.counts.matches) : "";

    const people = state.people.filter(visible);
    listEl.replaceChildren(...(people.length ? people.map(card) : [el("p", { class: "empty", text: EMPTY[filter] })]));
    listEl.removeAttribute("aria-busy");

    const matchedNow = new Set(state.people.filter((p) => p.matched).map((p) => p.id));
    if (matchedSeen) {
      for (const id of matchedNow) {
        const node = matchedSeen.has(id) ? null : listEl.querySelector(`[data-id="${id}"]`);
        if (!node) continue;
        node.classList.add("just-matched");
        // 뒷면이 펼쳐지는 자리가 아래 알림에 가리지 않게 명찰을 화면 안으로 올린다.
        const smooth = !matchMedia("(prefers-reduced-motion: reduce)").matches;
        node.scrollIntoView({ block: "nearest", behavior: smooth ? "smooth" : "auto" });
      }
    }
    matchedSeen = matchedNow;
  }

  function field(label, value) {
    if (!value) return null;
    return [el("dt", { text: label }), el("dd", { text: glue(value) })];
  }

  // 명찰 머리띠: 관계 종류와 내 상태
  function band(p) {
    let kind = "none";
    let label = "참가자";
    if (p.matched) {
      kind = "matched";
      label = "서로 연결";
    } else if (p.rec && p.rec.kind !== "none") {
      kind = p.rec.kind;
      label = KIND_LABEL[p.rec.kind];
    } else if (p.pending) {
      kind = "pending";
      label = "분석 중";
    }
    const mark = p.liked && !p.matched ? el("span", { class: "band-state" }, icon("check"), "보냄") : null;
    return el("div", { class: `band band-${kind}` }, el("span", { text: label }), mark);
  }

  function card(p) {
    const rec = p.rec;
    const details = el(
      "details",
      { class: "details", open: expanded.has(p.id) },
      el("summary", { text: "소개 더 보기" }),
      el(
        "dl",
        {},
        field("자기소개", p.about),
        field("같은 분야에 묻고 싶은 것", p.ask_same),
        field("다른 분야에서 필요한 것", p.ask_other),
      ),
    );
    details.addEventListener("toggle", () => (details.open ? expanded.add(p.id) : expanded.delete(p.id)));

    return el(
      "article",
      { class: `person${p.matched ? " matched" : ""}`, "data-id": p.id },
      band(p),
      el(
        "div",
        { class: "person-body" },
        el("h2", { class: "person-name", text: p.name }),
        p.headline ? el("p", { class: "person-headline", text: glue(p.headline) }) : null,
        rec && rec.reason ? el("p", { class: "reason", text: glue(rec.reason) }) : null,
        rec && rec.opener
          ? el(
              "p",
              { class: "opener" },
              el("span", { class: "opener-label", text: "이렇게 말을 걸어보세요" }),
              el("span", { class: "opener-text", text: glue(rec.opener) }),
            )
          : null,
        p.find_me ? el("p", { class: "find-me" }, icon("pin"), el("span", {}, "찾는 법 ", el("strong", { text: glue(p.find_me) }))) : null,
        details,
      ),
      ...actions(p),
    );
  }

  function actions(p) {
    let label = "만나고 싶어요";
    let cls = "primary";
    if (p.matched) {
      label = "서로 만나고 싶어해요";
      cls = "matched";
    } else if (p.liked) {
      label = "만나고 싶어요 보냄 · 누르면 취소";
      cls = "liked";
    }
    const btn = el("button", { class: `btn like-btn ${cls}`, type: "button", "aria-pressed": p.liked ? "true" : "false" }, label);
    btn.addEventListener("click", () => toggleLike(p, btn));
    const parts = [el("div", { class: "person-actions" }, btn)];
    if (p.matched) parts.push(ecard(p));
    return parts;
  }

  // 명찰 뒷면의 전자 명함. 서로 연결된 사람에게만 서버가 연락처를 보낸다.
  function ecard(p) {
    const lines = [
      p.phone && el("a", { class: "ecard-line", href: `tel:${p.phone.replace(/[^0-9+]/g, "")}` }, icon("phone"), el("span", { text: p.phone })),
      p.email && el("a", { class: "ecard-line", href: `mailto:${p.email}` }, icon("mail"), el("span", { text: p.email })),
      p.contact && el("p", { class: "ecard-line" }, icon("link"), el("span", { text: p.contact })),
    ].filter(Boolean);
    if (!lines.length) {
      return el("div", { class: "badge-back" }, el("p", { class: "note", text: "연락처는 적지 않았어요. 찾는 법을 보고 직접 찾아가 보세요." }));
    }
    return el(
      "div",
      { class: "badge-back" },
      el(
        "div",
        { class: "ecard" },
        el("p", { class: "ecard-name", text: p.name }),
        p.headline ? el("p", { class: "ecard-headline", text: glue(p.headline) }) : null,
        el("div", { class: "ecard-lines" }, lines),
        el("span", { class: "ecard-brand", text: "Meetpoint" }),
      ),
      el("a", { class: "btn primary block ecard-save", href: `${base}/api/vcard/${p.id}` }, "연락처에 저장"),
    );
  }

  async function toggleLike(p, btn) {
    const want = !p.liked;
    if (!want && p.matched && !confirm(`${p.name}님과의 연결을 취소할까요?`)) return;
    btn.disabled = true;
    try {
      const res = await fetch(`${base}/api/like/${p.id}`, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ liked: want }),
      });
      if (!res.ok) throw new Error(String(res.status));
      const data = await res.json();
      if (data.matched) {
        toast(`${data.name}님도 만나고 싶어해요`, "찾는 법과 연락처를 확인해 보세요.", "match");
        if (navigator.vibrate) navigator.vibrate(150);
      } else if (want) {
        toast("만나고 싶어요를 보냈어요", `${p.name}님도 누르면 서로에게 알려드려요.`);
      }
      await load();
    } catch {
      btn.disabled = false;
      toast("연결이 잠시 불안정해요", "다시 눌러주세요.");
    }
  }

  function toast(title, body, kind = "") {
    const node = el("div", { class: `toast ${kind}`, role: "status" }, el("strong", { text: title }), body);
    toastsEl.append(node);
    setTimeout(() => node.remove(), kind === "match" ? 8000 : 4000);
  }

  for (const chip of document.querySelectorAll(".chip")) {
    chip.addEventListener("click", () => {
      filter = chip.dataset.filter;
      for (const c of document.querySelectorAll(".chip")) {
        c.classList.toggle("active", c === chip);
        c.setAttribute("aria-selected", c === chip ? "true" : "false");
      }
      if (state) render();
    });
  }

  function connect() {
    if (!window.EventSource) return;
    const es = new EventSource(`${base}/api/events`);
    es.addEventListener("hello", () => scheduleLoad(0));
    es.addEventListener("refresh", () => scheduleLoad());
    es.addEventListener("match", (e) => {
      const data = JSON.parse(e.data || "{}");
      toast(`${data.name}님과 서로 연결됐어요`, "상대도 만나고 싶어해요. 찾는 법을 확인해 보세요.", "match");
      if (navigator.vibrate) navigator.vibrate(150);
      scheduleLoad(0);
    });
    es.addEventListener("gone", () => {
      es.close();
      location.reload();
    });
  }

  // 실시간 연결이 막힌 환경을 위한 보조 새로고침
  setInterval(() => {
    if (document.visibilityState === "visible") scheduleLoad(0);
  }, 30000);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") scheduleLoad(0);
  });

  load().catch(() => {
    listEl.replaceChildren(el("p", { class: "empty", text: "불러오지 못했어요. 새로고침해 주세요." }));
  });
  connect();
})();
