from __future__ import annotations

import json
import os
from typing import Any, Iterable, Iterator, List, Optional, Union

import httpx

from nevara.errors import NevaraAPIError
from nevara.models import (
    AssistantMessage,
    AssistantRun,
    AssistantSession,
    AssistantTurn,
    JSONDict,
    StreamEvent,
)

DEFAULT_ASSISTANT = "nevara/default"
MessageInput = Union[str, JSONDict]


class Nevara:
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = "https://app.nevara.ai/api/v1",
        timeout: float = 60.0,
    ) -> None:
        key = api_key or os.getenv("NEVARA_API_KEY")
        if not key:
            raise ValueError("api_key is required, or set NEVARA_API_KEY")

        self._http = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={
                "X-API-Key": key,
                "User-Agent": "nevara-python/0.1.0",
            },
        )
        self.assistant = DefaultAssistantResource(self)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "Nevara":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self._http.request(method, path, **kwargs)
        if response.status_code >= 400:
            raise _api_error(response)
        if not response.content:
            return None
        return response.json()

    def _stream(self, method: str, path: str, **kwargs: Any) -> Iterator[StreamEvent]:
        with self._http.stream(method, path, **kwargs) as response:
            if response.status_code >= 400:
                body = response.read().decode("utf-8", errors="replace")
                raise NevaraAPIError(response.status_code, response.reason_phrase, body)
            yield from _parse_sse(response.iter_lines())


class DefaultAssistantResource:
    def __init__(self, client: Nevara) -> None:
        self._client = client

    def create_session(
        self,
        *,
        title: Optional[str] = None,
        actor: Optional[JSONDict] = None,
        context: Optional[JSONDict] = None,
        metadata: Optional[JSONDict] = None,
    ) -> AssistantSession:
        payload: JSONDict = {}
        if title is not None:
            payload["title"] = title
        if actor is not None:
            payload["actor"] = actor
        if context is not None:
            payload["context"] = context
        if metadata is not None:
            payload["metadata"] = metadata

        data = self._client._request("POST", "/assistants/nevara/default/sessions", json=payload)
        return _parse_session(data)

    def get_session(self, session_id: str) -> AssistantSession:
        data = self._client._request("GET", f"/assistant/sessions/{session_id}")
        return _parse_session(data)

    def list_messages(self, session_id: str) -> List[AssistantMessage]:
        data = self._client._request("GET", f"/assistant/sessions/{session_id}/messages")
        return [_parse_message(item) for item in data.get("messages", [])]

    def run(
        self,
        session_id: str,
        messages: Union[MessageInput, Iterable[MessageInput]],
        *,
        mode: str = "sync",
    ) -> AssistantTurn:
        if mode == "stream":
            raise ValueError("Use assistant.stream(...) for streaming turns")
        data = self._client._request(
            "POST",
            f"/assistant/sessions/{session_id}/turns",
            json={"mode": mode, "messages": _message_payloads(messages)},
        )
        return _parse_turn(data)

    def stream(
        self,
        session_id: str,
        messages: Union[MessageInput, Iterable[MessageInput]],
    ) -> Iterator[StreamEvent]:
        return self._client._stream(
            "POST",
            f"/assistant/sessions/{session_id}/turns",
            json={"mode": "stream", "messages": _message_payloads(messages)},
        )

    def get_run(self, run_id: str) -> AssistantRun:
        data = self._client._request("GET", f"/assistant/runs/{run_id}")
        return _parse_run(data)

    def cancel_run(self, run_id: str) -> AssistantRun:
        data = self._client._request("POST", f"/assistant/runs/{run_id}/cancel")
        return _parse_run(data)


def _message_payloads(messages: Union[MessageInput, Iterable[MessageInput]]) -> List[JSONDict]:
    if isinstance(messages, (str, dict)):
        values: Iterable[MessageInput] = [messages]
    else:
        values = messages

    payloads: List[JSONDict] = []
    for message in values:
        if isinstance(message, str):
            payloads.append({"role": "user", "content": message})
        else:
            payloads.append(message)
    return payloads


def _parse_session(data: JSONDict) -> AssistantSession:
    return AssistantSession(
        id=str(data["id"]),
        assistant=data.get("assistant", {}),
        raw=data,
    )


def _parse_message(data: JSONDict) -> AssistantMessage:
    return AssistantMessage(
        id=str(data["id"]),
        session_id=str(data["session_id"]),
        role=str(data["role"]),
        content=str(data["content"]),
        raw=data,
    )


def _parse_run(data: JSONDict) -> AssistantRun:
    return AssistantRun(
        id=str(data["id"]),
        session_id=str(data["session_id"]),
        status=str(data["status"]),
        output=data.get("output"),
        raw=data,
    )


def _parse_turn(data: JSONDict) -> AssistantTurn:
    return AssistantTurn(
        run=_parse_run(data["run"]),
        accepted_message_ids=[str(item) for item in data.get("accepted_message_ids", [])],
        accepted_messages=[_parse_message(item) for item in data.get("accepted_messages", [])],
        output=data.get("output"),
        raw=data,
    )


def _parse_sse(lines: Iterable[str]) -> Iterator[StreamEvent]:
    event_type = "message"
    data_lines: List[str] = []

    for line in lines:
        if not line:
            if data_lines:
                yield StreamEvent(type=event_type, data=json.loads("\n".join(data_lines)))
            event_type = "message"
            data_lines = []
            continue
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            event_type = line.removeprefix("event:").strip()
        elif line.startswith("data:"):
            data_lines.append(line.removeprefix("data:").strip())

    if data_lines:
        yield StreamEvent(type=event_type, data=json.loads("\n".join(data_lines)))


def _api_error(response: httpx.Response) -> NevaraAPIError:
    try:
        body = response.json()
        message = body.get("error") or body.get("message") or response.reason_phrase
    except Exception:
        message = response.reason_phrase
    return NevaraAPIError(response.status_code, str(message), response.text)
