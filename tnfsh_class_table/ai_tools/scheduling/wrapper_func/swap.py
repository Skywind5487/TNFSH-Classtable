def swap(
    source_teacher: str,
    weekday: int,
    period: int,
    teacher_involved: int,
    page: int,
    # 第一候選課程過濾條件
    include_weekdays: list[int] = [],
    exclude_weekdays: list[int] = [],
    include_periods: list[int] = [],
    exclude_periods: list[int] = [],
    morning_only: bool = False,
    afternoon_only: bool = False,
    destination_teacher: str | None = None,
    # 路徑過濾條件
    exclude_teachers: list[str] = []
    
):
    """
    交換課程的AI助手。

    使用場景：
        1. 當只涉及兩位教師時，優先推薦使用交換。
        2. 需要保持課程順序時（如連續課程）。
        3. 參數可能是用在「我不要跟某個老師調」、「我不要星期三早上的(開afternoon only)」之類的

    預設值說明：
        不啟用過濾條件時，使用以下預設值：
        - include_weekdays: [] (空列表，表示不限制包含的星期)
        - exclude_weekdays: [] (空列表，表示不限制排除的星期)
        - include_periods: [] (空列表，表示不限制包含的節次)
        - exclude_periods: [] (空列表，表示不限制排除的節次)
        - morning_only: False (不限制只能早上)
        - afternoon_only: False (不限制只能下午)
        - destination_teacher: None (None表示不指定目標教師)
        - exclude_teachers: [] (空列表，表示不限制排除的教師)
        
    
    Args:
        source_teacher: 原授課教師名稱
        weekday: 星期（1-5）
        period: 節次（1-8）
        teacher_involved（2-5）: 參與交換的教師總數
        page: 分頁頁碼（從1開始計數）
        
        # 從源頭開始找到的第一個選擇的過濾條件
        include_weekdays: 要包含的星期清單，例如 [1,2,3]
        exclude_weekdays: 要排除的星期清單，例如 [4,5]
        include_periods: 要包含的節次清單，例如 [1,2,3,4]
        exclude_periods: 要排除的節次清單，例如 [5,6,7,8]
        morning_only: 是否只要早上的課（1-4節）
        afternoon_only: 是否只要下午的課（5-8節）
        destination_teacher: 目標教師名稱（作為第一候選的教師）
        
        # 過濾條件
        exclude_teachers: 要排除的教師清單

    Raises:
        ValueError: 如果無法找到交換課程，或參數不正確
        TypeError: 如果參數類型不正確

    Returns:
        PaginatedResult: 分頁結果，包含交換課程的詳細資訊

    Note:
        如果不需要使用過濾條件，可以傳入空列表([])或False。
        所有的過濾條件都是選用的，不使用時會採用預設值。
    """
    import asyncio
    from tnfsh_class_table.ai_tools.scheduling.swap import async_swap
    from tnfsh_class_table.ai_tools.scheduling.filter_func.base import FilterParams, FirstCandidateCourseFilters, PathFilters

    # 將 list 轉換成 set
    filter_params = FilterParams(
        source=FirstCandidateCourseFilters(
            weekdays=set(include_weekdays) if include_weekdays else None,
            exclude_weekdays=set(exclude_weekdays) if exclude_weekdays else None,
            periods=set(include_periods) if include_periods else None,
            exclude_periods=set(exclude_periods) if exclude_periods else None,
            morning_only=morning_only,
            afternoon_only=afternoon_only,
            destination_teacher=destination_teacher
        ),
        path=PathFilters(
            exclude_teachers=set(exclude_teachers) if exclude_teachers else None
        )
    )

    # 檢查參數邏輯
    filter_params.logic_check()
    result = asyncio.run(async_swap(
        source_teacher=source_teacher, 
        weekday=weekday, 
        period=period, 
        teacher_involved=teacher_involved, 
        page=page,
        filter_params=filter_params
    ))
    return result


if __name__ == "__main__":
    # 測試對調功能
    result = swap(
        source_teacher="顏永進",  # 替換成實際的教師名稱
        weekday=3,               # 星期三
        period=2,               # 第二節
        teacher_involved=2,      # 兩位教師參與
        page=1,                 # 第一頁結果
        include_weekdays=[4],     # 限制只能是星期四
        exclude_weekdays=[],     # 不排除任何星期
        include_periods=[],      # 不限制節次
        exclude_periods=[],      # 不排除任何節次
        morning_only=False,      # 不限制只能早上
        afternoon_only=False,    # 不限制只能下午
        exclude_teachers=[],     # 不排除任何教師
        destination_teacher="黃先明"      # 指定要找這位老師的課
    )

    print("對調結果:")
    print(f"頁數: {result.current_page}/{result.total_pages}")
    for option in result.options:
        print(f"路徑 ID: {option.route_id}")
        for step in option.route:
            print(f"路徑: {step.main_instruction}")  # 假設每個 node 有 name 屬性
