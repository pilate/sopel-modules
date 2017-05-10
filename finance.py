from pprint import pprint

import sopel.module
import re
import requests


def retry(times=10):
    def wrap(function):
        def f(*args, **kwargs):
            attempts = 0
            while attempts < times:
                try:
                    return function(*args, **kwargs)
                except:
                    attempts += 1
            raise Exception("Retry limit exceeded")
        return f
    return wrap


@retry(times=10)
def get_data_cnbc(symbol):
    response = requests.post("http://quote.cnbc.com/quote-html-webservice/quote.htm", data={
            "symbols": symbol,
            "symbolType": "symbol",
            "requestMethod": "quick",
            "realtime": "1",
            "extended": "1",
            "exthrs": "1",
            "extmode": "ALL",
            "fund": "1",
            "events": "0",
            "entitlement": "1",
            "skipcache": "0",
            "extendedMask": "2",
            "partnerId": "2",
            "output": "json",
            "noform": 1
        })

    if response.status_code != 200:
        return []

    quotes = response.json()["QuickQuoteResult"]["QuickQuote"]

    # Always return a list
    if type(quotes) != list:
        quotes = [quotes]

    # Remove invalid symbols
    quotes = filter(lambda q: "last" in q, quotes)

    for quote in quotes:
        for key in ["change", "change_pct", "last", "open", "previous_day_closing"]:
            quote[key] = float(quote[key])

        if "ExtendedMktQuote" in quote:
            for key in ["change", "change_pct", "last"]:
                quote["ExtendedMktQuote"][key] = float(quote["ExtendedMktQuote"][key])

    return quotes


@retry(times=10)
def get_data_yahoo(symbol):
    response = requests.get("https://query.yahooapis.com/v1/public/yql", params={
            "q": "select * from yahoo.finance.quotes where symbol in ('{}')".format(symbol),
            "format": "json",
            "env": "store://datatables.org/alltableswithkeys"
        })

    if response.status_code != 200:
        return {}

    return response.json()["query"]["results"]["quote"]


def get_color(change):
    color = ""
    if change < 0:
        color = "\x0304"
    elif change > 0:
        color = "\x0309"
    return color


TICKER_TPL = "({shortName} {last} {color}{change:+} {change_pct:+}%\x0f)"
def write_ticker(bot, symbols):
    quotes = get_data_cnbc("|".join(symbols))

    lines = []
    for quote in quotes:
        color = get_color(quote["change"])
        lines.append(TICKER_TPL.format(color=color, **quote))

    bot.say(" ".join(lines))


PRICE_TPL = "{last} {color}{change:+} {change_pct:+}%\x0f (Vol: {volume})"
PRICE_TPL_NV = "{last} {color}{change:+} {change_pct:+}%\x0f"

@sopel.module.rule("\\.\\. ((?:(?:[^ ]+) ?)+)")
def symbol_lookup(bot, trigger):
    raw_symbols = trigger.group(1)

    split_symbols = map(lambda s: s.strip(), raw_symbols.split(" "))[:4]

    quotes = get_data_cnbc("|".join(split_symbols))

    for quote in quotes:
        color = get_color(quote["change"])

        if "volume" in quote:
            price_line = PRICE_TPL.format(color=color, **quote)
        else:
            price_line = PRICE_TPL_NV.format(color=color, **quote)

        response = "{symbol} ({full_name}) Last: {price} Daily Range: ({low}-{high})".format(
            symbol=quote["symbol"],
            full_name=quote["name"],
            price=price_line,
            low=quote["low"],
            high=quote["high"])

        if ("FundamentalData" in quote) and quote["FundamentalData"]:
            response += " 52-Week Range: ({ylow}-{yhigh})".format(
                yhigh=quote["FundamentalData"]["yrhiprice"],
                ylow=quote["FundamentalData"]["yrloprice"])

        if quote["curmktstatus"] != "REG_MKT":
            if ("ExtendedMktQuote" in quote) and quote["ExtendedMktQuote"]["change"]:
                ah_color = get_color(quote["ExtendedMktQuote"]["change"])
                response += " Postmkt: " + PRICE_TPL.format(color=ah_color, **quote["ExtendedMktQuote"])

        bot.say(response)


SYMBOL_MAP = {
    "f(ore)?x": ["EUR=", "GBP=", "JPY=", "CHF=", "AUD=", "USDCAD", "NZD=", "EURJPY=", "EURCHF=", "EURGBP="],
    "b": ["US2Y", "US5Y", "US10Y", "US30Y"],
    "rtc[ou]m": ["@CL.1", "@GC.1", "@SI.1", "@NG.1"],
    "us": [".DJI", ".SPX", ".IXIC", ".NDX"],
    "fus": ["@DJ.1", "@SP.1", "@NQ.1"],
    "(ca|eh)": [".GSPTSE"],
    "eu": [".GDAXI", ".FTSE", ".FCHI"],
    "asia": [".N225", ".HSI", ".SSEC"]
}

TRIGGERS = "|".join(SYMBOL_MAP.keys())
@sopel.module.rule("\\.?\\.({0})$".format(TRIGGERS))
def zag_lookup(bot, trigger):
    user_trigger = trigger.group(1).lower()

    if user_trigger in SYMBOL_MAP:
        symbols = SYMBOL_MAP[user_trigger]

    else:
        for symbol in SYMBOL_MAP.keys():
            if re.search(symbol + "$", user_trigger):
                symbols = SYMBOL_MAP[symbol]
                break

    write_ticker(bot, symbols)


@sopel.module.rule("\\.\\.fun ([^ ]+)")
def fun_lookup(bot, trigger):
    raw_symbol = trigger.group(1)

    data = get_data_yahoo(raw_symbol)
    
    if data["Name"] is None:
        return

    bot.say(
        "{symbol} ({Name}) - {LastTradePriceOnly} " \
        "(EPS: {EarningsShare}) " \
        "(P/E: {PERatio}) " \
        "(FP/E: {PriceEPSEstimateNextYear}) " \
        "(P/S: {PriceSales}) " \
        "(P/B: {PriceBook}) " \
        "(BV: {BookValue}) " \
        "(50MA: {FiftydayMovingAverage}) " \
        "(200MA: {TwoHundreddayMovingAverage}) " \
        "(Market Cap: {MarketCapitalization}) " \
        "(Short Ratio: {ShortRatio})".format(**data))
