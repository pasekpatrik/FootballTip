import os

import requests


def send_discord_message(message):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        print("Chybí Discord webhook URL v proměnných prostředí.")
        return

    chunks = []
    current_chunk = ""
    for line in message.splitlines():
        addition = f"{line}\n"
        if current_chunk and len(current_chunk) + len(addition) > 1900:
            chunks.append(current_chunk.rstrip())
            current_chunk = ""
        current_chunk += addition
    if current_chunk:
        chunks.append(current_chunk.rstrip())

    for chunk in chunks:
        response = requests.post(
            webhook_url,
            json={"content": chunk},
            timeout=20,
        )
        if response.status_code not in (200, 204):
            print(f"Chyba při odesílání na Discord: {response.status_code} - {response.text}")
            return

    print(f"Odesláno {len(chunks)} zpráv na Discord.")
