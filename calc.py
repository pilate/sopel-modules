import ast
import math
import operator

import sopel.module



# Taken from http://stackoverflow.com/questions/26505420/evaluate-math-equations-from-unsafe-user-input-in-python

operations = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.div,
    ast.Pow: operator.pow,
    ast.BitXor: operator.pow,
}

functions = {
    "acos": math.acos,
    "asin": math.asin,
    "atan": math.atan,
    "atan2": math.atan,
    "cos": math.cos,
    "sin": math.sin,
    "tan": math.tan,

    "floor": math.floor,
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

    raise Exception("Unsafe operation")


@sopel.module.rule("\\.?\\.calc (.+)")
def calc(bot, trigger):
    expression = trigger.group(1)
    try:
        bot.say("{result}".format(result=safe_eval(expression)))
    except Exception as e:
        bot.say("Nope.")
    
