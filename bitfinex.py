import requests
import sopel.module


FIELDS = [
    "bid",
    "bid_size",
    "ask",
    "ask_size",
    "daily_change",
    "daily_change_relative",
    "last_price",
    "volume",
    "high",
    "low",
]


def get_quotes():
    response = requests.get(
        "https://api-pub.bitfinex.com/v2/tickers?symbols=ALL", timeout=10
    ).json()

    quotes = {}
    for values in response:
        if len(quotes) == 20:
            break

        if not values[0].endswith("USD"):
            continue

        symbol = values.pop(0)[1:-3]
        quote = dict(zip(FIELDS, map(float, values)))
        quotes[symbol] = quote

    return quotes


@sopel.module.rule("\\.?\\.bfx$")
@sopel.module.rule("\\.?\\.(bit)?finex$")
def bitfinex_lookup(bot, _):
    quotes = get_quotes()

    texts = []
    for symbol, quote in quotes.items():
        price = quote["last_price"]

        color = ""
        if quote["daily_change"] > 0:
            color = "\x0309"

        if quote["daily_change"] < 0:
            color = "\x0304"

        texts.append(f"{symbol}: {color}${price:,.02f}\x0f")

    tickers = " | ".join(texts)
    bot.say(f"Bitfinex - {tickers}")
