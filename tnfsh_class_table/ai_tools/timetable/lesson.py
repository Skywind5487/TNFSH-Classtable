from typing import List, Dict
from tnfsh_class_table.utils.log_func import log_func


@log_func
def get_lesson(target: str) -> Dict[str, List[str]]:
    """
    取得指定目標的各節時間，如果想查詢二年五班，應該轉換成205輸入力
    範圍涵蓋多個年級。

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