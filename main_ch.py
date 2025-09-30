from core.handlers.choice2_handler import Choice2
from test_cache.logger import _i


def teste():

    statements = [
        "when $.user.age lt 24 then #novo",
        "when $.user.age gt 50 then #velho",
        "#adulto"
    ]

    states = {
        "novo": {"name": "novo"},
        "velho": {"name": "velho"},
        "adulto": {"name": "adulto"}
    }

    ch = Choice2('choice_teste', statements, states)

    test_data = {"user": {"age": 60, "status": "active"}}
    result = ch.handler(test_data, {})
    _i(f"RESULT 1: {result}")

    test_data = {"user": {"age": 10, "status": "active"}}
    result = ch.handler(test_data, {})
    _i(f"RESULT 2: {result}")


if __name__ == "__main__":
    teste()
