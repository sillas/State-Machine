import logging
from time import sleep
from core.blocks.parallel_handler import ParallelHandler
from core.state_machine import StateMachine
from core.blocks.lambda_handler import Lambda, IF
from core.statement_models import Operator, StatementBuilder, DefaultStatements


def example_parallel_machine():

    workflow1 = StateMachine("parallel_workflow1", [
        Lambda("center_state", None, timeout=10)
    ])
    workflow2 = StateMachine("parallel_workflow2", [
        Lambda("outer_state", None, timeout=20)
    ])

    machine_tree = [
        ParallelHandler(
            name="Parallel_block",
            workflows=[workflow1, workflow2],
            next_state=None)
    ]

    machine = StateMachine("example_machine", machine_tree)
    event = {"value": 50}
    result = machine.run(event)
    print(result)  # {'workflow1': ..., 'workflow2': ...}


def example_machine():

    if__in_or_out__statements = [
        StatementBuilder()
        .when("$.value", Operator.GT, 10)
        .and_when("$.value", Operator.LT, 53)
        .then("center_state")
        .build(),
        DefaultStatements.next_state("outer_state")
    ]

    machine_tree = [
        Lambda("center_state", "in_or_out"),  # Input First
        IF("in_or_out", if__in_or_out__statements),
        Lambda("outer_state", None),  # Output!
    ]

    machine = StateMachine("example_machine", machine_tree)

    event = {"value": 50}
    machine.run(event)


def main():

    logging.info("Running example_machine()\n\n")
    example_machine()
    sleep(3)

    logging.info("\n\nRunning example_parallel_machine()\n\n")
    example_parallel_machine()
