#!/usr/bin/python
# -*- coding: UTF-8 -*-

import requests

import sopel.module



# PRICE_TPL_S = "({name} - ${price_usd} {price_sat}s {color}{percent_change_24h:+}%\x0f)"
PRICE_TPL = u"({name} - ${price_usd}/Ƀ{price_btc} {color}{percent_change_24h:+}%\x0f)"

def write_prices(prices, bot):
    output = []
    for price in prices:
        output.append(PRICE_TPL.format(color=get_color(price["percent_change_24h"]), **price))

    bot.say(" ".join(output))


def clean_price(price):
    for key in ["price_usd", "24h_volume_usd", "percent_change_24h", "available_supply"]:
        price[key] = float(price[key] or  0)

    if price["price_btc"]:
        price["price_btc"] = price["price_btc"].rstrip("0").rstrip(".")


def get_prices():
    prices = requests.get("https://api.coinmarketcap.com/v1/ticker/").json()
    map(clean_price, prices)
    return prices


def get_color(change):
    color = ""
    if change < 0:
        color = "\x0304"
    elif change > 0:
        color = "\x0309"
    return color


def get_fees():
    return requests.get("https://bitcoinfees.21.co/api/v1/fees/recommended").json()


@sopel.module.rule("\\.?\\.(shit|tard|alt)?coins?$")
def all_lookup(bot, trigger):
    prices = get_prices()
    write_prices(prices[:10], bot)


@sopel.module.rule("\\.?\\.c ((?:(?:[^ ]+) ?)+)$")
def specific_lookup(bot, trigger):
    raw = trigger.group(1)
    split = map(lambda s: s.strip().lower(), raw.split())[:10]

    prices = get_prices()

    found_prices = []
    for search_term in split:
        term_found = []
        for price in prices:
            if search_term in [price["name"].lower(), price["symbol"].lower()]:
                term_found = [price]
                break

            elif (search_term in price["name"].lower()) or (search_term in price["symbol"].lower()):
                term_found.append(price)
        found_prices += term_found

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

    market_cap = sum(map(lambda p: p["price_usd"] * p["available_supply"], prices))
    day_cap = sum(map(lambda p: p["24h_volume_usd"], prices))
    total_vol = sum(map(lambda p: p["24h_volume_usd"], prices))

    leaders = map(lambda p: "{0}: {1}%".format(p["name"], int(round((p["24h_volume_usd"] / total_vol) * 100))), prices[:3])

    bot.say("(Market Cap: ${0:,}) (24h Volume: ${1:,}) (24h Volume Leaders: {2})".format(int(market_cap), int(day_cap), ", ".join(leaders)))