
def rotation(
        source_teacher: str,
        weekday: int,
        period: int,
        teacher_involved: int,
        page: int):
    """
    輪調課程的AI助手
    Args:
        source_teacher: 原授課教師名稱
        weekday: 星期（1-5）
        period: 節次（1-8）
        teacher_involved: 參與輪調的教師數量
        page: 分頁頁碼

    Raises:
        ValueError: 如果無法找到輪調課程，或參數不正確
    
    Returns:
        PaginatedResult: 分頁結果，包含輪調課程的詳細資訊
    """
    import asyncio
    from tnfsh_class_table.ai_tools.scheduling.rotation import async_rotation
    return asyncio.run(async_rotation(source_teacher, weekday, period, teacher_involved, page))

