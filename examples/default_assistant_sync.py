from nevara import Nevara


client = Nevara()
session = client.assistant.create_session(
    title="SDK smoke test",
    context={"timezone": "America/New_York"},
)

turn = client.assistant.run(
    session.id,
    "Write a short follow-up email after a discovery call.",
)

print(turn.output["content"] if turn.output else turn.run.raw)
