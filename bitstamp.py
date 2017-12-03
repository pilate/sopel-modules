import requests

import sopel.module



def get_pairs():
    return requests.get("https://www.bitstamp.net/api/v2/trading-pairs-info/").json()


def get_ticker(pair):
    return requests.get("https://www.bitstamp.net/api/v2/ticker/{0}/".format(pair)).json()


@sopel.module.rule("\\.?\\.(bit)?stamp$")
@sopel.module.rule("\\.?\\.bs$")
def bitstamp_lookup(bot, trigger):
    pairs = get_pairs()
    pairs = filter(lambda p: "USD" in p["name"], pairs)

    quotes = []
    for pair in pairs:
        quote = get_ticker(pair["url_symbol"])
        quote["pair"] = pair
        quotes.append(quote)
    quotes.sort(key=lambda p: float(p["last"]), reverse=True)  

    texts = []
    for quote in quotes:
        texts.append("{market}: ${price:,.02f}".format(
            market=quote["pair"]["name"],
            price=float(quote["last"])))

    bot.say("Bitstamp - {0}".format(", ".join(texts)))


"""
Quote format:

{
    "high": "11082.00",
    "last": "11044.46",
    "timestamp": "1512179547",
    "bid": "11044.63",
    "vwap": "10362.04",
    "volume": "16730.31545647",
    "low": "9370.11",
    "ask": "11057.98",
    "open": "10840.45"
}
"""