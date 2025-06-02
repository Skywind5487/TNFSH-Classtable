from calendar import c
from tnfsh_class_table.utils.log_func import log_func

@log_func
def get_timetable_index() -> dict[str, dict[str, str]]:
    """
    從源頭課表網站獲取課表索引資料，包括科目與老師名稱、其連結
    並返回一個字典，包含所有課表索引資料。

    使用場景：
        1. 使用者需要查詢特定科目的課表資訊
        2. 使用者需要了解有哪些老師
        3. 使用者希望獲取課表索引以便進一步查詢

    Args:
        None

    Returns:
        dict[str, dict[str, str]]: 課表索引資料，格式為 {科目: {老師名稱: 連結}}
    """
    from tnfsh_timetable_core import TNFSHTimetableCore
    core = TNFSHTimetableCore()
    import asyncio
    index = asyncio.run(core.fetch_index())
    return index.index

if __name__ == "__main__":
    # For testing purposes
    timetable_index = get_timetable_index()
    print(timetable_index)
    # Example output: {'數學': {'陳老師': 'https://example.com/teacher/chen', ...}, ...}