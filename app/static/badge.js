// 입장 양식을 적는 동안 위쪽 명찰 미리보기를 채운다. textContent만 쓴다.
(() => {
  const form = document.getElementById("profile-form");
  const preview = document.getElementById("badge-preview");
  if (!form || !preview) return;
  const findWrap = preview.querySelector('[data-preview-wrap="find_me"]');

  function sync() {
    for (const node of preview.querySelectorAll("[data-preview]")) {
      const value = (form.elements[node.dataset.preview]?.value || "").trim();
      node.textContent = value || node.dataset.blank || "";
      node.classList.toggle("is-blank", !value);
    }
    if (findWrap) findWrap.hidden = !(form.elements.find_me?.value || "").trim();
  }

  form.addEventListener("input", sync);
  sync();
})();
