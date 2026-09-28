(() => {
  const code = document.getElementById("screen").dataset.code;
  const countEl = document.getElementById("screen-count");
  async function tick() {
    try {
      const res = await fetch(`/s/${code}/count`, { cache: "no-store" });
      if (res.ok) countEl.textContent = String((await res.json()).count);
    } catch {}
  }
  setInterval(tick, 5000);
})();
