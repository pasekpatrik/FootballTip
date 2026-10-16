import os

import requests


def fetch_football_matches():
    url = "https://api.football-data.org/v4/matches"
    api_key = os.environ.get("FOOTBALL_DATA_API_KEY")
    headers = {"X-Auth-Token": api_key}

    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            return response.json().get("matches", [])
        print(f"Chyba při stahování dat z API: {response.status_code} - {response.text}")
        return []
    except Exception as error:
        print(f"Výjimka při komunikaci s API: {error}")
        return []


def fetch_competition_matches(competition_code, match_date):
    url = f"https://api.football-data.org/v4/competitions/{competition_code}/matches"
    api_key = os.environ.get("FOOTBALL_DATA_API_KEY")

    if not api_key:
        print("Chybí football-data.org API klíč v proměnné prostředí FOOTBALL_DATA_API_KEY.")
        return []

    try:
        response = requests.get(
            url,
            headers={"X-Auth-Token": api_key},
            params={"dateFrom": match_date, "dateTo": match_date},
            timeout=20,
        )
        response.raise_for_status()
        return response.json().get("matches", [])
    except (requests.RequestException, ValueError, TypeError) as error:
        print(f"Zápasy soutěže {competition_code} nejsou dostupné: {error}")
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
        return response.json()
    except (requests.RequestException, ValueError, KeyError, TypeError) as error:
        print(f"Tabulka soutěže {competition_id} není dostupná: {error}")
        return {}


def fetch_match_head2head(match_id, api_key):
    url = f"https://api.football-data.org/v4/matches/{match_id}/head2head?limit=12"

    try:
        response = requests.get(
            url,
            headers={"X-Auth-Token": api_key},
            timeout=20,
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError, KeyError, TypeError) as error:
        print(f"Vzájemné zápasy {match_id} nejsou dostupné: {error}")
        return {}
