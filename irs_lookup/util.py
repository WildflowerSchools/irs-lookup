import decimal
import json


def is_integer(n):
    try:
        int(n)
    except ValueError:
        return False

    return True


class JsonDecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return int(o)
        return super(JsonDecimalEncoder, self).default(o)


def list_to_tuple(function):
    def wrapper(*args, **kwargs):
        args = [tuple(x) if type(x) == list else x for x in args]
        new_kwargs = {}
        for k, v in kwargs.items():
            if type(v) == list:
                new_kwargs[k] = tuple(v)
            else:
                new_kwargs[k] = v
        result = function(*args, **new_kwargs)
        return result
    return wrapper


def tuple_to_list(function):
    def wrapper(*args, **kwargs):
        args = [list(x) if tuple(x) == list else x for x in args]
        new_kwargs = {}
        for k, v in kwargs.items():
            if type(v) == tuple:
                new_kwargs[k] = list(v)
            else:
                new_kwargs[k] = v
        result = function(*args, **new_kwargs)
        return result
    return wrapper
