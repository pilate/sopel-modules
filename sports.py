import logging

import sopel.config.types
import sopel.module
import requests


"""
Config should look like:

[sports]
stattleship_token=zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz
"""


SPORTS = {
    "nhl": "hockey",
    "nba": "basketball",
    "mlb": "baseball"
}

TEMPLATES = {
    "nhl": {
        "score": "{scoreline} ({details})",
        "details": "{period}{suffix} {period_label}, {clock}"
    },
    "nba": {
        "score": "{scoreline} ({details})",
        "details": "{period}{suffix} {period_label}, {clock}"
    },
    "mlb": {
        "score": "{scoreline} ({details})",
        "details": "{period}{suffix} {period_label}"
    }
}

SUFFIXES = ["st", "nd", "rd"] + ["th"] * 16


class SportsSection(sopel.config.types.StaticSection):
    stattleship_token = sopel.config.types.ValidatedAttribute("stattleship_token", str)


def setup(bot):
    bot.config.define_section("sports", SportsSection)


def configure(config):
    config.define_section("sports", SportsSection, validate=False)
    config.sports.configure_setting("stattleship_token", "API token for stattleship")


def request_data(sport, league, token):
    url = "https://api.stattleship.com/{sport}/{league}/games".format(sport=sport, league=league)
    result = requests.get(url, params={
            "on": "today"
        },
        headers={
            "Accept": "application/vnd.stattleship.com; version=1",
            "Authorization": "Token token={token}".format(token=token),
            "Content-Type": "application/json"
        })

    try:
        return result.json()
    except Exception as e:
        return {}


def write_scores(bot, league, games):
    output = []

    for game in games:
        details = ""
        if game["status"] == "upcoming":
            continue
        elif game["status"] == "in_progress":
            suffix = SUFFIXES[game["period"] - 1]
            details = TEMPLATES[league]["details"].format(suffix=suffix, **game)
        else:
            details = "F"
        output.append(TEMPLATES[league]["score"].format(details=details, **game))

    bot.say(", ".join(output))


LEAGUES = "|".join(SPORTS.keys())
@sopel.module.rule("\\.?\\.({leagues})$".format(leagues=LEAGUES))
def game_lookup(bot, trigger):
    try:
        token = bot.config.sports.stattleship_token
    except:
        logging.error("Missing stattleship_token configuration setting, unable to lookup game information")
        return

    league = trigger.group(1)
    result = request_data(SPORTS[league], league, token)
    if "games" in result:
        write_scores(bot, league, result["games"])
