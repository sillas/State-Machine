# State Machine for AI Agent Workflows

A powerful and flexible state machine implementation similar to AWS Step Functions, designed to orchestrate and coordinate AI agent workflows.

> **⚠️ DEVELOPMENT STATUS**: This project is currently in active development and may not function as expected. APIs, interfaces, and functionality are subject to change without notice. Please do not use in production environments.

## Overview

This project provides a state machine framework that allows you to define, execute, and manage complex workflows involving AI agents. The state machine handles the sequential execution of lambdas (function handlers), conditional branching, and state transitions, making it ideal for coordinating multi-step AI agent processes.

## Features

- **Lambda-based Architecture**: Define reusable function handlers that perform specific tasks in your workflow
- **Conditional Branching**: Powerful JSON-based condition evaluation to control workflow paths
- **JSONPath Support**: Query and manipulate data using JSONPath expressions
- **Timeout Handling**: Built-in timeout protection for long-running workflows
- **Flexible State Transitions**: Define complex state transitions based on the output of previous steps

## Use Cases

- **Multi-agent Coordination**: Orchestrate communication and task handoff between multiple AI agents
- **Sequential Task Processing**: Define step-by-step workflows for complex AI tasks
- **Decision Trees**: Implement decision-making logic based on AI agent outputs
- **Error Handling and Retry Logic**: Gracefully handle failures and implement retry mechanisms
- **Long-running AI Processes**: Manage stateful processes that require multiple steps

## Getting Started

### Defining a State Machine

A state machine consists of a collection of lambda functions and a machine definition that specifies how these functions are connected:

```python
from machine_definition.machine import StateMachine
from utils.constants import Lambda, IF
from utils.statement_models import StatementBuilder, DefaultStatements, Operator

# Define your lambda states
machine_tree = [
    Lambda(
        name="request",
        next_state="process_data"
    ),
    Lambda(
        name="process_data",
        next_state="decision"
    ),
    IF(
        name="decision",
        statements=[
            StatementBuilder()
                .when("$.result.confidence", Operator.GT, 0.8)
                .then("high_confidence"),
            DefaultStatements.next_state("low_confidence")
        ]
    ),
    Lambda(
        name="high_confidence",
        next_state=None
    ),
    Lambda(
        name="low_confidence",
        next_state=None
    )
]

# Create the state machine
state_machine = StateMachine(
    machine_name="ai_workflow",
    machine_tree=machine_tree,
    timeout=60
)

# Execute the state machine with initial input
result = state_machine.run({"input": "initial data"})
```

### Creating Lambda Functions

Each state in the machine corresponds to a lambda function that should be placed in the `lambdas/{lambda_name}` directory with a `main.py` file containing a `lambda_handler` function:

```python
# lambdas/request/main.py

def lambda_handler(event, context):
    # Process the input event
    # Return data for the next state
    return {"processed_data": "some value"}
```

## Statement Evaluation

The state machine supports complex conditional evaluations using the `StatementEvaluator` class:

- Supports multiple comparison operators: `gt`, `lt`, `eq`, `neq`, `gte`, `lte`, `contains`, `starts_with`, `ends_with`
- Boolean operators for combining conditions: `AND`, `OR`
- JSONPath expressions for querying data

## Architecture

The project is organized into several key components:

- **machine_definition/**: Contains the core state machine implementation
- **lambdas/**: Directory for lambda function implementations
- **utils/**: Utility classes for statement evaluation, JSONPath querying, etc.
- **tests/**: Test cases and examples
- **machines/**: Pre-defined machine configurations

## Example: Out-of-Machine State Machine

Below is an example of a complete state machine defined in `machines/out_of_machine.py`. This state machine demonstrates the use of lambdas, conditional branching, and state transitions:

```python
from machine_definition.machine import StateMachine
from utils.constants import Lambda, IF
from utils.statement_models import Operator, StatementBuilder, DefaultStatements

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
        Lambda("center_state", "in_or_out"), # Input First
        IF("in_or_out", if__in_or_out__statements),
        Lambda("outer_state", None), # Output!
    ]

    machine = StateMachine("out-of-machine", machine_tree)

    event = {"value": 50}
    machine.run(event)
```

### Explanation

1. **State Definitions**:
   - `center_state`: A lambda function that processes the input.
   - `in_or_out`: A conditional state that evaluates the input value.
   - `outer_state`: The final state that outputs the result.

2. **Conditional Logic**:
   - If the value is between 10 and 100, the machine transitions to `center_state`.
   - Otherwise, it transitions to `outer_state`.

3. **Execution**:
   - The machine is executed with an input event `{"value": 50}`.
   - Based on the input, the machine evaluates the conditions and transitions accordingly.

This example showcases the flexibility and power of the state machine framework for orchestrating workflows.

### Clarification

In the example above:

- `statements`: Defined as a list of conditions that determine the state transitions.
- `machine_tree`: Defined as a list representing the sequence of states in the state machine.

This structure allows for flexibility in defining complex workflows with multiple states and transitions.

## Future Enhancements

- Parallel execution of states
- State machine visualization
- Persistence and recovery
- Monitoring and metrics
- More complex branching patterns

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
