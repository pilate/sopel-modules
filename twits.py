import base64
import logging
import xml.etree.ElementTree as ElementTree
from html.parser import HTMLParser

import requests
import sopel.config.types
import sopel.module

"""
Config should look like:

[twitter]
consumer_key=aaaaaaaaaaaaaaaaa
consumer_secret=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
"""

BEARER = None


class TwitterSection(sopel.config.types.StaticSection):
    consumer_key = sopel.config.types.ValidatedAttribute("consumer_key", str)
    consumer_secret = sopel.config.types.ValidatedAttribute("consumer_secret", str)


def setup(bot):
    bot.config.define_section("twitter", TwitterSection)
    global BEARER
    BEARER = get_bearer_token(bot)


def configure(config):
    config.define_section("twitter", TwitterSection, validate=False)
    config.twitter.configure_setting("consumer_key", "Consumer key for Twitter")
    config.twitter.configure_setting("consumer_secret", "Consumer secret for Twitter")


def get_bearer_token(bot):
    try:
        key = bot.config.twitter.consumer_key
        secret = bot.config.twitter.consumer_secret
    except Exception as e:
        logging.error("Missing consumer_key or consumer_secret configuration setting: {0}".format(str(e)))
        return

    joined_credentials = base64.b64encode(f"{key}:{secret}".encode())
    response =requests.post("https://api.twitter.com/oauth2/token", data={
            "grant_type":"client_credentials"
        }, headers={
            "Authorization": f"Basic {joined_credentials.decode()}",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        })
    if response.status_code != 200:
        raise Exception("Unable to obtain bearer token")

    return response.json()["access_token"]


def get_latest(user):
    response = requests.get("https://api.twitter.com/1.1/statuses/user_timeline.json", params={
            "screen_name": user,
            "count": 1,
            "include_rts": False,
            "tweet_mode": "extended"
        }, headers={
            "Authorization": "Bearer {0}".format(BEARER),
        })

    if response.status_code != 200:
        raise Exception("Unable to request timeline")

    return response.json()[0]


def get_tweet(tweet):
    response = requests.get("https://api.twitter.com/1.1/statuses/show.json", params={
            "id": tweet,
            "tweet_mode": "extended"
        }, headers={
            "Authorization": "Bearer {0}".format(BEARER),
        })

    if response.status_code != 200:
        raise Exception("Unable to request tweet")

    return response.json()


def write_twit(bot, tweet_data):
    if "full_text" in tweet_data:
        text = tweet_data["full_text"]
    else:
        text = tweet_data["text"]
    fixed_data = text.replace("\n", " ")
    fixed_data = HTMLParser().unescape(fixed_data)
    bot.say(u"@{0}: {1}".format(tweet_data["user"]["name"], fixed_data))


@sopel.module.rule("\\.?\\.tweet ([^ ]+)$")
def last_tweet(bot, trigger):
    tweeter = trigger.group(1).strip()

    try:
        tweet = get_latest(tweeter)
    except Exception as e:
        return

    write_twit(bot, tweet)


@sopel.module.rule("\\.?\\.trump$")
def trump_tweet(bot, trigger):
    try:
        tweet = get_latest("realDonaldTrump")
    except Exception as e:
        return

    write_twit(bot, tweet)


@sopel.module.rule(r".*twitter.com/(\S*)/status/(?P<id>\d+)")
def specific_tweet(bot, trigger):
    tweet_id = trigger.groupdict()["id"]
    tweet = get_tweet(tweet_id)

    write_twit(bot, tweet)
