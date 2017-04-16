import sopel.module
import requests



def get_data(phrase):
    return requests.get("http://api.urbandictionary.com/v0/define", params={"term":phrase}).json()


@sopel.module.rule("\\.u (.+)")
def phrase_lookup(bot, trigger):
    phrase = trigger.group(1)
    results = get_data(phrase)
    if not results.get("list"):
        return

    bot.say(results["list"][0]["definition"])
