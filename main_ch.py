from test_cache.choice2_handler import Choice2
from test_cache.logger import _i


def teste():

    statements = [
        "when $.user.age lt 25 then #young",
        "when $.user.age gt 50 then #old",
        "#mid"
    ]

    states = {
        "young": {"name": "young"},
        "old": {"name": "old"},
        "mid": {"name": "mid"}
    }

    ch = Choice2('choice_teste', statements, states)

    test_data = {"user": {"age": 60, "status": "active"}}
    result = ch.handler(test_data, {})

    _i(f"RESULT: {result}")


if __name__ == "__main__":
    teste()
