# Nevara Python SDK

Python SDK for the Nevara Assistant API.

This first SDK scope is intentionally narrow:

- Uses API key auth.
- Uses only the default assistant: `nevara/default`.
- Supports assistant sessions, turns, streaming turns, run lookup/cancel, and message listing.
- Does not expose custom assistant creation or assistant catalog APIs yet.

```python
from nevara import Nevara

client = Nevara(api_key="nvra_live_...", base_url="https://app.nevara.ai/api/v1")

session = client.assistant.create_session(
    title="Pre-call research",
    context={"timezone": "America/New_York"},
)

response = client.assistant.run(
    session.id,
    "Find my next customer call and prepare a concise brief.",
)

print(response.output["content"])
```

Streaming:

```python
for event in client.assistant.stream(session.id, "Write a follow-up email."):
    if event.type == "message.delta":
        print(event.data["delta"], end="")
```
