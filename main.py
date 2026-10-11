import os
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

def format_matches_message(matches):
    if not matches:
        return "🤖 **Fotbalový AI Bot:** Pro dnešní den nejsou k dispozici žádné naplánované zápasy nebo vypršel limit API."
    
    msg = "⚽ **Přehled nadcházejících zápasů a tipů od AI:**\n\n"
    
    # Zpracujeme prvních 5 zápasů, abychom zprávu zahltili
    count = 0
    for match in matches[:5]:
        home_team = match['homeTeam']['name']
        away_team = match['awayTeam']['name']
        utc_date = match['utcDate']
        competition = match['competition']['name']
        
        # Formátování času
        match_time = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ").strftime("%H:%M")
        
        msg += f"🏆 **{competition}**\n"
        msg += f"⚔️ {home_team} vs {away_team}\n"
        msg += f"⏰ Čas: {match_time} UTC\n"
        msg += f"💡 *AI Tip:* Očekává se ofenzivní duel. Sleduj live kurzy!\n"
        msg += "-----------------------------------\n"
        count += 1
        
    return msg

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
    message = format_matches_message(matches)
    
    send_discord_message(message)