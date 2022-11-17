#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pprint import pprint
import json
import os
import re
import time

import sopel.module
import requests


def retry(times=10):
    def wrap(function):
        def f(*args, **kwargs):
            attempts = 0
            while attempts < times:
                try:
                    return function(*args, **kwargs)
                except:
                    time.sleep(1)
                    attempts += 1
            raise Exception("Retry limit exceeded")
        return f
    return wrap


@retry(times=10)
def get_data_cnbc(symbol):
    response = requests.get("https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol", params={
            "symbols": symbol,
            "requestMethod": "itv",
            "exthrs": "1",
            "extmode": "ALL",
            "fund": "1",
            "events": "0",
            "partnerId": "2",
            "output": "json",
            "noform": 1
        },
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate"
        })

    if response.status_code != 200:
        return []

    quotes = response.json()["FormattedQuoteResult"]["FormattedQuote"]

    # Always return a list
    if type(quotes) != list:
        quotes = [quotes]

    # Remove invalid symbols
    quotes = filter(lambda q: "last" in q, quotes)

    for quote in quotes:
        for key in ["change", "change_pct", "last", "open", "previous_day_closing"]:
            if key not in quote:
                quote[key] = 0
            else:
                no_pct = quote[key].rstrip("%").replace(",", "")
                quote[key] = float(no_pct)


        # print(json.dumps(quote))
        if "ExtendedMktQuote" in quote:
            for key in ["change", "change_pct", "last", "volume", "mktcap"]:
                if key not in quote["ExtendedMktQuote"]:
                    quote["ExtendedMktQuote"][key] = "0.0"

                no_pct = quote["ExtendedMktQuote"][key].rstrip("%").replace(",", "")
                quote["ExtendedMktQuote"][key] = float(no_pct or 0.0)

    return quotes


@retry(times=10)
def get_data_yahoo(symbols):
    in_str = ", ".join(map(lambda s: "'{0}'".format(s), symbols))
    response = requests.get("https://query.yahooapis.com/v1/public/yql", params={
            "q": "select * from yahoo.finance.quotes where symbol in ({0})".format(in_str),
            "format": "json",
            "env": "store://datatables.org/alltableswithkeys"
        })

    if response.status_code != 200:
        return {}

    quotes = response.json()["query"]["results"]["quote"]
    if type(quotes) != list:
        return [quotes]

    return quotes


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

@sopel.module.rule(r"\.\. ((?:(?:[^ ]+)\s*)+)")
def symbol_lookup(bot, trigger):
    raw_symbols = trigger.group(1)

    split_symbols = map(lambda s: s.strip(), re.split(r"\s+", raw_symbols))[:4]

    try:
        quotes = get_data_cnbc("|".join(split_symbols))
    except Exception as e:
        bot.say("Error retrieving data")
        return

    for quote in quotes:
        color = get_color(quote["change"])

        if "volume" in quote:
            price_line = PRICE_TPL.format(color=color, **quote)
        else:
            price_line = PRICE_TPL_NV.format(color=color, **quote)

        response = "{symbol} ({full_name}) Last: {price} | Daily Range: {low}-{high}".format(
            symbol=quote["symbol"],
            full_name=quote["name"],
            price=price_line,
            low=quote["low"],
            high=quote["high"])

        if ("FundamentalData" in quote) and quote["FundamentalData"]:
            fundies = quote["FundamentalData"]
            response += " | 52-Week Range: {ylow}-{yhigh} | Cap: ${mktcap:,}".format(
                yhigh=fundies["yrhiprice"],
                ylow=fundies["yrloprice"],
                mktcap=int(float(fundies.get("mktcap", "0"))))
            if fundies.get("dividend", '0') != '0':
                response += " | Dividend: {0}".format(
                    round(float(fundies["dividend"]), 3))
                if "dividendyield" in fundies:
                    response += " ({0}%)".format(round(float(fundies["dividendyield"]), 3))

        if quote["curmktstatus"] != "REG_MKT":
            if ("ExtendedMktQuote" in quote) and quote["ExtendedMktQuote"]["change"]:
                ah_color = get_color(quote["ExtendedMktQuote"]["change"])
                response += " | Postmkt: " + PRICE_TPL.format(color=ah_color, **quote["ExtendedMktQuote"])

        bot.say(response)


SYMBOL_MAP = {
    "f(ore)?x": ["EUR=", "GBP=", "JPY=", "CHF=", "AUD=", "USDCAD", "NZD=", "EURJPY=", "EURCHF=", "EURGBP=", "CADUSD=", "CNYUSD=", "RUB="],
    "b": ["US2Y", "US5Y", "US7Y", "US10Y", "US30Y"],
    "rtc[ou]m": ["@CL.1", "@HG.1", "@SI.1", "@GC.1", "@NG.1"],
    "us": [".DJI", ".SPX", ".IXIC", ".NDX", ".RUT"],
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


@sopel.module.rule("\\.?\\.fun ((?:(?:[^ ]+) ?)+)$")
def fun_lookup(bot, trigger):
    raw_symbols = trigger.group(1)

    split_symbols = map(lambda s: s.strip(), raw_symbols.split(" "))[:4]

    data = get_data_yahoo(split_symbols)

    for row in data:
        if row["Name"] is None:
            continue

        row["symbol"] = row["symbol"].upper()

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
            "(Short Ratio: {ShortRatio})".format(**row))


ALII = "$alii.json"
if os.path.exists(ALII):
    ALII = json.load(open("$alii.json", "r"))
else:
    ALII = {}

@sopel.module.rule(r"\$alias ([^ ]+) ((?:(?:[^ ]+)\s*)+)")
def alias_add(bot, trigger):
    alias = trigger.group(1)
    if alias == "alias":
        bot.say("Nope!")

    # if alias in ALII:
    #     bot.say("Alias {0} in use!".format(alias))
    #     return

    raw_symbols = trigger.group(2)
    split_symbols = map(lambda s: s.strip(), re.split(r"\s+", raw_symbols))[:10]
    ALII[alias] = split_symbols

    bot.say("Alias ${0} set to: {1} 🚀🚀🚀".format(alias, ", ".join(split_symbols)))
    json.dump(ALII, open("$alii.json", "w+"))


@sopel.module.rule(r"\$([^ ]+)")
def alias_use(bot, trigger):
    alias = trigger.group(1)
    if alias == "alias":
        return

    if alias not in ALII:
        return

    write_ticker(bot, ALII[alias])
