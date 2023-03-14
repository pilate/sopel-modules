import requests
import sopel.module


PAIRS = ["BTC-USD", "BCH-USD", "ETH-USD", "ETC-USD", "LTC-USD"]


def get_prices_coinbase():
    prices = []
    for pair in PAIRS:
        response = requests.get(
            f"https://api.coinbase.com/v2/prices/{pair}/spot",
            timeout=10,
        ).json()
        prices.append((pair, float(response["data"]["amount"])))
    return prices


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
        coin = pair.split("-")[0]
        texts.append(f"{coin}: ${price:,}")

    tickers = " | ".join(texts)
    bot.say(f"Coinbase - {tickers}")


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
    tickers = " | ".join(texts)
    bot.say(f"Coinbase Pro - {tickers}")
