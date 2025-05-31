
from tnfsh_class_table.utils.log_func import log_func

@log_func
def get_current_time() -> str:
    """
    取得目前時間，包含年、月、日、星期、時、分、秒
    與時間相關的請求請考慮使用此工具，例如明天是今天的+1天，前天是今天的-2天等

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