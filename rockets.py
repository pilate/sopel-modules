import datetime
import json
from operator import itemgetter
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


@ttlcache(300)
def get_launches(name=""):
    params = {"mode": "detailed"}
    if name:
        params = {"search": name}

    response = requests.get(
        "https://ll.thespacedevs.com/2.2.0/launch/upcoming/",
        params=params,
        timeout=30,
    ).json()

    # return empty list on error
    return response.get("results", [])


def format_launch(launch):
    line = "{provider}: ".format(provider=launch["launch_service_provider"]["name"])

    rocket_config = launch["rocket"]["configuration"]
    line += "{name} - ".format(name=rocket_config["name"])

    if mission := launch.get("mission"):
        line += "\x02{name}\x0f".format(name=mission["name"])
        line += " | \x02Mission:\x0f {type} ({orbit})".format(
            type=mission["type"], orbit=mission["orbit"]["name"]
        )

    else:
        launch_name = launch["name"]
        rocket_name = rocket_config["full_name"]
        line += "\x02{name}\x0f".format(
            name=launch_name.replace(rocket_name, "").strip(" |")
        )

    if pad := launch.get("pad"):
        line += " | \x02Pad:\x0f {name} - {location}".format(
            name=pad["name"], location=pad["location"]["name"]
        )

    if vid_urls := launch.get("vidURLs"):
        line += " | \x02Streams:\x0f "
        getter = itemgetter("url")
        line += " / ".join(map(getter, vid_urls))

    line += " | \x02Countdown:\x0f T-{net_diff} ({status})".format(
        net_diff=launch["net_diff"], status=launch["status"]["name"]
    )

    return line


@sopel.module.rule(r"^\.?\.launch(?: (.+))?$")
def next_launch(bot, trigger):
    name = trigger.group(1) or ""

    launches = get_launches(name)

    now = datetime.datetime.utcnow()
    now = now.replace(microsecond=0)

    for launch in launches:
        launch_time = datetime.datetime.strptime(launch["net"], DATE_FMT)
        if launch_time < now:
            continue

        launch["net_diff"] = launch_time - now

        bot.say(format_launch(launch))
        break

    else:
        bot.say("No launches found")


@sopel.module.rule(r"^\.?\.launches(?: (.+))?$")
def next_launches(bot, trigger):
    name = trigger.group(1) or ""

    launches = get_launches(name)

    now = datetime.datetime.utcnow()
    now = now.replace(microsecond=0)

    found = 0
    for launch in launches:
        if found == 4:
            break

        launch_time = datetime.datetime.strptime(launch["net"], DATE_FMT)
        if launch_time < now:
            continue

        launch["net_diff"] = launch_time - now
        bot.say(format_launch(launch))
        found += 1

    if not found:
        bot.say("No launches found")


