from typing import Literal

def substitute(
        source_teacher: str,
        weekday: int,
        period: int,
        source: Literal["official_website", "wiki"],
        page: int):
    """
    尋找代課教師。
    Args:
        source_teacher: 原授課教師名稱
        weekday: 星期（1-5）
        period: 節次（1-8）
        source: 資訊來源（"official_website" 或 "wiki"）
        page: 分頁頁碼
    Raises:
        TeacherNotFoundError: 找不到指定的教師
        CourseNotFoundError: 指定的時段沒有課程
        InvalidDataError: 資料格式不正確或缺少必要資料
        ValueError: 參數錯誤或其他錯誤
    
    Returns:
        PaginatedSubstituteResult: 分頁結果，包含代課教師的詳細資訊
    """
    import asyncio
    from tnfsh_class_table.ai_tools.scheduling.substitute import async_substitute
    asyncio.run(async_substitute(source_teacher, weekday, period, source, page))
