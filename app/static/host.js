(() => {
  const el = window.el;
  const root = document.getElementById("host");
  const base = `/h/${root.dataset.token}`;
  const list = document.getElementById("people-mini");

  async function load() {
    const res = await fetch(`${base}/api/stats`, { cache: "no-store" });
    if (!res.ok) return;
    const s = await res.json();
    document.getElementById("stat-participants").textContent = String(s.participants);
    document.getElementById("stat-matches").textContent = String(s.matches);
    document.getElementById("stat-pending").textContent = String(s.pending);
    list.replaceChildren(
      ...(s.people.length
        ? s.people.slice(0, 50).map((p) =>
            el("li", {}, el("strong", { text: p.name }), p.headline ? el("span", { class: "sub", text: ` · ${p.headline}` }) : null),
          )
        : [el("li", { class: "muted", text: "아직 없어요" })]),
    );
  }

  let timer = null;
  const schedule = () => {
    clearTimeout(timer);
    timer = setTimeout(() => load().catch(() => {}), 500);
  };

  for (const btn of document.querySelectorAll("[data-copy]")) {
    btn.addEventListener("click", async () => {
      const input = document.getElementById(btn.dataset.copy);
      try {
        await navigator.clipboard.writeText(input.value);
      } catch {
        input.select();
        document.execCommand("copy");
      }
      const old = btn.textContent;
      btn.textContent = "복사됨";
      setTimeout(() => (btn.textContent = old), 1500);
    });
  }

  if (window.EventSource) {
    const es = new EventSource(`${base}/events`);
    es.addEventListener("hello", schedule);
    es.addEventListener("refresh", schedule);
    es.addEventListener("stats", schedule);
    // 연결이 너무 많아 서버가 닫았다. 다시 붙지 않고 30초 새로고침으로 버틴다.
    es.addEventListener("closed", () => es.close());
  }
  setInterval(() => document.visibilityState === "visible" && schedule(), 30000);
  load().catch(() => {});
})();
