import requests

import sopel.module



PAIRS = ["BTC-USD", "ETH-USD", "LTC-USD"]


def get_prices():
    prices = []
    for pair in PAIRS:
        response = requests.get("https://api.coinbase.com/v2/prices/{0}/spot".format(pair)).json()
        prices.append((pair, response["data"]["amount"]))
    return prices


@sopel.module.rule("\\.?\\.(cr[yi]pto|coinbase)$")
def game_lookup(bot, trigger):
    prices = get_prices()

    texts = []
    for pair, price in prices:
        texts.append("{coin}: ${price}".format(coin=pair.split("-")[0], price=price))

    bot.say("Coinbase - {0}".format(", ".join(texts)))