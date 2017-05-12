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


TPL = u"You\x0300,04Tube\x0f - {title} | Duration: {duration} | Views: {views:,}"
DURATION_RE = re.compile("PT(?P<h>\d+H)?(?P<m>\d+M)?(?P<s>\d+S)?")


class YouTubeSection(sopel.config.types.StaticSection):
    api_key = sopel.config.types.ValidatedAttribute("api_key", str)


def setup(bot):
    bot.config.define_section("youtube", YouTubeSection)


def configure(config):
    config.define_section("youtube", YouTubeSection, validate=False)
    config.youtube.configure_setting("api_key", "API key for YouTube")


def get_data(video_id, api_key):
    response = requests.get("https://www.googleapis.com/youtube/v3/videos", params={
        "id": video_id,
        "key": api_key,
        "part": "contentDetails,snippet,statistics"
    })

    if response.status_code != 200:
        raise Exception("Failed to lookup title")

    return response.json()


# Won't work for videos longer than 24hrs
def parse_duration(duration):
    match = DURATION_RE.match(duration).groupdict()

    duration = []
    for key in "hms":
        if match.get(key):
            duration.append("{0:02d}".format(int(match[key][:-1])))
        else:
            duration.append("00")

    return ":".join(duration)


@sopel.module.rule(r".*youtube.com/watch\S*v=(?P<vid>[\w-]+)")
@sopel.module.rule(r".*youtu.be/([\w-]+)")
def title_lookup(bot, trigger):
    try:
        key = bot.config.youtube.api_key
    except:
        logging.error("Missing api_key configuration setting")
        return

    yt_data = get_data(trigger.groups(1), key)["items"][0]
    duration = parse_duration(yt_data["contentDetails"]["duration"])

    bot.say(TPL.format(
        title=yt_data["snippet"]["title"],
        duration=duration,
        views=long(yt_data["statistics"]["viewCount"])))
