"""AI를 쓸 수 없을 때의 키워드 기반 추천.

한국어는 조사가 붙어 형태가 바뀌므로("마케팅을", "마케팅") 한글 단어는 두 글자 조각으로 비교한다.
"""

import re

from .schemas import PairResult, Profile

_WORD = re.compile(r"[0-9A-Za-z가-힣+#.]+")
_HANGUL = re.compile(r"[가-힣]")

# 어느 문장에나 나오는 조각은 연결점으로 치지 않는다.
_STOP_GRAMS = {
    "어요", "니다", "습니", "해요", "있는", "하는", "싶어", "싶습", "싶은", "사람", "에서", "으로",
    "하고", "관련", "경험", "에요", "이에", "입니", "합니", "대해", "같은", "분야", "어떻", "방법",
    "궁금", "알고", "있어", "없어", "까요", "려고", "필요", "도움", "받고", "주실", "는데", "에게",
    "한테", "지금", "요즘", "하게", "해서", "해본", "하면", "되는", "이야", "야기", "이랑", "랑요",
    "그리", "리고", "저는", "제가", "하기", "하는", "만들", "들고", "들어", "보고", "보는", "좋은",
    "잘하", "하시", "시는", "분께", "분을", "분이", "분과", "들이", "들을", "것을", "것이",
}
_STOP_WORDS = {"the", "and", "for", "with", "i", "a", "to", "of", "in", "on", "is", "at"}


def _grams(word: str) -> set[str]:
    if _HANGUL.search(word):
        if len(word) < 2:
            return set()
        grams = {word[i : i + 2] for i in range(len(word) - 1)}
        return {g for g in grams if g not in _STOP_GRAMS}
    if len(word) < 2 or word in _STOP_WORDS:
        return set()
    return {word}


def _words(text: str) -> list[str]:
    return [w.strip(".") for w in _WORD.findall(text.lower()) if w.strip(".")]


def _gram_set(text: str) -> set[str]:
    out: set[str] = set()
    for word in _words(text):
        out |= _grams(word)
    return out


def _overlap(query: str, doc: str) -> tuple[int, str]:
    """겹치는 조각 수와, 상대 글에서 질문과 가장 많이 겹치는 단어."""
    q = _gram_set(query)
    if not q:
        return 0, ""
    best_word, best_hits = "", 0
    shared: set[str] = set()
    for word in _words(doc):
        hits = _grams(word) & q
        if not hits:
            continue
        shared |= hits
        if len(hits) > best_hits or (len(hits) == best_hits and len(word) > len(best_word)):
            best_word, best_hits = word, len(hits)
    return len(shared), _strip_particle(best_word)


_PARTICLES = ("에서는", "으로는", "에서", "으로", "이랑", "에게", "한테", "까지", "부터", "은", "는", "이", "가", "을", "를", "과", "와", "도", "로", "에", "의")


def _strip_particle(word: str) -> str:
    for p in _PARTICLES:
        if len(word) > len(p) + 1 and word.endswith(p):
            return word[: -len(p)]
    return word


def _profile_text(p: Profile) -> str:
    return f"{p.job_title} {p.company} {p.headline} {p.about}"


def score_pair(viewer: Profile, target: Profile) -> PairResult:
    target_text = _profile_text(target)
    same_hits, same_word = _overlap(viewer.ask_same, target_text)
    field_hits, field_word = _overlap(_profile_text(viewer), target_text)
    other_hits, other_word = _overlap(viewer.ask_other, target_text)
    reverse_hits, _ = _overlap(f"{target.ask_same} {target.ask_other}", _profile_text(viewer))

    common = 2 * same_hits + field_hits if (same_hits or field_hits) else 0
    complement = 2 * other_hits
    mutual_bonus = min(20, 8 * reverse_hits)

    if common == 0 and complement == 0:
        return PairResult(
            kind="none",
            score=min(20, mutual_bonus),
            reason="",
            opener="",
            source="heuristic",
        )

    if complement > common:
        word = other_word
        score = min(95, 30 + 15 * complement + mutual_bonus)
        return PairResult(
            kind="complement",
            score=score,
            reason=f"{target.name}님 소개에 ‘{word}’ 이야기가 있어요. 내가 다른 분야에서 필요하다고 적은 부분과 연결돼요.",
            opener=f"안녕하세요 {target.name}님, ‘{word}’ 쪽 경험이 있으시다고 봐서 잠깐 여쭤보고 싶었어요.",
            source="heuristic",
        )

    word = same_word or field_word
    score = min(95, 25 + 12 * common + mutual_bonus)
    return PairResult(
        kind="common",
        score=score,
        reason=f"{target.name}님도 ‘{word}’ 쪽 이야기를 적었어요. 같은 분야에서 궁금한 점을 물어보기 좋아요.",
        opener=f"안녕하세요 {target.name}님, 저도 ‘{word}’ 쪽 일을 하고 있어서 말 걸어봤어요.",
        source="heuristic",
    )
