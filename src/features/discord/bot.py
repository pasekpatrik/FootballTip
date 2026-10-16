import asyncio
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord import app_commands

from src.features.data.football_data import fetch_competition_matches
from src.features.prompts.ai_tips import generate_ai_tips
from src.features.discord.match_formatter import format_matches_message


TIMEZONE = ZoneInfo("Europe/Prague")
MESSAGE_LIMIT = 1900


def build_daily_matches_message(competition_code, competition_name):
    match_date = datetime.now(TIMEZONE).date().isoformat()
    matches = fetch_competition_matches(competition_code, match_date)
    if not matches:
        return f"⚽ {competition_name}: na {match_date} nejsou v API dostupné žádné zápasy."

    tips = generate_ai_tips(matches)
    return format_matches_message(matches, tips)


def split_discord_message(message):
    chunks = []
    current_chunk = ""

    for line in message.splitlines():
        remaining = f"{line}\n"
        while remaining:
            available = MESSAGE_LIMIT - len(current_chunk)
            if len(remaining) <= available:
                current_chunk += remaining
                remaining = ""
            else:
                split_at = remaining.rfind("\n", 0, available + 1)
                if split_at <= 0:
                    split_at = available
                current_chunk += remaining[:split_at]
                chunks.append(current_chunk.rstrip())
                current_chunk = ""
                remaining = remaining[split_at:].lstrip("\n")

    if current_chunk:
        chunks.append(current_chunk.rstrip())
    return chunks


intents = discord.Intents.none()
client = discord.Client(intents=intents)
command_tree = app_commands.CommandTree(client)
commands_synced = False


async def send_daily_matches(interaction, competition_code, competition_name):
    await interaction.response.defer(thinking=True)
    try:
        message = await asyncio.to_thread(
            build_daily_matches_message,
            competition_code,
            competition_name,
        )
        for chunk in split_discord_message(message):
            await interaction.followup.send(chunk)
    except Exception:
        logging.exception("Chyba při zpracování příkazu pro soutěž %s", competition_code)
        await interaction.followup.send(
            "Při načítání zápasů nebo tipů nastala chyba. Zkuste to prosím později."
        )


@command_tree.command(name="premierleague", description="Dnešní zápasy Premier League a AI tipy")
async def premier_league(interaction: discord.Interaction):
    await send_daily_matches(interaction, "PL", "Premier League")


@command_tree.command(name="laliga", description="Dnešní zápasy La Ligy a AI tipy")
async def la_liga(interaction: discord.Interaction):
    await send_daily_matches(interaction, "PD", "La Liga")


@client.event
async def on_ready():
    global commands_synced
    if not commands_synced:
        await command_tree.sync()
        commands_synced = True
    print(f"Discord bot je přihlášen jako {client.user}.")


def run():
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise SystemExit("Nastavte proměnnou prostředí DISCORD_BOT_TOKEN.")
    client.run(token)


if __name__ == "__main__":
    run()
