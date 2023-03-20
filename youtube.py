import logging
import re

import sopel.config.types
import sopel.module
import requests


"""
Config should look like:

[youtube]
api_key=zzzzzzzzzzzzzzzzzzzz
"""


TPL = "You\x0300,04Tube\x0f - {title} | Duration: {duration} | Views: {views:,}"
DURATION_RE = re.compile(r"PT(?P<h>\d+H)?(?P<m>\d+M)?(?P<s>\d+S)?")


class YouTubeSection(sopel.config.types.StaticSection):
    api_key = sopel.config.types.ValidatedAttribute("api_key", str)


def setup(bot):
    bot.config.define_section("youtube", YouTubeSection)


def configure(config):
    config.define_section("youtube", YouTubeSection, validate=False)
    config.youtube.configure_setting("api_key", "API key for YouTube")


def get_data(video_id, api_key):
    response = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={
            "id": video_id,
            "key": api_key,
            "part": "contentDetails,snippet,statistics",
        },
        timeout=10,
    )

    if response.status_code != 200:
        return {}

    return response.json()


# Won't work for videos longer than 24hrs
def parse_duration(data):
    if data["snippet"]["liveBroadcastContent"] == "live":
        return "Live"

    match = DURATION_RE.match(data["contentDetails"]["duration"]).groupdict()
    duration = []
    for key in "hms":
        if value := match.get(key):
            # strip 'H' 'M' 'S' from values
            int_value = int(value[:-1])
            duration.append(f"{int_value:02d}")
        else:
            duration.append("00")

    return ":".join(duration)


@sopel.module.rule(r".*youtube.com/watch\S*v=(?P<vid>[\w-]+)")
@sopel.module.rule(r".*youtu.be/([\w-]+)")
def title_lookup(bot, trigger):
    if not bot.config.youtube.api_key:
        logging.error("Missing api_key configuration setting")
        return

    yt_data = get_data(trigger.groups(1), bot.config.youtube.api_key)["items"]
    if not yt_data:
        bot.say("Failed to look up title")
        return

    bot.say(
        TPL.format(
            title=yt_data[0]["snippet"]["title"],
            duration=parse_duration(yt_data[0]),
            views=int(yt_data[0]["statistics"]["viewCount"]),
        )
    )
