from datetime import timedelta
from datetime import datetime
import time

import requests
import sopel.config.types
import sopel.module


"""
Config should look like:

[google]
api_key=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa


Requires API access to:

https://developers.google.com/maps/documentation/geocoding/get-api-key
https://developers.google.com/maps/documentation/timezone/get-api-key

"""


class GoogleSection(sopel.config.types.StaticSection):
    api_key = sopel.config.types.ValidatedAttribute("api_key", str)


def setup(bot):
    bot.config.define_section("google", GoogleSection)


def configure(config):
    config.define_section("google", GoogleSection, validate=False)
    config.google.configure_setting("api_key", "API key for Google")


def geo_lookup(location, api_key):
    response = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={"address": location, "key": api_key},
        timeout=10,
    ).json()["results"]

    if response:
        return response[0]


def time_lookup(geo_data, api_key):
    geo_loc = geo_data["geometry"]["location"]

    return requests.get(
        "https://maps.googleapis.com/maps/api/timezone/json",
        params={
            "location": "{lat},{lng}".format(**geo_loc),
            "timestamp": int(time.time()),
            "key": api_key,
        },
        timeout=10,
    ).json()


@sopel.module.rule("\\.?\\.time (.+)$")
def get_time(bot, trigger):
    if not bot.config.google.api_key:
        return

    location = trigger.group(1).strip()

    geo_data = geo_lookup(location, bot.config.google.api_key)
    if (not geo_data) or ("geometry" not in geo_data):
        bot.say(f"Unable to find location: {location}")
        return

    time_data = time_lookup(geo_data, bot.config.google.api_key)

    utc = datetime.utcnow().replace(microsecond=0)
    delta = timedelta(seconds=time_data["rawOffset"] + time_data["dstOffset"])

    location_name = geo_data["formatted_address"]
    modified = utc + delta
    timezone = time_data["timeZoneId"]
    hours = int((delta.total_seconds() / 60 / 60) * 100)

    bot.say(f"Time in {location_name} is: {modified} ({timezone}, UTC{hours:+05d})")
