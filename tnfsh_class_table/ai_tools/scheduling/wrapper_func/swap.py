def swap(
        source_teacher: str,
        weekday: int,
        period: int,
        teacher_involved: int,
        page: int):
    """
    交換課程的AI助手
    
    Args:
        source_teacher: 原授課教師名稱
        weekday: 星期（1-5）
        period: 節次（1-8）
        teacher_involved: 參與交換的其他教師數量
        page: 分頁頁碼，從1開始計數，以"<當前頁碼>/<回傳的總頁碼>"形式表示
    Raises:
        ValueError: 如果無法找到交換課程，或參數不正確
    Returns:
        PaginatedResult: 分頁結果，包含交換課程的詳細資訊
    """
    import asyncio
    from tnfsh_class_table.ai_tools.scheduling.swap import async_swap
    return asyncio.run(async_swap(source_teacher, weekday, period, teacher_involved, page))

