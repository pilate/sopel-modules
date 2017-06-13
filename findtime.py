import sopel.config.types
import sopel.module

import datetime
import time

import requests



"""
Config should look like:

[google]
api_key=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa


Requires API access to:

https://developers.google.com/maps/documentation/geocoding/get-api-key
https://developers.google.com/maps/documentation/timezone/get-api-key

"""

API_KEY = None


class GoogleSection(sopel.config.types.StaticSection):
    api_key = sopel.config.types.ValidatedAttribute("api_key", str)


def setup(bot):
    bot.config.define_section("google", GoogleSection)
    global API_KEY
    try:
        API_KEY = bot.config.google.api_key
    except Exception as e:
        logging.error("Missing google api_key configuration setting: {0}".format(str(e)))
        return


def configure(config):
    config.define_section("google", GoogleSection, validate=False)
    config.google.configure_setting("api_key", "API key for Google")


def geo_lookup(location):
    response = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params={
            "address": location,
            "key": API_KEY
        }).json()["results"]
    if response:
        return response[0]


def time_lookup(geo_data):
    if "geometry" not in geo_data:
        return

    geo_loc = geo_data["geometry"]["location"]

    lat_lng = "{0},{1}".format(geo_loc["lat"], geo_loc["lng"])
    return requests.get("https://maps.googleapis.com/maps/api/timezone/json", params={
        "location": lat_lng,
        "timestamp": int(time.time()),
        "key": API_KEY
        }).json()


@sopel.module.rule("\\.?\\.time (.+)$")
def get_time(bot, trigger):
    location = trigger.group(1).strip()

    geo_data = geo_lookup(location)
    if not geo_data:
        return

    time_data = time_lookup(geo_data)

    utc = datetime.datetime.utcnow().replace(microsecond=0)
    delta = datetime.timedelta(seconds=time_data["rawOffset"] + time_data["dstOffset"])
    modified = utc + delta

    hours = int((delta.total_seconds() / 60 / 60) * 100)
    bot.say("Time in {0} is: {1} ({2}, UTC{3:+05d})".format(geo_data["formatted_address"], str(modified), time_data["timeZoneId"], hours))