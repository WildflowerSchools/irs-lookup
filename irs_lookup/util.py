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
