import requests
import sopel.module


def get_quotes():
    tickers = requests.get(
        f"https://www.bitstamp.net/api/v2/ticker/", timeout=10
    ).json()

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

        texts.append("{pair}: {color}${last:,.02f}\x0f".format(color=color, **quote))

    tickers = " | ".join(texts)
    bot.say(f"Bitstamp - {tickers}")


"""
Quote format:

{
    'timestamp': '1678770697',
    'open': '24210',
    'high': '24800',
    'low': '21900',
    'last': '24796',
    'volume': '6198.52491590',
    'vwap': '23454',
    'bid': '24796',
    'ask': '24797',
    'open_24': '22447',
    'percent_change_24': '10.46',
    'pair': 'BTC/USD'
}

"""
