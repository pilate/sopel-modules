import datetime
import xml.etree.ElementTree as ET
from decimal import Decimal

import requests
import sopel.module


FEED = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.quakeml"
DATE_FMT = "%Y-%m-%dT%H:%M:%S"
NS = {"": "http://quakeml.org/xmlns/bed/1.2"}


@sopel.module.rule(r"\.?\.quake(s?\s+(?P<threshold>\d+(\.\d+)?))?$")
def last_quake(bot, trigger):
    threshold = trigger.groupdict().get("threshold")
    threshold = Decimal(threshold or 0)

    count = 4
    if not threshold:
        count = 1

    response = requests.get(FEED, timeout=10)
    root = ET.fromstring(response.content)

    events = root.findall("./eventParameters/event", NS)

    lines = []
    for event in events:
        if len(lines) == count:
            break

        now = datetime.datetime.utcnow().replace(microsecond=0)

        name = event.find("./description/text", NS).text
        when = event.find("./origin/time/value", NS).text
        when = when.rsplit(".", 1)[0]

        parsed_when = datetime.datetime.strptime(when, DATE_FMT)
        diff = parsed_when - now

        magnitude = Decimal(event.find("./magnitude/mag/value", NS).text)

        if magnitude > threshold:
            lines.append(f"Magnitude: {magnitude} | {abs(diff)} ago | Location: {name}")

    for line in lines:
        bot.say(line)
