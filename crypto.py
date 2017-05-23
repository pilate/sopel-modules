import requests

import sopel.module



def get_prices():
    return requests.get("https://api.coinmarketcap.com/v1/ticker/").json()


@sopel.module.rule("\\.?\\.(shit|tard)coins?$")
def game_lookup(bot, trigger):
    prices = get_prices()

    coin_to_price = {}
    for price in prices:
        coin_to_price[price["name"]] = price

    top_10 = map(lambda p: p["name"], prices[:10]) + ["HoboNickels"]

    output = []
    for coin in top_10:
        output.append("({name} - ${price_usd})".format(**coin_to_price[coin]))

    bot.say(" ".join(output))