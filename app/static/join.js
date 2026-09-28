(() => {
  const code = document.currentScript.dataset.code;
  const input = document.getElementById("card-file");
  const status = document.getElementById("card-status");
  const wrap = document.getElementById("card-scan");
  const form = document.getElementById("profile-form");
  if (!input || !form) return;

  // 휴대폰 사진은 크다. 긴 변을 1568px로 줄여 JPEG로 보낸다.
  async function downscale(file, maxSide, quality) {
    let bitmap;
    try {
      bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
    } catch {
      return file;
    }
    const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height));
    const w = Math.round(bitmap.width * scale);
    const h = Math.round(bitmap.height * scale);
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    canvas.getContext("2d").drawImage(bitmap, 0, 0, w, h);
    return new Promise((resolve) => canvas.toBlob((b) => resolve(b || file), "image/jpeg", quality));
  }

  function fill(name, value) {
    const field = form.elements[name];
    if (!field || !value) return;
    if (!field.value.trim() || field.dataset.fromCard === "1") {
      field.value = value;
      field.dataset.fromCard = "1";
    }
  }

  input.addEventListener("change", async () => {
    const file = input.files && input.files[0];
    if (!file) return;
    wrap.classList.add("busy");
    status.textContent = "명함을 읽고 있어요…";
    try {
      const blob = await downscale(file, 1568, 0.85);
      const body = new FormData();
      body.append("file", blob, "card.jpg");
      const res = await fetch(`/r/${code}/card`, { method: "POST", body });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        status.textContent = data.error || "명함을 읽지 못했어요. 직접 적어주세요.";
        return;
      }
      fill("name", data.name);
      fill("headline", data.headline);
      fill("about", data.about);
      fill("contact", data.contact);
      status.textContent = "채웠어요. 내용을 확인하고 오늘 만나고 싶은 사람을 적어주세요.";
      form.elements.ask_same.focus();
    } catch {
      status.textContent = "명함을 읽지 못했어요. 직접 적어주세요.";
    } finally {
      wrap.classList.remove("busy");
      input.value = "";
    }
  });
})();
