import json
import os

import requests

from src.core.constants import HEAD2HEAD_LIMIT, MATCH_LIMIT, STANDINGS_LIMIT
from src.features.data.football_data import fetch_competition_standings, fetch_match_head2head
from src.features.prompts.football_tips import build_tips_prompt


def _compact_match(index, match):
    competition = match.get("competition") or {}
    home_team = match.get("homeTeam") or {}
    away_team = match.get("awayTeam") or {}
    compact = {
        "match_index": index,
        "competition": competition.get("name"),
        "home_team": home_team.get("name"),
        "away_team": away_team.get("name"),
        "utc_date": match.get("utcDate"),
        "status": match.get("status"),
        "matchday": match.get("matchday"),
    }
    full_time_score = (match.get("score") or {}).get("fullTime") or {}
    if full_time_score.get("home") is not None or full_time_score.get("away") is not None:
        compact["score"] = {
            "home": full_time_score.get("home"),
            "away": full_time_score.get("away"),
        }
    return compact


def _compact_standings(data, relevant_team_names):
    competition = data.get("competition") or {}
    total_table = next(
        (standing for standing in data.get("standings", []) if standing.get("type") == "TOTAL"),
        None,
    )
    if not total_table:
        return {}

    rows = []
    for row in total_table.get("table", []):
        team = row.get("team") or {}
        team_name = team.get("name")
        position = row.get("position")
        if position is not None and position > 5 and team_name not in relevant_team_names:
            continue
        compact_row = {
            key: row.get(key)
            for key in ("position", "playedGames", "won", "draw", "lost", "points", "goalsFor", "goalsAgainst", "goalDifference", "form")
            if row.get(key) is not None
        }
        if team_name:
            compact_row["team"] = team_name
        rows.append(compact_row)

    return {"competition": competition.get("name"), "table": rows}


def _compact_head2head(data):
    compact_matches = []
    for match in data.get("matches", [])[:3]:
        competition = match.get("competition") or {}
        home_team = match.get("homeTeam") or {}
        away_team = match.get("awayTeam") or {}
        score = (match.get("score") or {}).get("fullTime") or {}
        compact_matches.append(
            {
                "competition": competition.get("name"),
                "utc_date": match.get("utcDate"),
                "home_team": home_team.get("name"),
                "away_team": away_team.get("name"),
                "score": {"home": score.get("home"), "away": score.get("away")},
            }
        )
    return compact_matches


def generate_ai_tips(matches):
    if not matches:
        return {}

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Chybí Groq API klíč v proměnné prostředí GROQ_API_KEY.")
        return {}

    football_data_api_key = os.environ.get("FOOTBALL_DATA_API_KEY")
    selected_matches = matches[:MATCH_LIMIT]
    standings_by_competition = {}
    head2head_by_match = {}
    if football_data_api_key:
        for match in selected_matches:
            competition_id = match.get("competition", {}).get("id")
            if (
                competition_id is not None
                and competition_id not in standings_by_competition
                and len(standings_by_competition) < STANDINGS_LIMIT
            ):
                standings_by_competition[competition_id] = fetch_competition_standings(
                    competition_id,
                    football_data_api_key,
                )

            match_id = match.get("id")
            if match_id is not None and len(head2head_by_match) < HEAD2HEAD_LIMIT:
                head2head_by_match[match_id] = fetch_match_head2head(
                    match_id,
                    football_data_api_key,
                )

    api_data = {
        "matches": [
            _compact_match(index, match)
            for index, match in enumerate(selected_matches)
        ],
        "standings_by_competition": {
            str(competition_id): _compact_standings(
                data,
                {
                    (match.get("homeTeam") or {}).get("name")
                    for match in selected_matches
                }
                | {
                    (match.get("awayTeam") or {}).get("name")
                    for match in selected_matches
                },
            )
            for competition_id, data in standings_by_competition.items()
        },
        "head2head_by_match": {
            str(match_id): _compact_head2head(data)
            for match_id, data in head2head_by_match.items()
        },
    }
    prompt = build_tips_prompt(api_data)

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
                "max_tokens": 2800,
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
            if not isinstance(index, int) or not 0 <= index < len(selected_matches):
                continue
            market = " ".join(str(tip.get("market", "")).split())[:80]
            pick = " ".join(str(tip.get("pick", "")).split())[:100]
            reason = " ".join(str(tip.get("reason", "")).split())[:400]
            risk = " ".join(str(tip.get("risk", "")).split())[:300]
            alternative = " ".join(str(tip.get("alternative", "")).split())[:140]
            confidence = tip.get("confidence", "nízká")
            if market and pick:
                tips[index] = {
                    "market": market,
                    "pick": pick,
                    "reason": reason,
                    "risk": risk,
                    "alternative": alternative,
                    "confidence": confidence if confidence in ("nízká", "střední") else "nízká",
                }
        return tips
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as error:
        print(f"Chyba při generování AI tipů: {error}")
        return {}
