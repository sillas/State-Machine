# State Machine YAML Examples

This document presents practical examples of YAML configuration for different usage scenarios.

## Example 1: Simple Sequential Machine

**File**: `machines/sm_description.yml`

```yaml
entry: example-machine

example-machine:
  name: 'example machine'
  lambda_dir: lambdas/example

  tree:
    center-state: in-or-out
    in-or-out: $ioo-statements
    outer-state: null
  
  states:
    center-state:
      name: center_state
      type: lambda
    
    in-or-out:
      name: in_or_out
      type: choice
    
    outer-state:
      name: outer_state
      type: lambda
  
  vars:
    $ioo-statements:
      - "when ($.value gt 10) and ($.value lt 53) then #center-state else #outer-state"
```

### How It Works

1. **Entry**: Executes `center_state` lambda
2. **Decision**: Evaluates if `value` is between 10 and 53
3. **Output**:
   - If `value` ∈ [11, 52] → returns to `center_state`
   - Otherwise → goes to `outer_state` (final)

### Required File Structure

```
lambdas/example/
├── center_state/
│   └── main.py
└── outer_state/
    └── main.py
```

### Lambda Example

```python
# lambdas/example/center_state/main.py
def lambda_handler(event, context):
    event["value"] += 1
    return event
```

## Example 2: Parallel Execution

**File**: `machines/sm_p_description.yml`

```yaml
entry: example-machine

# First machine for parallel execution
mc_01:
  name: machine_01
  lambda_dir: lambdas/example

  tree:
    center-state: null
  
  states:
    center-state:
      name: center_state
      type: lambda 

# Second machine for parallel execution
mc_02:
  name: machine_02
  lambda_dir: lambdas/example

  tree:
    outer-state: null
  
  states:
    outer-state:
      name: outer_state
      type: lambda 

# Main machine that orchestrates parallel execution
example-machine:
  name: 'example machine'
  lambda_dir: lambdas/example

  tree:
    run-state: null # In this case, we have no more states.
  
  states:
    run-state:
      name: unique_state
      type: parallel
      workflows:
        - mc_01
        - mc_02
```

### How It Works

1. **Entry**: Executes parallel state `unique_state`
2. **Parallel**: Executes simultaneously one or more machines:
   - `mc_01`: executes `center_state`
   - `mc_02`: executes `outer_state`
   # Use for complex flows or for parallel state execution.
3. **Result**: Returns data from both workflows

### Expected Result

```python
{
    'machine_01': result_from_center_state,
    'machine_02': result_from_outer_state
}
```

## Example 3: Complex Decisions

```yaml
entry: complex-workflow

complex-workflow:
  name: 'Workflow with Multiple Decisions'
  lambda_dir: lambdas/business

  tree:
    validate-user: age-decision
    age-decision: $age-conditions
    process-adult: premium-decision
    process-minor: notify-guardian
    premium-decision: $premium-conditions
    upgrade-premium: null
    keep-basic: null
    notify-guardian: null
  
  states:
    validate-user:
      name: validate_user
      type: lambda
    
    age-decision:
      name: check_age
      type: choice
    
    process-adult:
      name: process_adult
      type: lambda
    
    process-minor:
      name: process_minor
      type: lambda
      
    premium-decision:
      name: check_premium
      type: choice
      
    upgrade-premium:
      name: upgrade_premium
      type: lambda
      
    keep-basic:
      name: keep_basic
      type: lambda
      
    notify-guardian:
      name: notify_guardian
      type: lambda
  
  vars:
    $age-conditions:
      - "when $.user.age gte 18 then #process-adult else #process-minor"
      
    $premium-conditions:
      - "when ($.user.points gt 1000) and ($.user.active eq true) then #upgrade-premium"
      - "#keep-basic"
```

### Execution Flow

```
validate-user
       ↓
  age-decision
    ↓        ↓
  adult     minor
   ↓          ↓
premium    notify
decision   guardian
 ↓    ↓
up   basic
grade
```

## Example 4: Timeout and Advanced Configurations

```yaml
entry: robust-workflow

robust-workflow:
  name: 'Workflow with Timeouts'
  lambda_dir: lambdas/robust

  tree:
    process-data: validate-result
    validate-result: $validation
    retry-processing: null
    finalize-success: null
  
  states:
    process-data:
      name: process_complex_data
      type: lambda
      timeout: 300  # 5 minutes
    
    validate-result:
      name: validate_result
      type: choice
    
    retry-processing:
      name: retry_processing
      type: lambda
      timeout: 180  # 3 minutes
      
    finalize-success:
      name: finalize_success
      type: lambda
  
  vars:
    $validation:
      - "when $.result.status eq 'success' then #finalize-success"
      - "when $.attempts lt 3 then #retry-processing"
      - "#finalize-success"  # fallback
```

## Example 5: Multiple Conditions

```yaml
entry: classifier

classifier:
  name: 'Classification System'
  lambda_dir: lambdas/classifier

  tree:
    analyze-input: classify
    classify: $classification-rules
    category-a: null
    category-b: null
    category-c: null
    category-default: null
  
  states:
    analyze-input:
      name: analyze_input
      type: lambda
    
    classify:
      name: apply_rules
      type: choice
      
    category-a:
      name: process_category_a
      type: lambda
      
    category-b:
      name: process_category_b
      type: lambda
      
    category-c:
      name: process_category_c
      type: lambda
      
    category-default:
      name: process_default
      type: lambda
  
  vars:
    $classification-rules:
      - "when ($.score gt 0.8) and ($.type eq 'premium') then #category-a"
      - "when ($.score gt 0.6) and ($.user.verified eq true) then #category-b"
      - "when $.score gt 0.4 then #category-c"
      - "#category-default"  # default case
```

## Common Patterns

### 1. Final State

States that have no next state:

```yaml
tree:
  last-state: null
```

### 2. Conditional Loop

States that can return to themselves:

```yaml
vars:
  $conditional-loop:
    - "when $.continue eq true then #same-state else #next-state"
```

### 3. Default Fallback

Always include a default case in choices:

```yaml
vars:
  $conditions_1: # using default condition
    - "when $.condition1 then #state1"
    - "when $.condition2 then #state2"
    - "#default-state"
  $conditions_2: # using else
    - "when $.condition1 then #state1 else #default-state"
```

## Best Practices Tips

1. **Descriptive Names**: Use clear names for states and machines
2. **Timeouts**: Define timeouts for long operations
3. **Fallbacks**: Always have a default case in choices
4. **Modularity**: Separate complex workflows into smaller machines
5. **Documentation**: Comment complex configurations

## Validation

To validate your configuration:

```python
from core.parser_machine import StateMachineParser

parser = StateMachineParser('your-file.yml')
machine = parser.parse()

if machine:
    result = machine.run({"test": "data"})
```

## Next Steps

- Consult [YAML Configuration](yaml-configuration.md) for technical details
- See [API Reference](api-reference.md) for programmatic integration