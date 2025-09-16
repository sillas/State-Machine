
from core.state_machine import StateMachine
from core.lambda_handler import Lambda, IF
from core.statement_models import Operator, StatementBuilder, DefaultStatements


def main():

    if__in_or_out__statements = [
        StatementBuilder()
        .when("$.value", Operator.GT, 10)
        .and_when("$.value", Operator.LT, 100)
        .then("center_state")
        .build(),
        DefaultStatements.next_state("outer_state")
    ]

    machine_tree = [
        Lambda("center_state", "in_or_out"),  # Input First
        IF("in_or_out", if__in_or_out__statements),
        Lambda("outer_state", None),  # Output!
    ]

    machine = StateMachine("out-of-machine", machine_tree)

    event = {"value": 50}
    machine.run(event)
