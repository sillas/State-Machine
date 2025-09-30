from core.handlers.choice_handler import Choice
from logging_config import _i


def teste():

    statements = [
        "when exist $.value and $.value lt 55 then #center-st",
        "#outer-st"
    ]

    states = {
        "center-st": {"name": "center_state"},
        "in-or-out": {"name": "in_or_out"},
        "outer-st": {"name": "outer_state"}
    }

    ch = Choice('choice_teste', statements, states)

    test_data = {"value": 50}
    result = ch.handler(test_data, {})
    _i(f"RESULT 1: {ch.next_state} -> {result}")


if __name__ == "__main__":
    teste()
