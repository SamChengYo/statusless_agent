from Tool import register_tool

@register_tool()
def get_time():
    """回傳當前時間的字串，格式為 YYYY-MM-DD HH:MM:SS"""

    from datetime import datetime

    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")
