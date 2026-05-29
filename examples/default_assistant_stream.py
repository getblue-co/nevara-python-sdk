from nevara import Nevara


client = Nevara()
session = client.assistant.create_session()

for event in client.assistant.stream(session.id, "Prepare a concise brief for my next customer call."):
    if event.type == "message.delta":
        print(event.data.get("delta", ""), end="")
