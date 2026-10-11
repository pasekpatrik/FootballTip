import os
import json
import requests
import pandas as pd
from datetime import datetime

MATCH_LIMIT = 10
STANDINGS_LIMIT = 5

def fetch_football_matches():
    # Použijeme bezplatné API z football-data.org (např. Premier League nebo jiné dostupné ligy)
    # Zde stahujeme aktuální zápasy
    url = "https://api.football-data.org/v4/matches"
    api_key = os.environ.get("FOOTBALL_DATA_API_KEY")
    
    headers = {
        "X-Auth-Token": api_key
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            data = response.json()
            return data.get("matches", [])
        else:
            print(f"Chyba při stahování dat z API: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Výjimka při komunikaci s API: {e}")
        return []

def fetch_competition_standings(competition_id, api_key):
    url = f"https://api.football-data.org/v4/competitions/{competition_id}/standings"

    try:
        response = requests.get(
            url,
            headers={"X-Auth-Token": api_key},
            timeout=20,
        )
        response.raise_for_status()
        standings = response.json().get("standings", [])
        table = next(
            (item.get("table", []) for item in standings if item.get("type") == "TOTAL"),
            [],
        )
        return {
            row["team"]["id"]: {
                "position": row.get("position"),
                "form": row.get("form"),
                "played": row.get("playedGames"),
                "points": row.get("points"),
                "goals_for": row.get("goalsFor"),
                "goals_against": row.get("goalsAgainst"),
            }
            for row in table
            if row.get("team", {}).get("id") is not None
        }
    except (requests.RequestException, ValueError, KeyError, TypeError) as e:
        print(f"Tabulka soutěže {competition_id} není dostupná: {e}")
        return {}

def generate_ai_tips(matches):
    if not matches:
        return {}

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Chybí Groq API klíč v proměnné prostředí GROQ_API_KEY.")
        return {}

    selected_matches = matches[:MATCH_LIMIT]
    standings_by_competition = {}
    for match in selected_matches:
        competition_id = match.get("competition", {}).get("id")
        if (
            competition_id is not None
            and competition_id not in standings_by_competition
            and len(standings_by_competition) < STANDINGS_LIMIT
        ):
            standings_by_competition[competition_id] = fetch_competition_standings(
                competition_id,
                api_key,
            )

    fixtures = []
    for index, match in enumerate(selected_matches):
        competition_id = match.get("competition", {}).get("id")
        standings = standings_by_competition.get(competition_id, {})
        home_team = match["homeTeam"]
        away_team = match["awayTeam"]
        fixtures.append({
            "match_index": index,
            "competition": match["competition"]["name"],
            "home_team": home_team["name"],
            "away_team": away_team["name"],
            "utc_date": match["utcDate"],
            "home_stats": standings.get(home_team.get("id")),
            "away_stats": standings.get(away_team.get("id")),
        })
    prompt = (
        "Navrhni opatrný, stručný sázkový tip pro každý uvedený fotbalový zápas. "
        "Využij přiloženou formu a statistiky z tabulky, pokud jsou dostupné. "
        "Nevymýšlej chybějící formu, zranění ani kurzy. Pokud jsou podklady omezené, "
        "výslovně uveď nízkou jistotu. "
        "Nezaručuj výhru ani nedoporučuj výši sázky. Vrať pouze JSON objekt s polem tips; "
        "každá položka musí mít match_index, pick, confidence (nízká/střední) a krátké reason.\n"
        f"Zápasy: {json.dumps(fixtures, ensure_ascii=False)}"
    )

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": os.environ.get("GROQ_MODEL") or "openai/gpt-oss-120b",
                "messages": [
                    {"role": "system", "content": "Jsi opatrný analytik fotbalových zápasů."},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.3,
            },
            timeout=30,
        )
        if response.status_code >= 400:
            print(f"Odpověď Groq API ({response.status_code}): {response.text[:1000]}")
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        result = json.loads(content)
        tips = {}
        for tip in result.get("tips", []):
            index = tip.get("match_index")
            if not isinstance(index, int) or not 0 <= index < len(fixtures):
                continue
            pick = " ".join(str(tip.get("pick", "")).split())[:100]
            reason = " ".join(str(tip.get("reason", "")).split())[:140]
            confidence = tip.get("confidence", "nízká")
            if pick:
                tips[index] = {
                    "pick": pick,
                    "reason": reason,
                    "confidence": confidence if confidence in ("nízká", "střední") else "nízká",
                }
        return tips
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as e:
        print(f"Chyba při generování AI tipů: {e}")
        return {}

def format_matches_message(matches, tips=None):
    tips = tips or {}
    if not matches:
        return "🤖 **Fotbalový AI Bot:** Pro dnešní den nejsou k dispozici žádné naplánované zápasy nebo vypršel limit API."
    
    msg = "⚽ **Přehled nadcházejících zápasů a tipů od AI:**\n\n"
    
    count = 0
    for index, match in enumerate(matches[:MATCH_LIMIT]):
        home_team = match['homeTeam']['name']
        away_team = match['awayTeam']['name']
        utc_date = match['utcDate']
        competition = match['competition']['name']
        
        # Formátování času
        match_datetime = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ")
        match_date = match_datetime.strftime("%d.%m.%Y")
        match_time = match_datetime.strftime("%H:%M")
        
        msg += f"🏆 **{competition}**\n"
        msg += f"⚔️ {home_team} vs {away_team}\n"
        msg += f"📅 Datum: {match_date}\n"
        msg += f"⏰ Čas: {match_time} UTC\n"
        tip = tips.get(index)
        if tip:
            msg += f"💡 AI tip (jistota: {tip['confidence']}): {tip['pick']} - {tip['reason']}\n"
        else:
            msg += "💡 AI tip: nyní nedostupný.\n"
        msg += "-----------------------------------\n"
        count += 1

    return msg + "⚠️ Tipy jsou nejisté odhady, ne garance výhry."

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

if __name__ == "__main__":
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