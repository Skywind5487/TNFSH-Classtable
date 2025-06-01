
from tnfsh_class_table.utils.log_func import log_func

@log_func
def get_current_time():
    """
    取得目前時間，包含年、月、日、星期、時、分、秒

    使用場景：
        1. 使用者需要知道目前的日期或時間
        2. 使用者詢問與時間相關的問題
        3. 使用者需要進行時間計算或比較
            - 例如：明天是今天的+1天，前天是今天的-2天等
        4. 使用者希望獲取下一節要上什麼課
    Args:
        There is no args needed.

    Returns:
        str: 目前時間
    
    Example:
        >>> get_current_time()
        "2025-03-31 Friday 17:24:31"
    """
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %A %H:%M:%S")