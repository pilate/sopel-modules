import xml.etree.ElementTree as ElementTree

import sopel.module
import requests



def get_last_tweet(user):
    result = requests.get("https://twitrss.me/twitter_user_to_rss/", params={
        "user": user,
        "replies": "on"
    })

    root = ElementTree.fromstring(result.content)
    tweet = root.find("./channel/item/title").text
    fixed = tweet.replace("pic.twitter.com/", " https://pic.twitter.com/").replace("\n", " ")

    return fixed


def write_twit(bot, tweeter):
    try:
        tweet = get_last_tweet(tweeter)
    except Exception as e:
        return

    bot.say(u"@{0}: {1}".format(tweeter, tweet))


@sopel.module.rule("\\.?\\.tweet ([^ ]+)$")
def last_tweet(bot, trigger):
    tweeter = trigger.group(1).strip()
    write_twit(bot, tweeter)


@sopel.module.rule("\\.?\\.trump$")
def trump_tweet(bot, trigger):
    write_twit(bot, "realDonaldTrump")
