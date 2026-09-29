from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

Kind = Literal["common", "complement", "none"]
KINDS: tuple[str, ...] = ("common", "complement", "none")


@dataclass(frozen=True)
class Profile:
    id: int
    name: str
    headline: str
    about: str
    ask_same: str
    ask_other: str
    version: int = 1
    company: str = ""
    job_title: str = ""

    def as_prompt_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "company": self.company,
            "job_title": self.job_title,
            "headline": self.headline,
            "about": self.about,
            "ask_same": self.ask_same,
            "ask_other": self.ask_other,
        }


@dataclass(frozen=True)
class PairResult:
    """viewer 입장에서 본 target에 대한 추천."""

    kind: str
    score: int
    reason: str
    opener: str
    source: str


class DirectionOut(BaseModel):
    kind: Kind
    score: int
    reason: str
    opener: str


class CandidateOut(BaseModel):
    candidate_id: int
    for_new: DirectionOut
    for_candidate: DirectionOut


class RecommendationBatchOut(BaseModel):
    results: list[CandidateOut]


class CardOut(BaseModel):
    is_business_card: bool
    name: str
    company: str
    job_title: str
    headline: str
    about: str
    phone: str
    email: str
    contact: str


_DIRECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {"type": "string", "enum": list(KINDS)},
        "score": {"type": "integer"},
        "reason": {"type": "string"},
        "opener": {"type": "string"},
    },
    "required": ["kind", "score", "reason", "opener"],
    "additionalProperties": False,
}

RECOMMENDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "candidate_id": {"type": "integer"},
                    "for_new": _DIRECTION_SCHEMA,
                    "for_candidate": _DIRECTION_SCHEMA,
                },
                "required": ["candidate_id", "for_new", "for_candidate"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}

CARD_SCHEMA = {
    "type": "object",
    "properties": {
        "is_business_card": {"type": "boolean"},
        "name": {"type": "string"},
        "company": {"type": "string"},
        "job_title": {"type": "string"},
        "headline": {"type": "string"},
        "about": {"type": "string"},
        "phone": {"type": "string"},
        "email": {"type": "string"},
        "contact": {"type": "string"},
    },
    "required": ["is_business_card", "name", "company", "job_title", "headline", "about", "phone", "email", "contact"],
    "additionalProperties": False,
}


def clamp_score(value: int) -> int:
    return max(0, min(100, int(value)))
