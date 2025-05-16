# import os
# import importlib

# # 全域工具註冊表
# TOOL_FUNCTIONS = {}

# def register_tool(name: str = None):
#     """
#     在工具函式上使用此 decorator 以註冊。
#     name: 自定義工具名稱，預設為函式名。
#     """
#     def decorator(func):
#         func._is_tool = True
#         func._tool_name = name or func.__name__
#         return func
#     return decorator

# # 動態載入 tools 資料夾下所有標記為 _is_tool 的函式
# def load_tools():
#     pkg_dir = os.path.dirname(__file__)
#     for fname in os.listdir(pkg_dir):
#         if not fname.endswith('.py') or fname == '__init__.py':
#             continue
#         mod_name = fname[:-3]
#         module = importlib.import_module(f"Tool.{mod_name}")
#         for attr in dir(module):
#             obj = getattr(module, attr)
#             if callable(obj) and getattr(obj, '_is_tool', False):
#                 TOOL_FUNCTIONS[obj._tool_name] = obj

# # 載入時立即註冊工具
# load_tools()


import os
import importlib
import sys

# 全域工具註冊表
TOOL_FUNCTIONS = {}

def register_tool(name: str = None):
    def decorator(func):
        func._is_tool = True
        func._tool_name = name or func.__name__
        return func
    return decorator

def load_tools():
    # 假設 tools 資料夾與這個檔案在同一層
    base_dir = os.path.dirname(__file__)
    tools_dir = os.path.join(base_dir, "tools")

    # 確保 tools 可以被 Python 匯入
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)

    for fname in os.listdir(tools_dir):
        if not fname.endswith(".py") or fname == "__init__.py":
            continue

        mod_name = fname[:-3]  # 移除 .py
        module = importlib.import_module(mod_name)  # 因為 tools/ 已加到 sys.path，所以直接用模組名

        for attr in dir(module):
            obj = getattr(module, attr)
            if callable(obj) and getattr(obj, "_is_tool", False):
                TOOL_FUNCTIONS[obj._tool_name] = obj

# 載入時立即註冊工具
load_tools()
