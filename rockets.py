import sopel.module

import requests

import datetime
import time



def get_launch_data(name):
    if name:
        name = "/" + name

    launches = requests.get("https://launchlibrary.net/1.2/launch{0}".format(name), params={
        "mode": "verbose",
        "startdate": datetime.datetime.utcnow().date(),
    }).json()

    if not launches["count"]:
        return []

    # Filter out launches that already happened
    launches = filter(lambda l: l["status"] not in [3, 4], launches["launches"])

    return launches


def print_launch_data(bot, launch):
    types = ", ".join(map(lambda l: l["typeName"], launch["missions"]))

    line = "(Rocket: {name}) (Payload Type: {type}) (Where: {location}) (When: {net})".format(
        name=launch["rocket"]["name"],
        type=types,
        location=launch["location"]["name"],
        net=launch["net"])

    # If we have a launch time, calculate the time remaining
    if launch["netstamp"]:
        delta = datetime.timedelta(seconds=launch["netstamp"] - int(time.time())) 
        line += " (Countdown: {delta})".format(delta=delta)

    if not target:
        bot.say(line)
    else:
        bot.msg(target, line)


@sopel.module.rule("\\.?\\.launch(?: (.+))?$")
def next_launch(bot, trigger):
    name = trigger.group(1) or ""

    data = get_launch_data(name.strip())
    if data:
        print_launch_data(bot, data[0])
    else:
        bot.say("No launches found.")
