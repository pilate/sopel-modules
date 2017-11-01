import multiprocessing

import requests

import sopel.module



def get_symbols():
    return requests.get("https://api.bitfinex.com/v1/symbols").json()


def get_ticker(symbol):
    return (symbol, requests.get("https://api.bitfinex.com/v1/pubticker/{0}".format(symbol)).json())


def get_tickers(symbols):
    pool = multiprocessing.Pool(len(symbols))
    return pool.map(get_ticker, symbols)


@sopel.module.rule("\\.?\\.bfx$")
@sopel.module.rule("\\.?\\.bitfinex$")
def bitfinex_lookup(bot, trigger):
    symbols = filter(lambda p: p.endswith("usd"), get_symbols())
    tickers = get_tickers(symbols)

    texts = []
    for symbol, ticker in tickers:
        texts.append("{market}: ${price:,}".format(
            market=symbol, 
            price=float(ticker["last_price"])))

    bot.say("Bitfinex - {0}".format(", ".join(texts)))