import requests

import sopel.module



def get_quotes(listed=True):
    response = requests.get("https://api.bithumb.com/public/ticker/ALL").json()
    if response["status"] != "0000":
        return []

    list_data = []
    data = response["data"]
    del data["date"]
    for coin, values in data.iteritems():
        for key, value in values.iteritems():
            values[key] = float(value)
        values["symbol"] = coin
        list_data.append(values)

    if listed:
        list_data.sort(key=lambda l: l["buy_price"], reverse=True)
        return list_data
    return data


def get_exchange():
    rates = requests.get("https://www.bithumb.com/resources/csv/CurrencyRate.json").json()
    currencies = {}
    for rate in rates:
        currencies[rate["Currency"]] = float(rate["Rate"])
    return currencies


def price_fix(quote, exchange, to="USD"):
    for key, value in quote.items():
        if key.endswith("_price"):
            quote[key] = value / exchange[to]


def make_line_simple(quotes, exchange, symbols):
    lines = []

    for quote in quotes:
        if quote["symbol"] not in symbols:
            continue
        price_fix(quote, exchange)
        lines.append("{symbol}: ${closing_price:,.02f}".format(**quote))

    return ", ".join(lines)


TEMPLATE = "{symbol} - ${closing_price:,.02f} (Buy: ${buy_price:,.02f}) (Sell: ${sell_price:,.02f}) (24h Volume: {volume_1day:,.02f}) (24h Range: {min_price:,.02f}-{max_price:,.02f})"
def make_line_complex(symbol, quote, exchange):
    price_fix(quote, exchange)
    return TEMPLATE.format(**quote)


@sopel.module.rule("\\.?\\.bth$")
@sopel.module.rule("\\.?\\.(bit)?t?humb$")
def thumb_lookup(bot, trigger):
    quotes = get_quotes()
    exchange = get_exchange()
    response = make_line_simple(quotes, exchange, ["BTC", "ETH", "DASH", "LTC", "BCH"])
    bot.say("bithumb - {0}".format(response))


@sopel.module.rule("\\.?\\.bth ((?:(?:[^ ]+) ?)+)$")
@sopel.module.rule("\\.?\\.(?:bit)?t?humb ((?:(?:[^ ]+) ?)+)$")
def thumb_lookup_each(bot, trigger):
    quotes = get_quotes(listed=False)
    exchange = get_exchange()
    
    raw = trigger.group(1)
    symbols = map(lambda s: s.strip().upper(), raw.split())[:4]
    for symbol in symbols:
        if symbol not in quotes:
            continue
        bot.say(make_line_complex(symbol, quotes[symbol], exchange))


"""
Quote format:

"BTC": {
    "opening_price": "11781000",
    "closing_price": "12703000",
    "min_price": "11649000",
    "max_price": "13624000",
    "average_price": "12702694.9755",
    "units_traded": "70069.14538508",
    "volume_1day": "70069.14538508",
    "volume_7day": "285853.74509918",
    "buy_price": "12718000",
    "sell_price": "12729000"
}
"""