from typing import Literal
from venv import logger

def substitute(
        source_teacher: str,
        weekday: int,
        period: int,
        source: str,
        page: int):
    """
    尋找代課教師。
    
    Args:
        source_teacher: 原授課教師名稱
        weekday: 星期（1-5）
        period: 節次（1-8）
        source: 資訊來源（"official_website" 或 "wiki"）
            - "official_website": 使用官方網站的資料，分類較不精確，但資料完整
            - "wiki": 使用台南一中社群編寫的 Wiki 資料，分類較精確，但資料可能不夠完整
            - 預設為 "wiki"
        page: 分頁頁碼
            - 從1開始計數，預設為1
            - 以"<當前頁碼>/<回傳的總頁碼>"形式表示

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
    result = asyncio.run(async_substitute(source_teacher, weekday, period, source, page))
    return result
if __name__ == "__main__":
    # 測試用例
    try:
        result = substitute(source_teacher="顏永進", weekday=3, period=2, source="wiki", page=1)
        print(result)
    except Exception as e:
        print(f"發生錯誤: {e}")