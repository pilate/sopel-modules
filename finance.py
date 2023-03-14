#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import re
import time
from pprint import pprint

import requests
import sopel.module


TICKER_TPL = "({shortName} {last} {color}{change} {change_pct}\x0f)"
SINGLE_TPL = "{symbol} ({name}) Last: {price} | Daily Range: {low}-{high} | 52-Week Range: {yrloprice}-{yrhiprice}"
PRICE_TPL = "{last} {color}{change} {change_pct}\x0f (Vol: {volume})"
PRICE_TPL_NV = "{last} {color}{change} {change_pct}\x0f"

SYMBOL_MAP = {
    "f(ore)?x": [
        "EUR=",
        "GBP=",
        "JPY=",
        "CHF=",
        "AUD=",
        "USDCAD",
        "NZD=",
        "EURJPY=",
        "EURCHF=",
        "EURGBP=",
        "CADUSD=",
        "CNYUSD=",
        "RUB=",
    ],
    "b": ["US2Y", "US5Y", "US7Y", "US10Y", "US30Y"],
    "rtc[ou]m": ["@CL.1", "@HG.1", "@SI.1", "@GC.1", "@NG.1"],
    "us": [".DJI", ".SPX", ".IXIC", ".NDX", ".RUT"],
    "fus": ["@DJ.1", "@SP.1", "@ND.1"],
    "(ca|eh)": [".GSPTSE"],
    "eu": [".GDAXI", ".FTSE", ".FCHI"],
    "asia": [".N225", ".HSI", ".SSEC"],
}

TRIGGERS = "|".join(SYMBOL_MAP.keys())

ALII = "$alii.json"
if os.path.exists(ALII):
    ALII = json.load(open("$alii.json", "r"))
else:
    ALII = {}


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
    if isinstance(symbol, list):
        symbol = "|".join(symbol)

    response = requests.get(
        "https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol",
        params={
            "symbols": symbol,
            "requestMethod": "itv",
            "exthrs": "1",
            "extmode": "ALL",
            "fund": "1",
            "events": "0",
            "partnerId": "2",
            "output": "json",
            "noform": 1,
        },
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )

    if response.status_code != 200:
        return []

    quotes = response.json()["FormattedQuoteResult"]["FormattedQuote"]

    # Always return a list
    if not isinstance(quotes, list):
        quotes = [quotes]

    # Remove symbols with no data
    quotes = list(filter(lambda q: "last" in q, quotes))

    for quote in quotes:
        for key, value in quote.items():
            if value == "UNCH":
                quote[key] = "0"

    return quotes


def get_color(change):
    if change.startswith("-"):
        return "\x0304"
    elif change.startswith("+"):
        return "\x0309"
    return ""


def write_ticker(bot, symbols):
    quotes = get_data_cnbc("|".join(symbols))

    lines = []
    for quote in quotes:
        color = get_color(quote["change"])
        lines.append(TICKER_TPL.format(color=color, **quote))

    bot.say(" ".join(lines))


@sopel.module.rule(r"\.\. ((?:(?:[^ ]+)\s*)+)")
def symbol_lookup(bot, trigger):
    raw_symbols = trigger.group(1)

    split_symbols = list(map(str.strip, re.split(r"\s+", raw_symbols)))[:4]

    try:
        quotes = get_data_cnbc(split_symbols)
    except Exception as e:
        bot.say("Error retrieving data")
        return

    for quote in quotes:
        color = get_color(quote["change"])

        if "volume" in quote:
            price_line = PRICE_TPL.format(color=color, **quote)
        else:
            price_line = PRICE_TPL_NV.format(color=color, **quote)

        print(quote)
        message = SINGLE_TPL

        if "mktcapView" in quote:
            message += " | Cap: ${mktcapView}"

        if quote.get("dividend", "0") != "0":
            message += " | Dividend: {dividend}"
            if "dividendyield" in quote:
                message += " ({dividendyield}%)"

        if quote["curmktstatus"] != "REG_MKT":
            if extended := quote.get("ExtendedMktQuote"):
                if change := extended.get("change"):
                    ah_color = get_color(change)
                    message += " | Postmkt: " + PRICE_TPL.format(
                        color=ah_color, **quote["ExtendedMktQuote"]
                    )

        bot.say(message.format(price=price_line, **quote))


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
