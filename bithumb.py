import requests
import sopel.module


SHORT_TPL = "{symbol}: {color}${closing_price:,.02f}\x0f"
LONG_TPL = (
    SHORT_TPL
    + " (24h Volume: {units_traded_24H:,.02f}) (24h Range: {min_price:,.02f}-{max_price:,.02f})"
)


def get_exchange():
    rates = requests.get(
        "https://gw.bithumb.com/exchange/v1/comn/exrate", timeout=10
    ).json()

    for rate in rates["data"]["currencyRateList"]:
        if rate["currency"] == "USD":
            return rate["rate"]


def get_quotes():
    response = requests.get(
        "https://api.bithumb.com/public/ticker/ALL",
        headers={"accept": "application/json"},
        timeout=10,
    ).json()

    exchange_rate = get_exchange()
    for symbol, quote in response["data"].items():
        if symbol == "date":
            continue

        for key, value in quote.items():
            if key.endswith("_price"):
                quote[key] = float(value) / exchange_rate
            else:
                quote[key] = float(value)

    return response["data"]


def get_color(quote):
    if quote["closing_price"] > float(quote["opening_price"]):
        return "\x0309"

    if quote["closing_price"] < float(quote["opening_price"]):
        return "\x0304"

    return ""


def make_line_simple(quotes, symbols):
    lines = []
    for symbol in symbols:
        if quote := quotes.get(symbol):
            lines.append(
                SHORT_TPL.format(symbol=symbol, color=get_color(quote), **quote)
            )

    return " | ".join(lines)


def make_line_complex(symbol, quote):
    return LONG_TPL.format(symbol=symbol, color=get_color(quote), **quote)


@sopel.module.rule("\\.?\\.bth$")
@sopel.module.rule("\\.?\\.(bit)?t?humb$")
def thumb_lookup(bot, _):
    quotes = get_quotes()

    response = make_line_simple(quotes, list(quotes.keys())[:10])
    bot.say("bithumb - {0}".format(response))


@sopel.module.rule("\\.?\\.bth ((?:(?:[^ ]+) ?)+)$")
@sopel.module.rule("\\.?\\.(?:bit)?t?humb ((?:(?:[^ ]+) ?)+)$")
def thumb_lookup_each(bot, trigger):
    quotes = get_quotes()

    raw = trigger.group(1)
    symbols = map(lambda s: s.strip().upper(), raw.split())
    for symbol in list(symbols)[:4]:
        if symbol not in quotes:
            continue
        bot.say(make_line_complex(symbol, quotes[symbol]))
