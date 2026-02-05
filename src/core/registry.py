"""
Exercise Registry - Stores registered exercise classes.

This module is separate from factory.py to avoid circular imports.
Exercise classes register themselves by importing and using the decorator.
"""
from typing import Dict, Type, Any, Callable, List
from src.core.interfaces import Exercise


# Global registry dictionary
_exercise_registry: Dict[str, Type[Exercise]] = {}


def register_exercise(name: str) -> Callable[[Type[Exercise]], Type[Exercise]]:
    """
    Decorator to register an exercise class with the factory.
    
    Usage:
        @register_exercise("bicep curl")
        class BicepCurl(Exercise):
            ...
    
    Args:
        name: The display name/identifier for the exercise (case-insensitive).
        
    Returns:
        The decorator function.
    """
    def decorator(cls: Type[Exercise]) -> Type[Exercise]:
        _exercise_registry[name.lower()] = cls
        return cls
    return decorator


def get_exercise_class(name: str) -> Type[Exercise]:
    """
    Retrieves an exercise class by name.
    
    Args:
        name: The registered name of the exercise.
        
    Returns:
        The exercise class.
        
    Raises:
        ValueError: If the exercise is not registered.
    """
    name_lower = name.lower()
    if name_lower not in _exercise_registry:
        available = ", ".join(_exercise_registry.keys())
        raise ValueError(
            f"Exercise '{name}' not registered. Available: [{available}]"
        )
    return _exercise_registry[name_lower]


def get_available_exercises() -> List[str]:
    """
    Returns a list of all registered exercise names.
    
    Returns:
        List of exercise names (lowercase).
    """
    return list(_exercise_registry.keys())


def is_exercise_registered(name: str) -> bool:
    """
    Checks if an exercise is registered.
    
    Args:
        name: The name to check.
        
    Returns:
        True if registered, False otherwise.
    """
    return name.lower() in _exercise_registry
