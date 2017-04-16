from pprint import pprint

import sopel.module
import requests



def get_data(symbol):
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
        return {}

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


def get_color(change):
    color = ""
    if change < 0:
        color = "\x0304"
    elif change > 0:
        color = "\x0309"
    return color


def write_ticker(bot, symbols):
    quotes = get_data("|".join(symbols))

    lines = []
    for quote in quotes:
        color = get_color(quote["change"])
        lines.append(TICKER_TPL.format(color=color, **quote))

    bot.say(" ".join(lines))


# > .. goog gps
# > GOOG (Alphabet Class C) Last: 738.634 -2.56 -0.3454% (Vol: 941322) Daily Range: (735.831-741.69) Yearly Range: (556.79-789.87)
# > GPS (Gap Inc) Last: 26.899 +1.01 +3.90% (Vol: 17584490) Daily Range: (25.70-26.94) Yearly Range: (17-34.53) PostMkt 26.884 -0.01 -0.0372% (Vol: 11066)

PRICE_TPL = "{last} {color}{change:+} {change_pct:+}%\x0f (Vol: {volume})"
PRICE_TPL_NV = "{last} {color}{change:+} {change_pct:+}%\x0f"

@sopel.module.rule("\\.\\. ((?:(?:[^ ]+) ?)+)")
def symbol_lookup(bot, trigger):
    raw_symbols = trigger.group(1)

    split_symbols = map(lambda s: s.strip(), raw_symbols.split(" "))[:4]

    quotes = get_data("|".join(split_symbols))

    for quote in quotes:
        color = get_color(quote["change"])

        if "volume" in quote:
            price_line = PRICE_TPL.format(color=color, **quote)
        else:
            price_line = PRICE_TPL_NV.format(color=color, **quote)

        response = "{symbol} ({full_name}) Last: {price} Daily Range: ({low}-{high}) 52-Week Range: ({ylow}-{yhigh})".format(
            symbol=quote["symbol"],
            full_name=quote["name"],
            price=price_line,
            low=quote["low"],
            high=quote["high"],
            yhigh=quote["FundamentalData"]["yrhiprice"],
            ylow=quote["FundamentalData"]["yrloprice"]
        )

        bot.say(response)


# > .fx
# > (EURUSD 1.13269 +0.0001 +0.01%) (GBPUSD 1.30734 -0.0001 -0.0076%) (USDJPY 100.209 +0.33 +0.33%) (USDCHF 0.96054 -0.0004 -0.0416%) (AUDUSD 0.76259 +0.0001 +0.01%) (USDCAD 1.28694 -0.0001 -0.0078%) (NZDUSD 0.72774 -0.0013 -0.1786%) (EURJPY 113.499 +0.01 +0.01%) (EURCHF 1.08794 -0.0003 -0.0276%) (EURGBP 0.866 0.00 0.00%)
@sopel.module.rule("\\.?\\.f(ore)?x$")
def forex_lookup(bot, trigger):
    write_ticker(bot, ["EUR=", "GBP=", "JPY=", "CHF=", "AUD=", "USDCAD", "NZD=", "EURJPY=", "EURCHF=", "EURGBP="])


# > .b
# > 2y: 1.262%4 -0.005 -0.4% 5y: 1.905%4 -0.007 -0.37% 10y: 2.362%4 -0.011 -0.47% 30y: 2.967%4 -0.012 -0.4%
@sopel.module.rule("\\.?\\.b")
def treasury_lookup(bot, trigger):
    write_ticker(bot, ["US2Y", "US5Y", "US10Y", "US30Y"])


# > .rtcom
# > Crude: 48.50 9+0.28 (9+0.58%) Gold: 1,345.30 4-11.90 (4-0.88%) Silver: 19.288 4-0.452 (4-2.29%) NatGas: 2.575 4-0.099 (4-3.70%)
@sopel.module.rule("\\.?\\.rtc[ou]m$")
def com_lookup(bot, trigger):
    write_ticker(bot, ["@CL.1", "@GC.1", "@SI.1", "@NG.1"])


# > .fus
# > DOW: 20,623.0 4-37.0 (4-0.18%) SP: 2,362.00 4-2.50 (4-0.11%) NQ100: 5,441.38 9+3.88 (9+0.07%) R2K: 1,380.2 4-1.1 (4-0.08%)
@sopel.module.rule("\\.?\\.fus$")
def fus_lookup(bot, trigger):
    write_ticker(bot, ["@DJ.1", "@SP.1", "@NQ.1"])


# > .us
# > DOW: 20721.029 +170.04 +0.83%  S&P: 2361.609 +20.01 +0.85%  Nasdaq: 5882.939 +42.56 +0.73%  R2K: 1364.039 +6.71 +0.49%
@sopel.module.rule("\\.?\\.us$")
def us_lookup(bot, trigger):
    write_ticker(bot, [".DJI", ".SPX", ".IXIC", ".NDX"])


# > .ca
# > S&P/TSX: 14,559.85 4-5.98 (4-0.04%)
@sopel.module.rule("\\.?\\.ca$")
@sopel.module.rule("\\.?\\.eh$")
def ca_lookup(bot, trigger):
    write_ticker(bot, [".GSPTSE"])


# > .eu
# > DAX: 10,986.69 9+211.37 (9+1.96%) FTSE: 6,902.23 9+122.39 (9+1.81%) CAC: 4,694.72 9+62.78 (9+1.36%)
@sopel.module.rule("\\.?\\.eu$")
def eu_lookup(bot, trigger):
    write_ticker(bot, [".GDAXI", ".FTSE", ".FCHI"])


# > .asia
# > Nikkei: 18,975.50 9+210.03 (9+1.12%) HSI: 22,752.00 4-109.84 (4-0.48%) Shanghai:  9 (9) SSEC: .SSEC (Shanghai) Last: 3223.379 +8.00 +0.25% (Vol: 68264) Daily Range: (3207.04-3228.92) Yearly Range: (2638.3-3684.57)
@sopel.module.rule("\\.?\\.asia$")
def asia_lookup(bot, trigger):
    write_ticker(bot, [".N225", ".HSI", ".SSEC"])
