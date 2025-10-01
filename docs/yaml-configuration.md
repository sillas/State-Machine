# YAML Configuration for State Machine

This document describes how to define state machines using YAML files in the State Machine project.

## Basic Structure

A YAML state machine configuration file has the following structure:

```yaml
entry: main-machine-name

machine-1:
  name: 'Machine Name'
  lambda_dir: directory/of/lambdas # Lambda root directory
  tree:
    state-1: next-state
    state-2: null
  states:
    state-1:
      name: real_state_name # Lambda directory inside "lambda_dir"
      type: lambda|choice|parallel
  vars: # used for "Choice" state definitions
    $variable: value
```

## Main Elements

### 1. Entry Point (`entry`)

Defines which machine will be executed as the entry point:

```yaml
entry: example-machine
```

### 2. Machine Definition

Each machine has:

- **name**: Descriptive name of the machine
- **lambda_dir**: Directory where lambda functions are located
- **tree**: Execution flow between states
- **states**: Detailed state definitions
- **vars**: Reusable variables (optional)

### 3. Tree (Execution Tree)

Defines the flow between states:

```yaml
tree:
  first-state: second-state     # first-state → second-state
  second-state: third-state     # second-state → third-state
  third-state: null             # third-state (final)
```

### 4. States (State Definitions)

#### Lambda State

Executes a lambda function:

```yaml
states:
  my-state:
    name: lambda_function_name
    type: lambda
    timeout: 30  # optional, in seconds (default: 60s for lambda type)
```

The lambda function must be at: `{lambda_dir}/{name}/main.py`
And have the entry method `lambda_handler(event: Any, context: dict[str, Any])`

#### Choice State

Executes conditional logic:

```yaml
states:
  decision:
    name: decision_name
    type: choice
```

Requires variables with conditions:

```yaml
vars:
  $conditions: # list
    - "when $.value gt 10 then #state-a else #state-b"
```

#### Parallel State

Executes multiple workflows in parallel:

```yaml
states:
  parallel:
    name: parallel_execution
    type: parallel
    workflows:
      - workflow-1
      - workflow-2
```

### 5. Variables

Allow reuse of complex values in Choice:

```yaml
vars:
  $my-conditions:
    - "when ($.value gt 10) and ($.value lt 53) then #center-state else #outer-state"
```

Usage in tree:
```yaml
tree:
  choice-state: $my-conditions
```

## State References

### Hash Reference (#)

Within conditions, use `#` to reference defined states:

```yaml
vars:
  $conditions:
    - "when $.value gt 100 then #expensive-state else #cheap-state"
```

This will be automatically converted to the real state names.
You can use the real names (in name) in single quotes if you prefer.

## Condition Syntax

Conditions follow natural syntax:

```yaml
# Simple condition
"when $.age gt 18 then #adult else #minor"

# Complex conditions
"when ($.age gt 18) and ($.name starts_with 'John') then #valid"
# or
"when $.age gt 18 and $.name starts_with 'John' then #valid"

# Nested conditions
"when $.price gt 100 then #expensive else when $.price gt 50 then #medium else #cheap"

# Complex conditions (list)
- "when exist $.error then #error-handler-state"
- "when $.result eq 'email' then #send-email-state"
- "when $.result eq 'whatsapp' then #send-wa-state"
- "#default-state"
```

### Supported Operators

- **Comparison**: `gt`, `lt`, `eq`, `neq`, `gte`, `lte`
- **String**: `contains`, `starts_with`, `ends_with`
- **Lists**: `contains`
- **Structure**: `exist`
- **Logical**: `and`, `or`, `not`
- **Grouping**: `(condition)`

## Usage examples:
- **Comparison**: `term op term`
- **String**: `term op literal`

## Literal:
- String: `'string', '10'` # Use single quotes
- Number: 10, 15.7
> Use double quotes for strings inside lists and dictionaries
- List: `[5, 36, 8, 10, "string"]`
- Dictionary: `{"key_1": "value", "key_2": 10}`

### JSONPath

Use JSONPath to access data:

```yaml
"when $.user.age gt 25 then #senior"
"when $.items[0] eq 'premium' then #vip"
"when $.list eq [] then #empty"
```
> Only empty lists and dictionaries can be compared with `eq`.

## Complete Example

See `machines/sm_description.yml` for a complete functional example.

## Next Steps

- Consult [YAML Examples](yaml-examples.md) for practical use cases
- See [API Reference](api-reference.md) for technical details