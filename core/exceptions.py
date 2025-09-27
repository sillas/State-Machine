class StateNotFoundError(Exception):
    """Raised when a specific state is not found in the state machine."""
    pass


class StateMachineExecutionError(Exception):
    """Raised for general errors during state machine execution."""
    pass


class JSONPathNotFound(Exception):
    """Raise for JSONPath not found"""
    pass
