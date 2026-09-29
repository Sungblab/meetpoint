// 사용자 입력은 textContent로만 넣는다. innerHTML을 쓰지 않는다.
window.el = function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value == null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value === true ? "" : String(value));
  }
  for (const child of children.flat(2)) {
    if (child == null || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
};

// 의존명사·호칭(준비 중, 할 수, 예린 님, 유의할 점)이 앞말과 떨어져 줄이 바뀌지 않게 붙인다.
// ponytail: 짧은 낱말 목록으로 어림한다. 틀려도 줄바꿈 자리 하나가 줄어들 뿐이다.
const GLUE = / ([수것중등때점님분뿐쯤번][가-힣]{0,2})(?![가-힣])/g;
window.glue = (text) => (text ? String(text).replace(GLUE, " $1") : text);

// base.html에 심어 둔 <symbol>을 가리키는 아이콘
window.icon = function icon(name) {
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("class", "icon");
  svg.setAttribute("aria-hidden", "true");
  const use = document.createElementNS(ns, "use");
  use.setAttribute("href", `#i-${name}`);
  svg.append(use);
  return svg;
};
