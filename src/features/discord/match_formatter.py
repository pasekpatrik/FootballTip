from datetime import datetime

from src.core.constants import MATCH_LIMIT


def format_matches_message(matches, tips=None):
    tips = tips or {}
    if not matches:
        return "🤖 **Fotbalový AI Bot:** Pro dnešní den nejsou k dispozici žádné naplánované zápasy nebo vypršel limit API."

    message = "⚽ **Přehled nadcházejících zápasů a tipů od AI:**\n\n"

    for index, match in enumerate(matches[:MATCH_LIMIT]):
        home_team = match['homeTeam']['name']
        away_team = match['awayTeam']['name']
        utc_date = match['utcDate']
        competition = match['competition']['name']

        match_datetime = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ")
        match_date = match_datetime.strftime("%d.%m.%Y")
        match_time = match_datetime.strftime("%H:%M")

        message += f"🏆 **{competition}**\n"
        message += f"⚔️ {home_team} vs {away_team}\n"
        message += f"📅 Datum: {match_date}\n"
        message += f"⏰ Čas: {match_time} UTC\n"
        tip = tips.get(index)
        if tip:
            message += f"💡 **Hlavní tip (jistota: {tip['confidence']})**\n"
            if tip["market"] == "Bez sázky":
                message += "🎯 Bez sázky: podklady nestačí na rozumný tip.\n"
            else:
                message += f"🎯 Trh: {tip['market']} | Výběr: {tip['pick']}\n"
            if tip["reason"]:
                message += f"📊 Analýza: {tip['reason']}\n"
            if tip["risk"]:
                message += f"⚠️ Riziko: {tip['risk']}\n"
            if tip["alternative"]:
                message += f"↪ Alternativa: {tip['alternative']}\n"
        else:
            message += "💡 AI tip: nyní nedostupný.\n"
        message += "-----------------------------------\n"

    return message
