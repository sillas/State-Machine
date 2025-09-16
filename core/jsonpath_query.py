from typing import Any
from jsonpath_ng import parse

def jsonpath_query(obj: Any, expr: str) -> Any:
    """
    Recebe um objeto JSON (Python dict/list) e uma expressão JSONPath,
    retorna lista com os valores encontrados.
    """
    try:
        jsonpath_expr = parse(expr)
    except Exception as e:
        raise ValueError(f"Expressão JSONPath inválida: {expr}") from e

    matches = jsonpath_expr.find(obj)
    result = [match.value for match in matches]
    
    if(len(result) == 1):
        return result[0]
    
    return result
