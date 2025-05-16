from Tool import register_tool

@register_tool()
def get_current_weather(location: str, unit: str = "celsius") -> str:
    """取得指定城市的即時天氣"""

    return f"{location} 現在天氣是 28 度（單位：{unit}）"
