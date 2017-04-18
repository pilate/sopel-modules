import sopel.module

import requests



API_URL = "https://query.yahooapis.com/v1/public/yql"

CARDS = [
    (338, "north"),
    (293, "north west"),
    (247, "west"),
    (203, "south west"),
    (157, "south"),
    (110, "south east"),
    (67, "east"),
    (23, "north east"),
    (0, "north")
]


def req_weather(location):
    clean_ish = location.replace("\\", "").replace("\"", "")
    response = requests.get(API_URL, params={
        "q": """select * from weather.forecast where woeid in (select woeid from geo.places where text = "{city}")""".format(city=location),
        "format": "json",
        "env": "store://datatables.org/alltableswithkeys"
    })
    return response.json()["query"]["results"]


def f_to_c(temp):
    return (float(temp) - 32) * (float(5) / float(9))


# Degress to cardinal direction
def d_to_c(degree):
    for min_degree, direction in CARDS:
        if degree > min_degree:
            return direction


@sopel.module.rule("\\.?\\.wz (.+)")
def current_lookup(bot, trigger):
    user_trigger = trigger.group(1)

    data = req_weather(user_trigger)
    if not data:
        return

    if type(data["channel"]) == list:
        weather = data["channel"][0]
    else:
        weather = data["channel"]

    weather["item"]["condition"]["temp_c"] = round(f_to_c(weather["item"]["condition"]["temp"]), 2)
    weather["wind"]["chill_c"] = round(f_to_c(weather["wind"]["chill"]), 2)
    weather["wind"]["direction_s"] = d_to_c(float(weather["wind"]["direction"]))
    weather["wind"]["speed_k"] = round(float(weather["wind"]["speed"]) * 1.609344)

    location = "{city},{region}, {country}: ".format(**weather["location"])
    conditions = "{temp} F ({temp_c} C), ".format(**weather["item"]["condition"])
    atmosphere = "humidity {humidity}%, ".format(**weather["atmosphere"])
    wind = "wind chill {chill} F ({chill_c} C) speed {speed}mph ({speed_k}kph) from the {direction_s}".format(**weather["wind"])

    bot.say(location + conditions + atmosphere + wind)