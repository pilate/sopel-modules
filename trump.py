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
    fixed = tweet.replace("pic.twitter.com/", " https://pic.twitter.com/")

    return fixed


@sopel.module.rule("\\.?\\.trump$")
def last_tweet(bot, trigger):
    try:
        tweet = get_last_tweet("realDonaldTrump")
    except:
        return

    bot.say(tweet)