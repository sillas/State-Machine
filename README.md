# State Machine for AI Agent Workflows

A flexible state machine implementation similar to AWS Step Functions, designed to orchestrate and coordinate AI agent workflows.

**⚠️ DEVELOPMENT STATUS**: This project is currently in active development and may not function correctly or functionality may be incomplete. APIs, interfaces, and functionality are subject to change without notice. Please do not use in production environments.

## Overview

This project provides a state machine framework that allows you to define, execute, and manage complex workflows involving AI agents. The state machine handles the sequential execution of lambdas (function handlers), conditional branching, and state transitions, making it ideal for coordinating multi-step AI agent processes.

## Features

- **Lambda-based Architecture**: Define reusable function handlers that perform specific tasks in your workflow
- **Powerful Choice Logic**: Natural language-like conditional statements with JSONPath support
- **Parallel Execution**: Run multiple workflows concurrently with Parallel
- **Advanced Condition Parsing**: Support for strings, numbers, lists, JSONPath expressions, and boolean logic
- **Flexible State Transitions**: Define complex state transitions based on dynamic conditions
- **Timeout Handling**: Built-in timeout protection for long-running workflows and individual states

## Use Cases

- **Multi-agent Coordination**: Orchestrate communication and task handoff between multiple AI agents
- **Sequential Task Processing**: Define step-by-step workflows for complex AI tasks
- **Decision Trees**: Implement decision-making logic based on AI agent outputs
- **Error Handling and Retry Logic**: Gracefully handle failures and implement retry mechanisms
- **Long-running AI Processes**: Manage stateful processes that require multiple steps

## Getting Started
 install [uv](https://docs.astral.sh/uv/getting-started/installation/)
 
 Run: `$ uv run main.py`

### Defining a State Machine

A state machine consists of a collection of lambda functions and a machine definition that specifies how these functions are connected:

```python
from core.state_machine import StateMachine
from core.handlers.lambda_handler import Lambda
from core.handlers.choice_handler import Choice

# Define your state machine with lambdas and choice states
machine_tree = [
    Lambda("request", "process_data", "lambda_path"),  # Process initial request
    Lambda("process_data", "decision", "lambda_path"),  # Process the data
    Choice("decision", [
        "when $.result.confidence gt 0.8 then 'high_confidence' else 'low_confidence'"
    ]),
    Lambda("high_confidence", None, "lambda_path"),  # Final state for high confidence
    Lambda("low_confidence", None, "lambda_path")    # Final state for low confidence
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

## Statement Evaluation and Choice States

The state machine now supports powerful conditional evaluations using the `Choice` class with natural language-like syntax:

### Supported Operators
- Comparison: `gt`, `lt`, `eq`, `neq`, `gte`, `lte`, `contains`, `starts_with`, `ends_with`
- Boolean: `and`, `or`, `not`
- Parentheses for grouping: `(condition)`

### Supported Data Types
- **JSONPath expressions**: `$.user.name`, `$.items[0]`
- **Literal strings**: `'text value', '42', '3.14'`
- **Numbers**: 42, 3.14
- **Empty lists**: `[]`
- **Lists**: `[item1, item2]`

### Choice Statement Syntax

Choice statements support complex conditional logic with the following formats:

```python
# When-then statements
"when $.user.age gt 18 then 'adult'"

# When-then-else statements  
"when $.user.age gt 18 then 'adult' else 'minor'"

# Complex conditions with boolean operators
"when ($.user.age gt 18) and ($.user.name starts_with 'John') then 'valid_user'"

# Nested conditions
"when $.price gt 100 then 'expensive' else when $.price gt 50 then 'medium' else 'cheap'"

# Multiple Conditions in a List (Returns the First True Evaluation)
# Similar to if, elif..., else
[
    "when ($.value gt 10) and ($.value lt 20) then 'inside'",  # returns 'inside' if true
    "when $.value eq 100 then 'is 100'",                       # returns 'is 100' if true
    "'not matched!'"                                           # return default value "not matched!"
]
```

### Example Choice Usage

```python
from core.handlers.choice_handler import Choice

# Define complex conditional statements
choice_statements = [
    "when ($.user.age gt 36) then 'senior' else when ($.user.age lt 18) then 'minor' else 'adult'",
    "when $.user.name starts_with 'John' or $.user.name starts_with 'Jane' then 'common_name'",
    "when $.items contains 'premium' then 'premium_user'", 
    "when $.price gte 100 then 'expensive_item'",
    "when not $.discount_applied then 'full_price'",
    "when $.shopping_cart eq [] then 'empty_cart'",
    "'default_value'"  # Default fallback
]

# Create choice state
choice_state = Choice("price_decision", choice_statements)
```

## Architecture

The project is organized into several key components:

- **core/**: Contains the core state machine implementation
  - **state_machine.py**: Main StateMachine class for workflow orchestration
  - **handlers/**: State handler implementations
    - **choice_handler.py**: Conditional logic and decision making
    - **lambda_handler.py**: Lambda function execution
    - **parallel_handler.py**: Parallel workflow execution
  - **utils/**: Utility classes and parsers
    - **parsers.py**: Condition parsing (JSONPath, literals, numbers, lists)
    - **state_base.py**: Base state class and types
- **lambdas/**: Directory for lambda function implementations
- **machines/**: Pre-defined machine configurations and examples
- **tests/**: Test cases and validation

## Example: Complete State Machine with Choice Logic

Below is an example of a complete state machine defined in `machines/example_machine.py`. This demonstrates the use of Lambda states, Choice states for conditional branching, and Parallel execution:

```python
from core.state_machine import StateMachine
from core.handlers.lambda_handler import Lambda
from core.handlers.choice_handler import Choice
from core.handlers.parallel_handler import Parallel

def example_machine():
    """Example showing conditional branching based on input value."""
    
    # Define conditional statements for routing
    if__in_or_out__statements = [
        "when ($.value gt 10) and ($.value lt 53) then 'example/center_state' else 'example/outer_state'"
    ]

    machine_tree = [
        Lambda("example/center_state", "in_or_out"),  # Initial processing
        Choice("in_or_out", if__in_or_out__statements),  # Conditional routing
        Lambda("example/outer_state", None),  # Final output state
    ]

    machine = StateMachine("example_machine", machine_tree)
    
    event = {"value": 50}
    result = machine.run(event)
    return result

def example_parallel_machine():
    """Example showing parallel execution of workflows."""
    
    # Define parallel workflows
    workflow1 = StateMachine("parallel_workflow1", [
        Lambda("example/center_state", None, timeout=10)
    ])
    
    workflow2 = StateMachine("parallel_workflow2", [
        Lambda("example/outer_state", None, timeout=20)
    ])

    machine_tree = [
        Parallel(
            name="Parallel_block",
            next_state=None,
            workflows=[workflow1, workflow2]
        )
    ]

    machine = StateMachine("example_machine", machine_tree)
    event = {"value": 50}
    result = machine.run(event)
    print(result)  # {'parallel_workflow1': ..., 'parallel_workflow2': ...}
    return result
```

### Advanced Choice Examples

```python
# Example data structure
test_data = {
    "user": {
        "name": "Jonas Silva",
        "age": 37,
        "items": ["apple", "banana"]
    },
    "price": 170,
    "empty_list": []
}

# Complex choice statements
advanced_statements = [
    "when ($.user.age gt 36) then 'senior' else when ($.user.age lt 10) then 'children' else 'young'",
    "when $.user.name starts_with 'João' or $.user.name starts_with 'Jonas' then 'matched name'",
    "when $.user.items contains 'banana' then 'has banana'",
    "when $.price gte 100 then 'expensive'",
    "when (not $.price gte 180) then 'cheaper'", 
    "when $.empty_list eq [] then 'list is empty'",
    "'default value'"  # Fallback value
]

choice_state = Choice("complex_decision", advanced_statements)
```

## Future Enhancements

- ✅ Parallel execution of machines (implemented via Parallel)
- State machine visualization
- Run and forget state
- Persistence and recovery
- Monitoring and metrics
- More complex branching patterns
- Enhanced error handling and retry mechanisms

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
