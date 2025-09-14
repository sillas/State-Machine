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
from machine_definition.machine import StateMachine, Lambda, LambdaTypes

# Define your lambda states
machine_tree = {
    "init": Lambda(
        name="request",
        type="request",
        next_state="process_data"
    ),
    "process_data": Lambda(
        name="process_data",
        type="process",
        next_state="decision"
    ),
    "decision": Lambda(
        name="decision",
        type=LambdaTypes.IF.value,
        statements=[
            {
                "sttm": ["$.result.confidence gt 0.8"],
                "then": "high_confidence",
                "bool_ops": None
            },
            {
                "sttm": None,  # Default case
                "then": "low_confidence",
                "bool_ops": None
            }
        ]
    ),
    "high_confidence": Lambda(
        name="high_confidence_handler",
        type="process",
        next_state=LambdaTypes.END.value
    ),
    "low_confidence": Lambda(
        name="low_confidence_handler",
        type="process",
        next_state=LambdaTypes.END.value
    )
}

# Create the state machine
state_machine = StateMachine(
    machine_name="ai_workflow",
    machine_tree=machine_tree,
    timeout=60
)

# Execute the state machine with initial input
result = state_machine.machine({"input": "initial data"})
```

### Creating Lambda Functions

Each state in the machine corresponds to a lambda function that should be placed in the `lambdas/{machine_name}/{lambda_name}` directory with a `main.py` file containing a `lambda_handler` function:

```python
# lambdas/ai_workflow/request/main.py

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

## Future Enhancements

- Parallel execution of states
- State machine visualization
- Persistence and recovery
- Monitoring and metrics
- More complex branching patterns

## License

[Specify your license here]
