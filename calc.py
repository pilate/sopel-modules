import ast
import math
import operator
import re

import sopel.module

# try:
#     import crypto as c
# except:
#     c = None

try:
    import finance
except:
    finance = None


# Borrowed from http://stackoverflow.com/questions/26505420/evaluate-math-equations-from-unsafe-user-input-in-python

operations = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.BitXor: operator.pow,
}


# def coin_price(symbol):
#     if symbol in ["btg", "btcg"]:
#         symbol = "bitcoin-gold"

#     if c is None:
#         raise Exception("Crypto module not found")

#     prices = c.price_search([symbol])
#     if not prices:
#         raise Exception("Crypto symbol not found")

#     return prices[0]["price_usd"]


def stock_price(symbol):
    if finance is None:
        raise ModuleNotFoundError("Finance module not found")

    data = finance.get_data_cnbc(symbol)
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
    if isinstance(node, str):
        node = ast.parse(node, "<string>", "eval").body

    if isinstance(node, ast.Num):
        return node.n

    if isinstance(node, ast.BinOp):
        operation = operations[node.op.__class__]
        left = safe_eval(node.left)
        right = safe_eval(node.right)
        if isinstance(node.op, ast.Pow):
            assert right < 100
        return operation(float(left), float(right))

    if isinstance(node, ast.Call):
        assert not node.keywords and not node.starargs and not node.kwargs
        assert isinstance(node.func, ast.Name), "Unsafe function derivation"
        func = functions[node.func.id]
        args = [safe_eval(arg) for arg in node.args]
        return func(*args)

    if isinstance(node, ast.Name):
        if node.id in names:
            return names[node.id]

        node_id = str(node.id)
        if node.id.startswith("_"):
            raise Exception("No crypto module")
            # return coin_price(node_id[1:].lower())
        else:
            return stock_price(node_id.lower())

    raise Exception("Unsafe operation")


@sopel.module.rule("\\.?\\.calc (.+)")
def calc(bot, trigger):
    expression = trigger.group(1).strip()
    expression = re.sub(r"\s", "", expression)

    try:
        result = safe_eval(expression)
    except Exception:
        bot.say("I'm afraid I can't do that.")
        return

    if isinstance(result, float) and result.is_integer():
        result = int(result)

    bot.say(f"{result:,}")
