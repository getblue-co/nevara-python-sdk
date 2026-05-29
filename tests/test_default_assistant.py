import httpx
import respx

from nevara import Nevara


@respx.mock
def test_create_session_uses_default_assistant_endpoint():
    client = Nevara(api_key="test", base_url="https://example.test/api/v1")
    route = respx.post("https://example.test/api/v1/assistants/nevara/default/sessions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "session_1",
                "assistant": {"namespace": "nevara", "slug": "default", "version": 1},
            },
        )
    )

    session = client.assistant.create_session(title="Test")

    assert route.called
    assert route.calls.last.request.headers["X-API-Key"] == "test"
    assert route.calls.last.request.content == b'{"title":"Test"}'
    assert session.id == "session_1"


@respx.mock
def test_sync_run_parses_turn_response():
    client = Nevara(api_key="test", base_url="https://example.test/api/v1")
    respx.post("https://example.test/api/v1/assistant/sessions/session_1/turns").mock(
        return_value=httpx.Response(
            200,
            json={
                "run": {
                    "id": "run_1",
                    "session_id": "session_1",
                    "status": "completed",
                    "output": {"content": "Hello"},
                },
                "accepted_message_ids": ["message_1"],
                "accepted_messages": [
                    {
                        "id": "message_1",
                        "session_id": "session_1",
                        "role": "user",
                        "content": "Hi",
                    }
                ],
                "output": {"content": "Hello"},
            },
        )
    )

    turn = client.assistant.run("session_1", "Hi")

    assert turn.run.id == "run_1"
    assert turn.output == {"content": "Hello"}
    assert turn.accepted_messages[0].content == "Hi"


@respx.mock
def test_stream_run_parses_sse_events():
    client = Nevara(api_key="test", base_url="https://example.test/api/v1")
    respx.post("https://example.test/api/v1/assistant/sessions/session_1/turns").mock(
        return_value=httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            text='event: message.delta\ndata: {"delta":"Hi"}\n\n'
            'event: run.completed\ndata: {"status":"completed"}\n\n',
        )
    )

    events = list(client.assistant.stream("session_1", "Hi"))

    assert [event.type for event in events] == ["message.delta", "run.completed"]
    assert events[0].data == {"delta": "Hi"}


@respx.mock
def test_get_and_cancel_run():
    client = Nevara(api_key="test", base_url="https://example.test/api/v1")
    run_payload = {
        "id": "run_1",
        "session_id": "session_1",
        "status": "cancelled",
        "output": None,
    }
    respx.get("https://example.test/api/v1/assistant/runs/run_1").mock(
        return_value=httpx.Response(200, json=run_payload)
    )
    respx.post("https://example.test/api/v1/assistant/runs/run_1/cancel").mock(
        return_value=httpx.Response(202, json=run_payload)
    )

    assert client.assistant.get_run("run_1").status == "cancelled"
    assert client.assistant.cancel_run("run_1").status == "cancelled"
