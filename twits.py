import base64
import html
import logging
import re
from functools import lru_cache


import requests
import sopel.config.types
import sopel.module


"""
Config should look like:

[twitter]
consumer_key=aaaaaaaaaaaaaaaaa
consumer_secret=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
"""


class TwitterSection(sopel.config.types.StaticSection):
    consumer_key = sopel.config.types.ValidatedAttribute("consumer_key", str)
    consumer_secret = sopel.config.types.ValidatedAttribute("consumer_secret", str)
    bearer = sopel.config.types.ValidatedAttribute("bearer", str)


def setup(bot):
    bot.config.define_section("twitter", TwitterSection)
    if not bot.db.get_plugin_value("twits", "bearer"):
        bot.db.set_plugin_value("twits", "bearer", get_bearer_token(bot))


def configure(config):
    config.define_section("twitter", TwitterSection, validate=False)
    config.twitter.configure_setting("consumer_key", "Consumer key for Twitter")
    config.twitter.configure_setting("consumer_secret", "Consumer secret for Twitter")
    config.twitter.configure_setting("bearer", "Bearer token for twitter")


def get_bearer_token(bot):
    try:
        if bearer := bot.config.twitter.bearer:
            return bearer
        key = bot.config.twitter.consumer_key
        secret = bot.config.twitter.consumer_secret

    except Exception as exc:
        logging.error(
            "Missing consumer_key or consumer_secret configuration setting: %s", exc
        )
        return ""

    joined_credentials = base64.b64encode(f"{key}:{secret}".encode())
    response = requests.post(
        "https://api.twitter.com/oauth2/token",
        data={"grant_type": "client_credentials"},
        headers={
            "Authorization": f"Basic {joined_credentials.decode()}",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        },
        timeout=10,
    )
    if response.status_code != 200:
        raise Exception("Unable to obtain bearer token")

    return response.json()["access_token"]


def make_request(api, params, bearer):
    response = requests.get(
        f"https://api.twitter.com/1.1/statuses/{api}",
        params=params,
        headers={
            "Authorization": f"Bearer {bearer}",
        },
        timeout=10,
    )

    if response.status_code != 200:
        raise Exception("API request failed: %s (%d)", response, response.status_code)

    return response.json()


@lru_cache
def get_tweet(tweet_id, bearer):
    return make_request(
        "show.json", params={"id": tweet_id, "tweet_mode": "extended"}, bearer=bearer
    )


def write_twit(bot, tweet_data):
    if "full_text" in tweet_data:
        text = tweet_data["full_text"]
    else:
        text = tweet_data["text"]

    # strip newlies
    fixed_data = text.replace("\n", " ")
    # merge whitespace
    fixed_data = re.sub(r"\s+", " ", fixed_data)
    # html entity unescape
    fixed_data = html.unescape(fixed_data)

    tweeter = tweet_data["user"]["name"]
    bot.say(f"@{tweeter}: {fixed_data}")


@sopel.module.rule("\\.?\\.tweet ([^ ]+)$")
def last_tweet(bot, trigger):
    bearer = bot.db.get_plugin_value("twits", "bearer")
    if not bearer:
        return

    tweeter = trigger.group(1).strip()

    try:
        tweet = make_request(
            "user_timeline.json",
            params={
                "screen_name": tweeter,
                "count": 1,
                "include_rts": False,
                "tweet_mode": "extended",
            },
            bearer=bearer,
        )[0]

    except Exception:
        bot.say(f"Failed to get latest tweet for {tweeter}")
        return

    write_twit(bot, tweet)


@sopel.module.rule(r"https?://[^/]*twitter.com/(\S*)/status/(?P<id>\d+)")
@sopel.module.rule(r"https?://[^/]*nitter[^/]+/(\S*)/status/(?P<id>\d+)")
def specific_tweet(bot, trigger):
    bearer = bot.db.get_plugin_value("twits", "bearer")
    if not bearer:
        return

    tweet_id = trigger.groupdict()["id"]
    tweet = get_tweet(tweet_id, bearer)

    write_twit(bot, tweet)
