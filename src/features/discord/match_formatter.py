from datetime import datetime

def format_matches_message(matches, tips=None):
    tips = tips or {}
    if not matches:
        return "🤖 **Fotbalový AI Bot:** Pro dnešní den nejsou k dispozici žádné naplánované zápasy nebo vypršel limit API."
    if not tips:
        return "🤖 **Fotbalový AI Bot:** Z dostupných dat se nepodařilo určit dostatečně podložené tipy."

    message = "⚽ **Zápasy s nejvyšší odhadovanou pravděpodobností:**\n\n"

    ranked_tips = sorted(
        tips.items(),
        key=lambda item: (-item[1].get("probability", 0), item[0]),
    )
    for index, tip in ranked_tips:
        if not 0 <= index < len(matches):
            continue
        match = matches[index]
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
        message += f"💡 **Odhad modelu: {tip['probability']} % (jistota: {tip['confidence']})**\n"
        message += f"🎯 Trh: {tip['market']} | Výběr: {tip['pick']}\n"
        if tip["reason"]:
            message += f"📊 Analýza: {tip['reason']}\n"
        if tip["risk"]:
            message += f"⚠️ Riziko: {tip['risk']}\n"
        if tip["alternative"]:
            message += f"↪ Alternativa: {tip['alternative']}\n"
        message += "-----------------------------------\n"

    return message + "Odhady nejsou zárukou výsledku ani doporučením výše vkladu."
