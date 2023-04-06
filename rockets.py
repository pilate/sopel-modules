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


@ttlcache(600)
def get_launches(name=""):
    params = {"mode": "detailed"}
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
        # if launch["status"]["id"] != 1:
        #     continue

        launch_time = datetime.datetime.strptime(launch["net"], DATE_FMT)
        if launch_time < now:
            continue

        launch["net_diff"] = launch_time - now

        matching.append(launch)

    return matching


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

    line += " | \x02Countdown:\x0f T-{net_diff}".format(net_diff=launch["net_diff"])

    return line


@sopel.module.rule(r"^\.?\.launch(?: (.+))?$")
def next_launch(bot, trigger):
    name = trigger.group(1) or ""

    launches = get_launches(name)
    if not launches:
        bot.say("No launches found")
        return

    bot.say(format_launch(launches[0]))


@sopel.module.rule(r"^\.?\.launches(?: (.+))?$")
def next_launches(bot, trigger):
    name = trigger.group(1) or ""

    launches = get_launches(name)
    if not launches:
        bot.say("No launches found")
        return

    for count, launch in enumerate(launches):
        bot.say(format_launch(launch))
        if count == 3:
            break
