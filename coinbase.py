import requests
import sopel.module
from cachetools import TTLCache, cached


PAIRS = ["BTC-USD", "BCH-USD", "ETH-USD", "ETC-USD", "LTC-USD"]


@cached(TTLCache(100, ttl=60 * 5))
def get_prices_coinbase():
    prices = []
    for pair in PAIRS:
        response = requests.get(
            f"https://api.coinbase.com/v2/prices/{pair}/spot",
            timeout=10,
        ).json()
        prices.append((pair, float(response["data"]["amount"])))
    return prices


@cached(TTLCache(100, ttl=60 * 5))
def get_price_gdax(product_id):
    return requests.get(
        f"https://api.pro.coinbase.com/products/{product_id}/ticker", timeout=10
    ).json()


@sopel.module.rule("\\.?\\.(cr[yi]pto|co[ir]nbas?e)$")
@sopel.module.rule("\\.?\\.corn$")
def cb_lookup(bot, _):
    prices = get_prices_coinbase()

    texts = []
    for pair, price in prices:
        texts.append("{coin}: ${price:,}".format(coin=pair.split("-")[0], price=price))

    bot.say("Coinbase - {0}".format(", ".join(texts)))


@sopel.module.rule("\\.?\\.gd(ax)?e?$")
@sopel.module.rule("\\.?\\.(cbp|pro)$")
def gdax_lookup(bot, _):
    texts = []
    for product in PAIRS:
        price = get_price_gdax(product)
        texts.append(
            "{market}: ${price:,} ({volume:,})".format(
                market=product,
                price=float(price["price"]),
                volume=int(float(price["volume"])),
            )
        )
    tickers = ", ".join(texts)
    bot.say(f"Coinbase Pro - {tickers}")
