#!/usr/bin/python
# -*- coding: UTF-8 -*-
from lxml import html

import copy
import datetime
import json
import time

import requests

import sopel.module



# PRICE_TPL_S = "({name} - ${price_usd} {price_sat}s {color}{percent_change_24h:+}%\x0f)"
PRICE_TPL = u"({name} - ${price_usd}/Ƀ{price_btc} {color}{percent_change_24h:+}%\x0f)"
SINGLE_PRICE_TPL = u"{name} - ${price_usd}/Ƀ{price_btc} {color}{percent_change_24h:+}%\x0f | Coins: {available_supply} | Cap: ${market_cap_usd} | 24h Vol: ${24h_volume_usd}"


def retry(times=10):
    def wrap(function):
        def f(*args, **kwargs):
            attempts = 0
            while attempts < times:
                try:
                    return function(*args, **kwargs)
                except:
                    time.sleep(.1)
                    attempts += 1
            raise Exception("Retry limit exceeded")
        return f
    return wrap


def write_prices(prices, bot):
    prices = copy.deepcopy(prices)
    for price in prices:
        for key in ["price_usd", "24h_volume_usd", "market_cap_usd", "price_btc", "available_supply"]:
            price[key] = "{:,.8f}".format(price[key]).rstrip("0").rstrip(".")

    output = []
    if len(prices) == 1:
        price = prices[0]
        output.append(SINGLE_PRICE_TPL.format(color=get_color(price["percent_change_24h"]), **price))
    else:
        for price in prices:
            output.append(PRICE_TPL.format(color=get_color(price["percent_change_24h"]), **price))

    bot.say(" ".join(output))


def clean_price(price):
    for key in ["price_usd", "24h_volume_usd", "percent_change_24h", "available_supply", "market_cap_usd"]:
        price[key] = float(price[key] or  0)

    if price["price_btc"]:
        price["price_btc"] = float(str(price["price_btc"]).rstrip("0").rstrip("."))
    else:
        price["price_btc"] = 0


def price_search(needles):
    prices = get_prices()

    found_prices = []
    seen_terms = []
    for search_term in needles:
        if search_term in ["btg", "btcg"]:
            search_term = "bitcoin-gold"

        if search_term in seen_terms:
            continue

        seen_terms.append(search_term)

        term_found = []
        for price in prices:
            if search_term in [price["name"].lower(), price["symbol"].lower(), price["id"].lower()]:
                term_found = [price]
                break

            elif (search_term in price["name"].lower()) or (search_term in price["symbol"].lower()):
                term_found.append(price)
        found_prices += term_found

    return found_prices

price_cache = {
    "time": datetime.datetime(*[1900, 1, 1]),
    "values": []
}

@retry(10)
def get_prices():
    global price_cache
    now = datetime.datetime.now()
    if (now - price_cache["time"]) > datetime.timedelta(minutes=2):
        prices = requests.get("https://api.coinmarketcap.com/v1/ticker/", params={"limit": 5000}, timeout=1).json()
        map(clean_price, prices)
        price_cache["time"] = now
        price_cache["values"] = prices

    return price_cache["values"]


def get_color(change):
    color = ""
    if change < 0:
        color = "\x0304"
    elif change > 0:
        color = "\x0309"
    return color


def get_fees():
    return requests.get("https://bitcoinfees.earn.com/api/v1/fees/recommended").json()


# https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def get_markets(coin_ids):
    market_map = {}
    for coin in coin_ids:
        data = requests.get("https://coinmarketcap.com/currencies/{0}/".format(coin)).content
        try:
            tree = html.fromstring(data)
        except:
            continue

        market_links = tree.xpath('//*[@id="markets"]//tbody/tr/td[2]/a')
        # order preserving
        unique = []
        [unique.append(item.text) for item in market_links if item.text not in unique]
        market_map[coin] = unique

    return market_map


@sopel.module.rule("\\.?\\.(shit|tard|alt)?coins?$")
@sopel.module.rule("\\.?\\.shit$")
def all_lookup(bot, trigger):
    prices = get_prices()
    write_prices(prices[:10], bot)


@sopel.module.rule("\\.?\\.c ((?:(?:[^ ]+) ?)+)$")
def specific_lookup(bot, trigger):
    raw = trigger.group(1)
    split = map(lambda s: s.strip().lower(), raw.split())[:10]

    found_prices = price_search(split)

    write_prices(found_prices[:10], bot)


@sopel.module.rule("\\.?\\.btcfees?$")
def fee_lookup(bot, trigger):
    prices = get_prices()
    for price in prices:
        if price["symbol"] == "BTC":
            clean_price(price)
            break

    fees = get_fees()
    for key in fees.keys():
        fees[key] = round(((fees[key] * 226) * 0.00000001) * price["price_usd"], 3)

    bot.say("Fastest: ${0}, 30m: ${1}, 1h: ${2}".format(fees["fastestFee"], fees["halfHourFee"], fees["hourFee"]))


@sopel.module.rule("\\.?\\.ccap$")
def market_cap(bot, trigger):
    prices = sorted(get_prices(), key=lambda p: p["24h_volume_usd"], reverse=True)
    caps = sorted(get_prices(), key=lambda p: p["market_cap_usd"], reverse=True)

    market_cap = sum(map(lambda p: p["price_usd"] * p["available_supply"], prices))
    day_cap = sum(map(lambda p: p["24h_volume_usd"], prices))
    total_vol = sum(map(lambda p: p["24h_volume_usd"], prices))

    vol_leaders = map(lambda p: "{0}: {1}%".format(p["name"], int(round((p["24h_volume_usd"] / total_vol) * 100))), prices[:3])
    mkt_leaders = map(lambda p: "{0}: {1}%".format(p["name"], int(round((p["market_cap_usd"] / market_cap) * 100))), caps[:3])

    bot.say("(Market Cap: ${0:,}) (24h Volume: ${1:,}) (24h Volume Leaders: {2}) (Market Leaders: {3})".format(int(market_cap), int(day_cap), ", ".join(vol_leaders), ", ".join(mkt_leaders)))


@sopel.module.rule("\\.?\\.best$")
def positive_movers(bot, trigger):
    prices = sorted(get_prices(), key=lambda p: p["market_cap_usd"], reverse=True)
    prices = sorted(prices[:100], key=lambda p: p["percent_change_24h"], reverse=True)
    write_prices(prices[:10], bot)


@sopel.module.rule("\\.?\\.worst$")
def negative_movers(bot, trigger):
    prices = sorted(get_prices(), key=lambda p: p["market_cap_usd"], reverse=True)
    prices = sorted(prices[:100], key=lambda p: p["percent_change_24h"])
    write_prices(prices[:10], bot)


@sopel.module.rule("\\.?\\.unconfirmed$")
@sopel.module.rule("\\.?\\.m[eo]m(pool)?$")
def mempool(bot, trigger):
    coins = [
        ("Core", "https://dedi.jochen-hoenicke.de/queue/2h.js", "Ƀ"),
        ("Cash", "https://dedi.jochen-hoenicke.de/queue/cash/2h.js", "Ƀ"),
        ("LTC", "https://dedi.jochen-hoenicke.de/queue/litecoin/2h.js", "Ł"),
    ]
    lines = []
    for coin, data_url, symbol in coins:
        response = requests.get(data_url).text.strip()[5:-4] + "]"

        try:
            response_obj = json.loads(response)
        except Exception as e:
            print "Failed: {0}".format(e)

        last_data = response_obj[-1]
        fees = float(sum(last_data[3])) / 100000000
        size = sizeof_fmt(float(sum(last_data[2])))
        lines.append("({0} - {1:,} transactions, {2}{3:,.8f} in fees, {4})".format(coin, sum(last_data[1]), symbol, fees, size))
    bot.say(" ".join(lines))


@sopel.module.rule("\\.?\\.cm ((?:(?:[^ ]+) ?)+)$")
@sopel.module.rule("\\.?\\.markets? ((?:(?:[^ ]+) ?)+)$")
def market_lookup(bot, trigger):
    raw = trigger.group(1)
    split = set(map(lambda s: s.strip().lower(), raw.split())[:3])

    found_prices = price_search(split)

    coin_ids = map(lambda f: f["id"], found_prices)
    markets = get_markets(coin_ids[:3])
    for coin, markets in markets.items():
        line = "{0} - {1}".format(coin, ", ".join(markets[:15]))
        if len(markets) > 15:
            line += "... ({0} others)".format(len(markets) - 15)
        bot.say(line)
