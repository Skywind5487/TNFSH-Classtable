"""批量處理的實作函數"""
from typing import List, Literal
import asyncio
from math import ceil

from tnfsh_class_table.ai_tools.scheduling.rotation import async_rotation
from tnfsh_class_table.ai_tools.scheduling.swap import async_swap
from tnfsh_class_table.ai_tools.scheduling.substitute import async_substitute
from tnfsh_class_table.ai_tools.scheduling.batch.models import BatchResult, BatchSubstituteResult
from tnfsh_class_table.ai_tools.scheduling.filter_func.base import FilterParams

from tnfsh_timetable_core import TNFSHTimetableCore 
core = TNFSHTimetableCore()
logger = core.get_logger()


async def async_batch_process(
    source_teacher: str,
    weekday: int,
    time_range: Literal["morning", "afternoon", "full_day"],
    mode: Literal["rotation", "swap"],
    teacher_involved: int = 2,
    page: int = 1,
    items_per_page: int = 3,
    filter_params: FilterParams = None
) -> BatchResult:
    """
    批量處理一位老師在指定時段內的所有課程調動

    Args:
        source_teacher: 原授課教師名稱
        weekday: 星期（1-5）
        time_range: 時段範圍
            - "morning": 早上 (1-4節)
            - "afternoon": 下午 (5-8節)
            - "full_day": 整天 (1-8節)
        mode: 調課模式
            - "rotation": 輪調模式
            - "swap": 交換模式
        teacher_involved: 參與調課的教師數量（預設為2）
        page: 分頁頁碼（從1開始）
        items_per_page: 每頁顯示的結果數量
        filter_params: 過濾條件參數

    Returns:
        BatchResult: 批量處理結果
    """
    # 確定要處理的節次範圍
    if time_range == "morning":
        periods = range(1, 5)
    elif time_range == "afternoon":
        periods = range(5, 9)
    else:  # full_day
        periods = range(1, 9)

    # 取得課表確認哪些節次有課
    timetable = await core.fetch_timetable(target=source_teacher)
    if not timetable or not timetable.table:
        raise ValueError(f"無法獲取教師 {source_teacher} 的課表")

    results = []
    for period in periods:
        # 檢查該節是否有課
        if not timetable.table[weekday-1][period-1]:
            continue

        try:
            if mode == "rotation":
                result = await async_rotation(
                    source_teacher=source_teacher,
                    weekday=weekday,
                    period=period,
                    teacher_involved=teacher_involved,
                    page=page,
                    items_per_page=items_per_page,
                    filter_params=filter_params
                )
            else:  # swap
                result = await async_swap(
                    source_teacher=source_teacher,
                    weekday=weekday,
                    period=period,
                    teacher_involved=teacher_involved,
                    page=page,
                    items_per_page=items_per_page,
                    filter_params=filter_params
                )
            results.append(result)
        except ValueError as e:
            logger.warning(f"處理第 {period} 節時發生錯誤: {str(e)}")
            continue

    return BatchResult(
        teacher=source_teacher,
        mode=mode,
        time_range=time_range,
        results=results
    )


async def async_batch_substitute(
    source_teacher: str,
    weekday: int,
    time_range: Literal["morning", "afternoon", "full_day"],
    source: Literal["official_website", "wiki"] = "wiki",
    page: int = 1,
    items_per_page: int = 5
) -> BatchSubstituteResult:
    """
    批量處理一位老師在指定時段內的所有課程代課安排

    Args:
        source_teacher: 原授課教師名稱
        weekday: 星期（1-5）
        time_range: 時段範圍
            - "morning": 早上 (1-4節)
            - "afternoon": 下午 (5-8節)
            - "full_day": 整天 (1-8節)
        source: 資料來源
            - "official_website": 使用官方網站的資料
            - "wiki": 使用台南一中社群編寫的 Wiki 資料
        page: 分頁頁碼（從1開始）
        items_per_page: 每頁顯示的結果數量

    Returns:
        BatchSubstituteResult: 批量處理代課結果
    """
    # 確定要處理的節次範圍
    if time_range == "morning":
        periods = range(1, 5)
    elif time_range == "afternoon":
        periods = range(5, 9)
    else:  # full_day
        periods = range(1, 9)

    # 取得課表確認哪些節次有課
    timetable = await core.fetch_timetable(target=source_teacher)
    if not timetable or not timetable.table:
        raise ValueError(f"無法獲取教師 {source_teacher} 的課表")

    results = []
    for period in periods:
        # 檢查該節是否有課
        if not timetable.table[weekday-1][period-1]:
            continue

        try:
            result = await async_substitute(
                source_teacher=source_teacher,
                weekday=weekday,
                period=period,
                source=source,
                page=page,
                items_per_page=items_per_page
            )
            results.append(result)
        except ValueError as e:
            logger.warning(f"處理第 {period} 節時發生錯誤: {str(e)}")
            continue

    return BatchSubstituteResult(
        teacher=source_teacher,
        mode="substitute",
        time_range=time_range,
        results=results
    )


async def async_batch_process_backwards(
    source_teacher: str,
    weekday: int,
    time_range: Literal["morning", "afternoon", "full_day"],
    mode: Literal["rotation", "swap"],
    teacher_involved: int = 2,
    page: int = 1,
    items_per_page: int = 3,
    filter_params: FilterParams = None
) -> BatchResult:
    """
    從後往前批量處理一位老師在指定時段內的所有課程調動。
    當一節課處理完後，會跳到該課程的第一節繼續處理。

    Args:
        source_teacher: 原授課教師名稱
        weekday: 星期（1-5）
        time_range: 時段範圍
            - "morning": 早上 (1-4節)
            - "afternoon": 下午 (5-8節)
            - "full_day": 整天 (1-8節)
        mode: 調課模式
            - "rotation": 輪調模式
            - "swap": 交換模式
        teacher_involved: 參與調課的教師數量（預設為2）
        page: 分頁頁碼（從1開始）
        items_per_page: 每頁顯示的結果數量
        filter_params: 過濾條件參數

    Returns:
        BatchResult: 批量處理結果
    """
    # 確定要處理的節次範圍
    if time_range == "morning":
        start_period = 1
        end_period = 4
    elif time_range == "afternoon":
        start_period = 5
        end_period = 8
    else:  # full_day
        start_period = 1
        end_period = 8

    # 取得課表
    scheduling = await core.fetch_scheduling()
    if not scheduling:
        raise ValueError(f"無法獲取排課系統")

    # 從最後一節開始處理
    results = []
    current_period = end_period
    processed_positions = set()  # 記錄已處理過的位置

    while current_period >= start_period:
        # 取得當前課程節點
        current_node = await scheduling.fetch_course_node(
            teacher_name=source_teacher,
            weekday=weekday,
            period=current_period
        )
        
        # 如果這個位置已經處理過或沒有課程，跳到前一節
        position_key = f"{weekday}-{current_period}"
        if not current_node or position_key in processed_positions:
            current_period -= 1
            continue

        # 標記這個位置為已處理
        processed_positions.add(position_key)
        
        try:
            # 根據模式處理課程
            if mode == "rotation":
                result = await async_rotation(
                    source_teacher=source_teacher,
                    weekday=weekday,
                    period=current_period,
                    teacher_involved=teacher_involved,
                    page=page,
                    items_per_page=items_per_page,
                    filter_params=filter_params
                )
            else:  # swap
                result = await async_swap(
                    source_teacher=source_teacher,
                    weekday=weekday,
                    period=current_period,
                    teacher_involved=teacher_involved,
                    page=page,
                    items_per_page=items_per_page,
                    filter_params=filter_params
                )
            results.append(result)

            # 如果是連續的課程，跳到第一節的位置
            if current_node.time and current_node.time.period != current_period:
                # 將中間的節次都標記為已處理
                for p in range(current_node.time.period, current_period + 1):
                    processed_positions.add(f"{weekday}-{p}")
                # 跳到連續課程的第一節前一節
                current_period = current_node.time.period - 1
            else:
                current_period -= 1

        except ValueError as e:
            logger.warning(f"處理第 {current_period} 節時發生錯誤: {str(e)}")
            current_period -= 1
            continue

    return BatchResult(
        teacher=source_teacher,
        mode=mode,
        time_range=time_range,
        results=results
    )


async def async_batch_substitute_backwards(
    source_teacher: str,
    weekday: int,
    time_range: Literal["morning", "afternoon", "full_day"],
    source: Literal["official_website", "wiki"] = "wiki",
    page: int = 1,
    items_per_page: int = 5
) -> BatchSubstituteResult:
    """
    從後往前批量處理一位老師在指定時段內的所有課程代課安排。
    當一節課處理完後，會跳到該課程的第一節繼續處理。

    Args:
        source_teacher: 原授課教師名稱
        weekday: 星期（1-5）
        time_range: 時段範圍
            - "morning": 早上 (1-4節)
            - "afternoon": 下午 (5-8節)
            - "full_day": 整天 (1-8節)
        source: 資料來源
            - "official_website": 使用官方網站的資料
            - "wiki": 使用台南一中社群編寫的 Wiki 資料
        page: 分頁頁碼（從1開始）
        items_per_page: 每頁顯示的結果數量

    Returns:
        BatchSubstituteResult: 批量處理代課結果
    """
    # 確定要處理的節次範圍
    if time_range == "morning":
        start_period = 1
        end_period = 4
    elif time_range == "afternoon":
        start_period = 5
        end_period = 8
    else:  # full_day
        start_period = 1
        end_period = 8

    # 取得課表
    scheduling = await core.fetch_scheduling()
    if not scheduling:
        raise ValueError(f"無法獲取排課系統")

    # 從最後一節開始處理
    results = []
    current_period = end_period
    processed_positions = set()  # 記錄已處理過的位置

    while current_period >= start_period:
        # 取得當前課程節點
        current_node = await scheduling.fetch_course_node(
            teacher_name=source_teacher,
            weekday=weekday,
            period=current_period
        )
        
        # 如果這個位置已經處理過或沒有課程，跳到前一節
        position_key = f"{weekday}-{current_period}"
        if not current_node or position_key in processed_positions:
            current_period -= 1
            continue

        # 標記這個位置為已處理
        processed_positions.add(position_key)

        try:
            result = await async_substitute(
                source_teacher=source_teacher,
                weekday=weekday,
                period=current_period,
                source=source,
                page=page,
                items_per_page=items_per_page
            )
            results.append(result)

            # 如果是連續的課程，跳到第一節的位置
            if current_node.time and current_node.time.period != current_period:
                # 將中間的節次都標記為已處理
                for p in range(current_node.time.period, current_period + 1):
                    processed_positions.add(f"{weekday}-{p}")
                # 跳到連續課程的第一節前一節
                current_period = current_node.time.period - 1
            else:
                current_period -= 1

        except ValueError as e:
            logger.warning(f"處理第 {current_period} 節時發生錯誤: {str(e)}")
            current_period -= 1
            continue

    return BatchSubstituteResult(
        teacher=source_teacher,
        mode="substitute",
        time_range=time_range,
        results=results
    )
