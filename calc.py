import ast
import math
import operator
import re

import sopel.module



try:
    import crypto as c
except:
    c = None

try:
    import finance as f
except:
    f = None


# Borrowed from http://stackoverflow.com/questions/26505420/evaluate-math-equations-from-unsafe-user-input-in-python

operations = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.div,
    ast.Pow: operator.pow,
    ast.BitXor: operator.pow,
}


def coin_price(symbol):
    if symbol in ["btg", "btcg"]:
        symbol = "bitcoin-gold"

    if c is None:
        raise Exception("Crypto module not found")

    prices = c.price_search([symbol])
    if not prices:
        raise Exception("Crypto symbol not found")

    return prices[0]["price_usd"]


def stock_price(symbol):
    if f is None:
        raise Exception("Finance module not found")

    data = f.get_data_cnbc(symbol)
    if not data:
        raise Exception("Failed to get symbol data")

    return data[0]["last"]


functions = {
    "acos": math.acos,
    "asin": math.asin,
    "atan": math.atan,
    "atan2": math.atan,
    "cos": math.cos,
    "sin": math.sin,
    "tan": math.tan,
    "floor": math.floor,
    "log": math.log,
    "log10": math.log10,
}

names = {
    "pi": math.pi,
    "e": math.e
}

def safe_eval(node):
    if type(node) == unicode:
        node = ast.parse(node, "<string>", "eval").body

    if isinstance(node, ast.Num):
        return node.n

    elif isinstance(node, ast.BinOp):
        op = operations[node.op.__class__]
        left = safe_eval(node.left)
        right = safe_eval(node.right)
        if isinstance(node.op, ast.Pow):
            assert right < 100
        return op(float(left), float(right))

    elif isinstance(node, ast.Call):
        assert not node.keywords and not node.starargs and not node.kwargs
        assert isinstance(node.func, ast.Name), "Unsafe function derivation"
        func = functions[node.func.id]
        args = [safe_eval(arg) for arg in node.args]
        return func(*args)

    elif isinstance(node, ast.Name):
        if node.id in names:
            return names[node.id]

        node_id = str(node.id)
        if node.id.startswith("_"):
            return coin_price(node_id[1:].lower())
        else:
            return stock_price(node_id.lower())

    raise Exception("Unsafe operation")


@sopel.module.rule("\\.?\\.calc (.+)")
def calc(bot, trigger):
    expression = trigger.group(1).strip()
    expression = re.sub("\s", "", expression)

    try:
        result = safe_eval(expression)
    except Exception as e:
        bot.say("Nope.")
        return

    if (type(result) == float) and result.is_integer():
        result = long(result)

    bot.say("{result:,}".format(result=result))

