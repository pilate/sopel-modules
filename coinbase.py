import requests

import sopel.module



PAIRS = ["BTC-USD", "BCH-USD", "ETH-USD", "LTC-USD"]


def get_prices_coinbase():
    prices = []
    for pair in PAIRS:
        response = requests.get("https://api.coinbase.com/v2/prices/{0}/spot".format(pair), headers={
            "CB-VERSION": "2017-05-25"
        }).json()
        prices.append((pair, float(response["data"]["amount"])))
    return prices


def get_products_gdax():
    return requests.get("https://api.gdax.com/products").json()


def get_price_gdax(product_id):
    return requests.get("https://api.gdax.com/products/{0}/ticker".format(product_id)).json()


@sopel.module.rule("\\.?\\.(cr[yi]pto|co[ir]nbas?e)$")
@sopel.module.rule("\\.?\\.corn$")
def cb_lookup(bot, trigger):
    prices = get_prices_coinbase()

    texts = []
    for pair, price in prices:
        texts.append("{coin}: ${price:,}".format(coin=pair.split("-")[0], price=price))

    bot.say("Coinbase - {0}".format(", ".join(texts)))


@sopel.module.rule("\\.?\\.gd(ax)?e?$")
def gdax_lookup(bot, trigger):
    products = filter(lambda p: "USD" in p["id"], get_products_gdax())

    texts = []
    for product in reversed(products):
        price = get_price_gdax(product["id"])
        texts.append("{market}: ${price:,} ({volume:,})".format(
            market=product["id"], 
            price=float(price["price"]),
            volume=int(float(price["volume"]))))

    bot.say("GDAX - {0}".format(", ".join(texts)))