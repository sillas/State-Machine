"""
Exemplo avançado demonstrando o uso do JSONPath wrapper com dados mais complexos
"""

from parser import parse_cond
from demo_usage import load_cached_function_with_jsonpath
from logger import _i


def advanced_demo():
    """Demonstra uso com dados mais complexos e múltiplos JSONPaths"""

    _i("=== Advanced Demo: Complex JSONPath Usage ===")

    # Exemplo com estrutura de dados mais complexa
    choice_name = "complex-evaluation"
    conditions = [
        "when $.customer.profile.age gte 25 and $.order.total gt 100 and $.customer.tier eq 'premium' then #premium-discount",
        "when $.customer.profile.age gte 18 and $.order.total gt 50 then #standard-discount",
        "when $.customer.profile.age lt 18 then #minor-restricted",
        "when $.order.items contains 'electronics' then #electronics-promo",
        "#no-discount"
    ]

    states = {
        "premium-discount": {"name": "premium_discount_applied"},
        "standard-discount": {"name": "standard_discount_applied"},
        "minor-restricted": {"name": "minor_purchase_restricted"},
        "electronics-promo": {"name": "electronics_promotion"},
        "no-discount": {"name": "no_discount_applied"}
    }

    # Gerar/obter função cached
    _i(f"\n--- Generating cached function for '{choice_name}' ---")
    parse_cond(choice_name, conditions, states)

    # Carregar com JSONPath wrapper
    try:
        wrapper_function = load_cached_function_with_jsonpath(choice_name)
        _i("Successfully loaded complex function with JSONPath wrapper")

        # Casos de teste com dados complexos
        test_cases = [
            {
                "description": "Premium customer with high-value order",
                "data": {
                    "customer": {
                        "profile": {"age": 30, "name": "John"},
                        "tier": "premium"
                    },
                    "order": {
                        "total": 150,
                        "items": ["laptop", "mouse"]
                    }
                },
                "expected": "premium_discount_applied"
            },
            {
                "description": "Standard customer with medium-value order",
                "data": {
                    "customer": {
                        "profile": {"age": 25, "name": "Jane"},
                        "tier": "standard"
                    },
                    "order": {
                        "total": 75,
                        "items": ["book", "pen"]
                    }
                },
                "expected": "standard_discount_applied"
            },
            {
                "description": "Minor customer",
                "data": {
                    "customer": {
                        "profile": {"age": 16, "name": "Mike"},
                        "tier": "standard"
                    },
                    "order": {
                        "total": 25,
                        "items": ["game"]
                    }
                },
                "expected": "minor_purchase_restricted"
            },
            {
                "description": "Electronics promotion",
                "data": {
                    "customer": {
                        "profile": {"age": 22, "name": "Alice"},
                        "tier": "standard"
                    },
                    "order": {
                        "total": 30,
                        "items": ["electronics", "cable"]
                    }
                },
                "expected": "electronics_promotion"
            },
            {
                "description": "No discount case",
                "data": {
                    "customer": {
                        "profile": {"age": 20, "name": "Bob"},
                        "tier": "basic"
                    },
                    "order": {
                        "total": 25,
                        "items": ["book"]
                    }
                },
                "expected": "no_discount_applied"
            }
        ]

        _i("\n--- Testing complex JSONPath scenarios ---")
        for i, test_case in enumerate(test_cases, 1):
            result = wrapper_function(test_case["data"])
            status = "✓" if result == test_case["expected"] else "✗"

            _i(f"Test {i}: {test_case['description']}")
            _i(f"  Data: {test_case['data']}")
            _i(f"  Result: {result} {status}")
            _i("")

    except Exception as e:
        _i(f"Error in advanced demo: {e}")


if __name__ == "__main__":
    advanced_demo()
