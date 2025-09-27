#!/usr/bin/env python3
"""
Test script for the cache system in parser.py
"""

from parser import parse_cond
from logger import _i
import os


def test_cache_system():
    """Test the hash-based cache invalidation system"""

    _i("=== Testing Cache System ===")

    # Test data
    choice_name = "test-choice"
    conditions = [
        "when $.user.age gt 18 then #adult",
        "when $.user.status eq 'premium' then #premium-user",
        "#default-user"
    ]

    states = {
        "adult": {"name": "adult_state"},
        "premium-user": {"name": "premium_user_state"},
        "default-user": {"name": "default_user_state"}
    }

    _i("\n--- First run (should generate new function) ---")
    cache_path1 = parse_cond(choice_name, conditions, states)

    _i(f"\nCache file created at: {cache_path1}")
    _i(f"File exists: {os.path.exists(cache_path1)}")

    _i("\n--- Second run (should use cache) ---")
    cache_path2 = parse_cond(choice_name, conditions, states)

    _i(f"\nCache paths match: {cache_path1 == cache_path2}")

    _i("\n--- Third run with different conditions (should generate new function) ---")
    modified_conditions = [
        "when $.user.age gt 21 then #adult",  # Changed age threshold
        "when $.user.status eq 'premium' then #premium-user",
        "#default-user"
    ]

    cache_path3 = parse_cond(choice_name, modified_conditions, states)

    _i(f"\nNew cache path: {cache_path3}")
    _i(f"Different from original: {cache_path1 != cache_path3}")

    _i("\n--- Fourth run with original conditions (should use first cache again) ---")
    cache_path4 = parse_cond(choice_name, conditions, states)

    _i(f"\nCache path matches original: {cache_path1 == cache_path4}")

    # Show cache directory contents
    cache_dir = os.path.join(os.path.dirname(__file__), 'conditions_cache')
    if os.path.exists(cache_dir):
        _i(f"\n--- Cache directory contents ---")
        cache_files = os.listdir(cache_dir)
        for file in sorted(cache_files):
            _i(f"  {file}")

    _i("\n=== Cache System Test Complete ===")


if __name__ == "__main__":
    test_cache_system()
