from typing import Callable

TOOL_FUNCTIONS = {}

def register_tool(name: str = None):
    def decorator(func: Callable):
        tool_name = name or func.__name__
        TOOL_FUNCTIONS[tool_name] = func
        return func

    if callable(name):
        return decorator(name)
    return decorator

def get_registered_tools():
    return TOOL_FUNCTIONS
