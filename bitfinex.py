import multiprocessing

import requests

import sopel.module



def get_symbols():
    return requests.get("https://api.bitfinex.com/v1/symbols").json()


def get_ticker(symbol):
    return (symbol, requests.get("https://api.bitfinex.com/v1/pubticker/{0}".format(symbol)).json())


def get_tickers(symbols):
    return map(get_ticker, symbols)


@sopel.module.rule("\\.?\\.bfx$")
@sopel.module.rule("\\.?\\.(bit)?finex$")
def bitfinex_lookup(bot, trigger):
    tickers = get_tickers(["btcusd", "ethusd", "ltcusd", "etcusd",  "btgusd"])

    texts = []
    for symbol, ticker in tickers:
        texts.append("{market}: ${price:,.02f}".format(
            market=symbol.upper(),
            price=float(ticker["last_price"])))

    bot.say("Bitfinex - {0}".format(", ".join(texts)))