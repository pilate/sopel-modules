import requests

import sopel.module



PRICE_TPL = "({name} - ${price_usd} {color}{percent_change_24h:+}%\x0f)"

def write_prices(prices, bot):
    output = []
    for price in prices:
        output.append(PRICE_TPL.format(color=get_color(price["percent_change_24h"]), **price))

    bot.say(" ".join(output))


def clean_price(price):
    for key in ["price_usd", "percent_change_24h"]:
        if price[key]:
            price[key] = float(price[key])


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


@sopel.module.rule("\\.?\\.(shit|tard|alt)?coins?$")
def all_lookup(bot, trigger):
    prices = get_prices()
    write_prices(prices[:10], bot)


@sopel.module.rule("\\.?\\.c (.+)$")
def specific_lookup(bot, trigger):
    search_term = trigger.group(1).lower()

    prices = get_prices()

    found_prices = []
    for price in prices:
        if (search_term == price["name"].lower()) or (search_term == price["symbol"].lower()):
            found_prices = [price]
            break

        elif (search_term.lower() in price["name"].lower()) or (search_term.lower() in price["symbol"].lower()):
            found_prices.append(price)

    write_prices(found_prices, bot)