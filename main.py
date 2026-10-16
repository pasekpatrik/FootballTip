import json
import os

from src.features.data.football_data import (
    fetch_competition_matches,
    fetch_competition_standings,
    fetch_football_matches,
    fetch_match_head2head,
)
from src.features.discord.webhook import send_discord_message
from src.features.ai_tips import generate_ai_tips
from src.features.match_formatter import format_matches_message


def main():
    print("Spouštím stahování fotbalových dat...")
    matches = fetch_football_matches()

    print(f"Nalezeno zápasů: {len(matches)}")
    tips = generate_ai_tips(matches)
    print("AI model vrátil:")
    print(json.dumps(tips, ensure_ascii=False, indent=2))
    message = format_matches_message(matches, tips)

    if os.environ.get("SKIP_DISCORD", "").lower() == "true":
        print("Testovací režim: zpráva na Discord nebyla odeslána.")
    else:
        send_discord_message(message)


if __name__ == "__main__":
    main()
