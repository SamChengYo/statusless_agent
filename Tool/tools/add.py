from Tool import register_tool

@register_tool()
def add(a: int, b: int) -> int:
    """計算兩數總和"""
    return a + b
