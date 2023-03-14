import requests
import sopel.module


def get_quotes():
    tickers = requests.get("https://www.bitstamp.net/api/v2/ticker/", timeout=10).json()

    usd_quotes = list(filter(lambda t: t["pair"].endswith("/USD"), tickers))

    for quote in usd_quotes:
        quote["open"] = float(quote["open"])
        quote["last"] = float(quote["last"])

    return usd_quotes[:20]


@sopel.module.rule("\\.?\\.(bit)?stamp$")
@sopel.module.rule("\\.?\\.bs$")
def bitstamp_lookup(bot, _):
    quotes = get_quotes()

    texts = []
    for quote in quotes:
        if quote["last"] > float(quote["open_24"]):
            color = "\x0309"
        elif quote["last"] < float(quote["open_24"]):
            color = "\x0304"
        else:
            color = ""

        symbol = quote["pair"].rsplit("/")[0]
        texts.append("{symbol}: {color}${last:,.02f}\x0f".format(symbol=symbol, color=color, **quote))

    tickers = " | ".join(texts)
    bot.say(f"Bitstamp - {tickers}")
