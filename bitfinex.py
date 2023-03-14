import requests
import sopel.module


def get_symbols():
    return requests.get("https://api.bitfinex.com/v1/symbols", timeout=10).json()


def get_ticker(symbol):
    response = requests.get(
        f"https://api.bitfinex.com/v1/pubticker/{symbol}", timeout=10
    ).json()
    return (symbol, response)


def get_tickers(symbols):
    return map(get_ticker, symbols)


@sopel.module.rule("\\.?\\.bfx$")
@sopel.module.rule("\\.?\\.(bit)?finex$")
def bitfinex_lookup(bot, _):
    tickers = get_tickers(["btcusd", "ethusd", "ltcusd", "etcusd", "btgusd"])

    texts = []
    for symbol, ticker in tickers:
        price = float(ticker["last_price"])
        texts.append(f"{symbol.upper()}: ${price:,.02f}")

    tickers = ", ".join(texts)
    bot.say(f"Bitfinex - {tickers}")
