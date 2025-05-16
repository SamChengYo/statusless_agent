import inspect
import typing
from typing import Callable, List, Union, get_origin, get_args
from .register import get_registered_tools

def _python_type_to_json_type(py_type):
    mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        dict: "object",
        list: "array"
    }

    if get_origin(py_type) is typing.Literal:
        return "string", list(get_args(py_type))  # enum
    return mapping.get(py_type, "string"), None

def generate_tool_schema(funcs: Union[Callable, List[Callable]]):
    if not isinstance(funcs, (list, tuple)):
        funcs = [funcs]

    result = []
    for func in funcs:
        sig = inspect.signature(func)
        properties = {}
        required = []

        for param in sig.parameters.values():
            annotation = param.annotation if param.annotation != param.empty else str
            json_type, enum_values = _python_type_to_json_type(annotation)

            prop = {"type": json_type}
            if enum_values:
                prop["enum"] = enum_values
            prop["description"] = f"{param.name} 參數"

            properties[param.name] = prop

            if param.default is inspect.Parameter.empty:
                required.append(param.name)

        result.append({
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": func.__doc__ or "",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        })

    return result

def generate_tools():
    tools = get_registered_tools().values()
    return generate_tool_schema(list(tools))
