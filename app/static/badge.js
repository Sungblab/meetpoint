// 입장 양식을 적는 동안 위쪽 명찰과 아래 전자 명함 미리보기를 채운다. textContent만 쓴다.
(() => {
  const form = document.getElementById("profile-form");
  if (!form) return;
  const value = (name) => (form.elements[name]?.value || "").trim();

  function sync() {
    for (const node of document.querySelectorAll("[data-preview]")) {
      const v = value(node.dataset.preview);
      node.textContent = v || node.dataset.blank || "";
      node.classList.toggle("is-blank", !v);
    }
    for (const wrap of document.querySelectorAll("[data-preview-wrap]")) {
      wrap.hidden = !value(wrap.dataset.previewWrap);
    }
  }

  form.addEventListener("input", sync);
  sync();
})();
