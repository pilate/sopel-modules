import sopel.module
import requests


def get_data(phrase):
    return requests.get(
        "http://api.urbandictionary.com/v0/define", params={"term": phrase}, timeout=10
    ).json()


@sopel.module.rule("\\.?\\.u (.+)")
def phrase_lookup(bot, trigger):
    phrase = trigger.group(1)
    results = get_data(phrase)

    if not results.get("list"):
        return

    if phrase.lower() in [
        "suki (tm)",
        "suki(tm)",
        "the new world religion (tm)",
        "the new world religion(tm)",
    ]:
        bot.say("RIP Pitz")
        return

    if phrase.lower() in [
        "vip (tm)",
        "vip(tm)",
        "superelite",
        "superelite(tm)",
        "superelite (tm)",
    ]:
        bot.say("RIP Pitz")
        return

    if phrase.lower() in ["profit (tm)", "profit(tm)"]:
        bot.say("RIP Pitz")
        return

    bot.say(results["list"][0]["definition"])
