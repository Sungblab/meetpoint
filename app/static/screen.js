(() => {
  const code = document.getElementById("screen").dataset.code;
  const countEl = document.getElementById("screen-count");
  async function tick() {
    try {
      const res = await fetch(`/s/${code}/count`, { cache: "no-store" });
      if (!res.ok) return;
      const next = String((await res.json()).count);
      if (next === countEl.textContent) return;
      countEl.textContent = next;
      // 숫자가 바뀌는 순간을 한 번 보여준다.
      countEl.classList.remove("tick");
      void countEl.offsetWidth;
      countEl.classList.add("tick");
    } catch {}
  }
  setInterval(tick, 5000);
})();
