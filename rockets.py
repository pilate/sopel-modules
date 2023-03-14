import datetime

import requests
import sopel.module


DATE_FMT = "%Y-%m-%dT%H:%M:%SZ"


def get_launches(name=""):
    params = {}
    if name:
        params = {"search": name}

    now = datetime.datetime.utcnow()
    now = now.replace(microsecond=0)

    response = requests.get(
        "https://lldev.thespacedevs.com/2.2.0/launch/upcoming/",
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


@sopel.module.rule("\\.?\\.launch(?: (.+))?$")
def next_launch(bot, trigger):
    name = trigger.group(1) or ""

    data = get_launches(name)
    if not data:
        bot.say("No launches found")
        return

    launch = data[0]
    flattened = flatten({}, launch)

    line = "{_name}"
    line += " | Rocket: {_rocket_configuration_full_name}"
    if launch.get("mission"):
        line += " | Mission: {_mission_type}, {_mission_orbit_name}"
    if launch.get("pad"):
        line += " | Pad: {_pad_name}, {_pad_location_name}"
    line += " | Countdown: {_net_diff}"

    bot.say(line.format(**flattened))
