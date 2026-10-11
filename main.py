import os
import json
import requests
import pandas as pd
from datetime import datetime

def fetch_football_matches():
    # Použijeme bezplatné API z football-data.org (např. Premier League nebo jiné dostupné ligy)
    # Zde stahujeme aktuální zápasy
    url = "https://api.football-data.org/v4/matches"
    api_key = os.environ.get("FOOTBALL_DATA_API_KEY")
    
    headers = {
        "X-Auth-Token": api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("matches", [])
        else:
            print(f"Chyba při stahování dat z API: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Výjimka při komunikaci s API: {e}")
        return []

def generate_ai_tips(matches):
    if not matches:
        return {}

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Chybí OpenAI API klíč v proměnné prostředí OPENAI_API_KEY.")
        return {}

    fixtures = [
        {
            "match_index": index,
            "competition": match["competition"]["name"],
            "home_team": match["homeTeam"]["name"],
            "away_team": match["awayTeam"]["name"],
            "utc_date": match["utcDate"],
        }
        for index, match in enumerate(matches[:5])
    ]
    prompt = (
        "Navrhni opatrný, stručný sázkový tip pro každý uvedený fotbalový zápas. "
        "Máš pouze názvy týmů, soutěž a datum: nevymýšlej aktuální formu, zranění, "
        "kurzy ani statistiky. Pokud pro tip nejsou podklady, výslovně uveď nízkou jistotu. "
        "Nezaručuj výhru ani nedoporučuj výši sázky. Vrať pouze JSON objekt s polem tips; "
        "každá položka musí mít match_index, pick, confidence (nízká/střední) a krátké reason.\n"
        f"Zápasy: {json.dumps(fixtures, ensure_ascii=False)}"
    )

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": [
                    {"role": "system", "content": "Jsi opatrný analytik fotbalových zápasů."},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.3,
            },
            timeout=30,
        )
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
    
    # Zpracujeme prvních 5 zápasů, abychom zprávu zahltili
    count = 0
    for index, match in enumerate(matches[:5]):
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
    
    payload = {
        "content": message
    }
    
    response = requests.post(webhook_url, json=payload)
    if response.status_code in [200, 204]:
        print("Zpráva úspěšně odeslána na Discord!")
    else:
        print(f"Chyba při odesílání na Discord: {response.status_code} - {response.text}")

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