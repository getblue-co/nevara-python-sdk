from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

JSONDict = Dict[str, Any]


@dataclass(frozen=True)
class AssistantSession:
    id: str
    assistant: JSONDict
    raw: JSONDict = field(repr=False)


@dataclass(frozen=True)
class AssistantMessage:
    id: str
    session_id: str
    role: str
    content: str
    raw: JSONDict = field(repr=False)


@dataclass(frozen=True)
class AssistantRun:
    id: str
    session_id: str
    status: str
    output: Optional[JSONDict]
    raw: JSONDict = field(repr=False)


@dataclass(frozen=True)
class AssistantTurn:
    run: AssistantRun
    accepted_message_ids: List[str]
    accepted_messages: List[AssistantMessage]
    output: Optional[JSONDict]
    raw: JSONDict = field(repr=False)


@dataclass(frozen=True)
class StreamEvent:
    type: str
    data: JSONDict
