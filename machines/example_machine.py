import logging
from time import sleep
from core.blocks.choice_handler import Choice
from core.state_machine import StateMachine
from core.blocks.lambda_handler import Lambda
from core.blocks.parallel_handler import ParallelHandler


def example_parallel_machine():
    work_dir = "example"
    workflow1 = StateMachine("parallel_workflow1", [
        Lambda(f"{work_dir}/center_state", None, timeout=10)
    ])
    workflow2 = StateMachine("parallel_workflow2", [
        Lambda(f"{work_dir}/outer_state", None, timeout=20)
    ])

    machine_tree = [
        ParallelHandler(
            name="Parallel_block",
            next_state=None,
            workflows=[workflow1, workflow2]
        )
    ]

    machine = StateMachine("example_machine", machine_tree)
    event = {"value": 50}
    result = machine.run(event)
    print(result)  # {'workflow1': ..., 'workflow2': ...}


def example_machine():
    work_dir = "example"

    if__in_or_out__statements = [
        f"when ($.value gt 10) and ($.value lt 53) then '{work_dir}/center_state' else '{work_dir}/outer_state'"
    ]

    machine_tree = [
        Lambda(f"{work_dir}/center_state", "in_or_out"),  # Input First
        Choice("in_or_out", if__in_or_out__statements),
        Lambda(f"{work_dir}/outer_state", None),  # Output!
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
