from typing import List, Dict
from tnfsh_class_table.utils.log_func import log_func


@log_func
def get_lesson(target: str) -> Dict[str, List[str]]:
    """
    取得指定目標的各節開始、結束時間，常與 get_timetable 搭配使用。

    使用指引:
        1. 如果想查詢二年五班，應該轉換成205輸入

    使用場景:
        1. 當使用者並不是用星期幾第幾節而是幾點詢問時
    
    Args:
        target: 班級或老師名稱

    Returns:
        Dict[str, List[str]]: 各節次時間


    Example:
        >>> get_lesson("307")
        {"第一節": ["08:30", "09:30"], "第二節": ["09:30", "10:30"]......} # 代表第一節從08:30到09:30......s
    """
    from tnfsh_class_table.backend import TNFSHClassTable
    class_table = TNFSHClassTable(target)
    return class_table.lessons