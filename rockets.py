import datetime
import json
from time import time

import requests
import sopel.module


DATE_FMT = "%Y-%m-%dT%H:%M:%SZ"


def ttlcache(seconds=10):
    def wrap(function):
        cache = {}

        def wrapped(*args, **kwargs):
            now = time()

            cache_key = json.dumps([args, kwargs])
            if cached := cache.get(cache_key):
                expiration, value = cached
                if now < expiration:
                    return value

            value = function(*args, **kwargs)

            cache[cache_key] = (time() + seconds, value)

            return value

        return wrapped

    return wrap


@ttlcache(600)
def get_launches(name=""):
    params = {}
    if name:
        params = {"search": name}

    now = datetime.datetime.utcnow()
    now = now.replace(microsecond=0)

    response = requests.get(
        "https://ll.thespacedevs.com/2.2.0/launch/upcoming/",
        params=params,
        timeout=10,
    ).json()

    matching = []
    for launch in response["results"]:
        if launch["status"]["id"] != 1:
            continue

        launch_time = datetime.datetime.strptime(launch["net"], DATE_FMT)
        if launch_time < now:
            continue

        launch["net_diff"] = launch_time - now

        matching.append(launch)

    return matching


def flatten(root, thing, prefix=""):
    if isinstance(thing, dict):
        for key, value in thing.items():
            flatten(root, value, f"{prefix}_{key}")
    elif isinstance(thing, list):
        for counter, value in enumerate(thing):
            flatten(root, value, f"{prefix}_{counter}")
    else:
        root[prefix] = thing

    return root


def format_launch(launch):
    flattened = flatten({}, launch)

    line = "{_rocket_configuration_full_name} - \x02{_mission_name}\x0f"

    if launch.get("mission"):
        line += " | \x02Mission:\x0f {_mission_type} ({_mission_orbit_name})"

    if launch.get("pad"):
        line += " | \x02Pad:\x0f {_pad_name}, {_pad_location_name}"

    line += " | \x02Countdown:\x0f T-{_net_diff}"

    return line.format(**flattened)


@sopel.module.rule("\\.?\\.launch(?: (.+))?$")
def next_launch(bot, trigger):
    name = trigger.group(1) or ""

    launches = get_launches(name)
    if not launches:
        bot.say("No launches found")
        return

    bot.say(format_launch(launches[0]))


@sopel.module.rule("\\.?\\.launches$")
def next_launches(bot, _):
    data = get_launches()
    if not data:
        bot.say("No launches found")
        return

    for count, launch in enumerate(data):
        bot.say(format_launch(launch))
        if count == 4:
            break
