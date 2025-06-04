"""批量處理的包裝函數"""
from typing import List, Literal, Union

def batch_process(
    source_teacher: str,
    weekday: int,
    time_range: Literal["morning", "afternoon", "full_day"],
    mode: Literal["rotation", "swap", "substitute"],
    teacher_involved: int = 2,
    page: int = 1,
    # 第一候選課程過濾條件（僅用於 rotation 和 swap 模式）
    include_weekdays: list[int | None] = [],
    exclude_weekdays: list[int | None] = [],
    include_periods: list[int | None] = [],
    exclude_periods: list[int | None] = [],
    morning_only: bool = False,
    afternoon_only: bool = False,
    destination_teacher: str | None = None,
    # 路徑過濾條件（僅用於 rotation 和 swap 模式）
    exclude_teachers: list[str | None] = [],
    # 代課模式專用參數
    source: Literal["official_website", "wiki"] = "wiki"
):
    """
    批量處理一位老師在指定時段內的所有課程調動或代課安排

    Args:
        source_teacher: 原授課教師名稱
        weekday: 星期（1-5）
        time_range: 時段範圍
            - "morning": 早上 (1-4節)
            - "afternoon": 下午 (5-8節)
            - "full_day": 整天 (1-8節)
        mode: 處理模式
            - "rotation": 輪調模式
            - "swap": 交換模式
            - "substitute": 代課模式
        teacher_involved: 參與調課的教師數量（預設為2，僅用於 rotation 和 swap 模式）
        page: 分頁頁碼（從1開始計數）
        items_per_page: 每頁顯示的結果數量

        # 以下參數僅用於 rotation 和 swap 模式
        include_weekdays: 要包含的星期清單
        exclude_weekdays: 要排除的星期清單
        include_periods: 要包含的節次清單
        exclude_periods: 要排除的節次清單
        morning_only: 是否只要早上的課（1-4節）
        afternoon_only: 是否只要下午的課（5-8節）
        destination_teacher: 目標教師名稱
        exclude_teachers: 要排除的教師清單

        # 以下參數僅用於 substitute 模式
        source: 代課資料來源
            - "official_website": 使用官方網站的資料
            - "wiki": 使用台南一中社群編寫的 Wiki 資料

    Returns:
        Union[BatchResult, BatchSubstituteResult]: 批量處理結果
    """
    if mode in ["rotation", "swap"]:
        items_per_page = 3
    elif mode == "substitute":
        items_per_page = 5
    import asyncio
    from tnfsh_class_table.ai_tools.scheduling.batch.process import (
        async_batch_process,
        async_batch_substitute
    )
    from tnfsh_class_table.ai_tools.scheduling.filter_func.base import (
        FilterParams,
        FirstCandidateCourseFilters,
        PathFilters
    )

    # 如果是代課模式
    if mode == "substitute":
        return asyncio.run(async_batch_substitute(
            source_teacher=source_teacher,
            weekday=weekday,
            time_range=time_range,
            source=source,
            page=page,
            items_per_page=items_per_page
        ))

    # 對於輪調和交換模式，需要建立過濾參數
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

    return asyncio.run(async_batch_process(
        source_teacher=source_teacher,
        weekday=weekday,
        time_range=time_range,
        mode=mode,
        teacher_involved=teacher_involved,
        page=page,
        items_per_page=items_per_page,
        filter_params=filter_params
    ))

if __name__ == "__main__":
    # 測試用例
    """
    result = batch_process(
        source_teacher="顏永進",
        weekday=2,
        time_range="morning",
        mode="rotation",
        teacher_involved=3,
        page=1,
        include_weekdays=[],
        exclude_weekdays=[],
        include_periods=[],
        exclude_periods=[],
        morning_only=False,
        afternoon_only=False,
        destination_teacher=None,
        exclude_teachers=[]
    )
    """
    result = batch_process(
        source_teacher="汪登隴",
        weekday=2,
        time_range="full_day",
        mode="substitute",
        source="wiki",
        page=1,
    )
    from google.genai import types
    from google import genai
    import os
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    fn_decl = types.FunctionDeclaration.from_callable(callable=batch_process, client=client)
    import json
    print(f"函數聲明: {json.dumps(fn_decl.to_json_dict(), indent=2, ensure_ascii=False)}")      
    print(result)