from tnfsh_class_table.utils.log_func import log_func

@log_func
def get_timetable_index() -> dict[str, dict[str, str]]:
    """
    從源頭課表網站獲取課表索引資料，包括科目與老師名稱、其連結
    Args:
        None
    """
    from tnfsh_class_table.backend import TNFSHClassTableIndex
    index = TNFSHClassTableIndex()
    return index.index