"""批量處理的實作函數"""
from calendar import c
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
):
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
    from tnfsh_timetable_core import TNFSHTimetableCore
    core = TNFSHTimetableCore()
    logger = core.get_logger()
    logger.info(f"[Batch] 開始批量處理：教師={source_teacher}, 星期={weekday}, 時段={time_range}, 模式={mode}, 頁碼={page}")
    logger.info(f"[Batch] 過濾條件: {filter_params}")
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

    # 取得課表確認哪些節次有課
    timetable = await core.fetch_timetable(target=source_teacher)
    scheduling = await core.fetch_scheduling()
    if not timetable or not timetable.table:
        raise ValueError(f"無法獲取教師 {source_teacher} 的課表")

    period_results = []
    current_period = end_period

    while current_period >= start_period:
        # 檢查該節是否有課
        try:
            course_node = await scheduling.fetch_course_node(
                teacher_name=source_teacher,
                weekday=weekday,
                period=current_period,
                ignore_condition=True  # 忽略條件檢查，因為我們已經在課表中確認了
            )
            logger.debug(f"current_period: {current_period}")
            logger.debug(f"course_node: {course_node.short()}")
            if course_node.time.period + course_node.time.streak - 1 < current_period:
                # 如果課程的實際節次小於當前節次，則跳過
                raise ValueError(f"可能是因為一堂課同時要教多班級等情況出現")

        except ValueError as e:
            current_period -= 1
            raise ValueError(f"無法獲取教師 {source_teacher} 在星期 {weekday} 第 {current_period} 節的課程: {str(e)}") from e
        
        # 取得課程實際的節次
        working_period = course_node.time.period if course_node.time else current_period
        
        if course_node.is_free:
            logger.debug(f"第 {current_period} 節沒有課程，跳過")
            current_period = working_period - 1
            continue

        try:
            if mode == "rotation":
                period_result = await async_rotation(
                    source_teacher=source_teacher,
                    weekday=weekday,
                    period=working_period,
                    teacher_involved=teacher_involved,
                    page=page,
                    items_per_page=items_per_page,
                    filter_params=filter_params
                )
            else:  # swap
                period_result = await async_swap(
                    source_teacher=source_teacher,
                    weekday=weekday,
                    period=working_period,
                    teacher_involved=teacher_involved,
                    page=page,
                    items_per_page=items_per_page,
                    filter_params=filter_params
                )
            period_results.append(period_result)
        except ValueError as e:
            logger.warning(f"處理第 {working_period} 節時發生錯誤: {str(e)}")

        # 如果是連續課程，跳到第一節前一節；否則往前一節
        current_period = working_period - 1    
        period_results.reverse()  # 反轉結果，因為我們是從後往前處理的
    for result_item in period_results:
        if not result_item.options:
            logger.warning(f"[Batch] 在星期 {weekday} 第 {result_item.period} 節沒有找到任何可用的調課選項")
        else:
            logger.debug(f"[Batch] 在星期 {weekday} 第 {result_item.period} 節找到 {len(result_item.options)} 個調課選項")
    logger.debug(f"[Batch] 找到 {len(period_results)} 節課程的調課結果")
    return BatchResult(
        teacher=source_teacher,
        mode=mode,
        time_range=time_range,
        teacher_involved=teacher_involved,
        period_results=period_results
    )
        
async def async_batch_substitute(
    source_teacher: str,
    weekday: int,
    time_range: Literal["morning", "afternoon", "full_day"],
    source: Literal["official_website", "wiki"] = "wiki",
    page: int = 1,
    items_per_page: int = 5
):
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
    from tnfsh_timetable_core import TNFSHTimetableCore
    core = TNFSHTimetableCore()
    logger = core.get_logger()
    logger.info(f"[Batch Substitute] 開始批量處理代課：教師={source_teacher}, 星期={weekday}, 時段={time_range}, 資料來源={source}, 頁碼={page}")
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

    # 取得課表和排課資訊
    timetable = await core.fetch_timetable(target=source_teacher)
    scheduling = await core.fetch_scheduling()
    if not timetable or not timetable.table:
        raise ValueError(f"無法獲取教師 {source_teacher} 的課表")

    period_results = []
    current_period = end_period

    while current_period >= start_period:
        # 檢查該節是否有課
        try:
            course_node = await scheduling.fetch_course_node(
                teacher_name=source_teacher,
                weekday=weekday,
                period=current_period,
                ignore_condition=True  # 忽略條件檢查，因為我們已經在課表中確認了
            )
            logger.debug(f"current_period: {current_period}")
            logger.debug(f"course_node: {course_node.short()}")
            if course_node.time.period + course_node.time.streak - 1 < current_period:
                # 如果課程的實際節次小於當前節次，則跳過
                raise ValueError(f"可能是因為一堂課同時要教多班級等情況出現")

        except ValueError as e:
            current_period -= 1
            logger.warning(f"無法獲取教師 {source_teacher} 在星期 {weekday} 第 {current_period} 節的課程: {str(e)}")
            continue

        # 取得課程實際的節次
        working_period = course_node.time.period if course_node.time else current_period
        
        if course_node.is_free:
            logger.debug(f"第 {current_period} 節沒有課程，跳過")
            current_period = working_period - 1
            continue

        try:
            result = await async_substitute(
                source_teacher=source_teacher,
                weekday=weekday,
                period=working_period,
                source=source,
                page=page,
                items_per_page=items_per_page
            )
            period_results.append(result)
        except ValueError as e:
            logger.warning(f"處理第 {working_period} 節時發生錯誤: {str(e)}")

        # 如果是連續課程，跳到第一節前一節；否則往前一節
        current_period = working_period - 1    
        period_results.reverse()  # 反轉結果，因為我們是從後往前處理的
    for result_item in period_results:
        if not result_item.options:
            logger.warning(f"[Batch Substitute] 在星期 {weekday} 第 {result_item.period} 節沒有找到任何可用的代課選項")
        else:
            logger.debug(f"[Batch Substitute] 在星期 {weekday} 第 {result_item.period} 節找到 {len(result_item.options)} 個代課選項")
    logger.debug(f"[Batch Substitute] 找到 {len(period_results)} 節課程的代課結果")
    return BatchSubstituteResult(
        teacher=source_teacher,
        mode="substitute",
        time_range=time_range,
        source=source,
        period_results=period_results
    )

if __name__ == "__main__":
    # 測試用例
    async def main():
        result = await async_batch_process(
            source_teacher="顏永進",
            weekday=2,
            time_range="morning",
            mode="rotation",
            teacher_involved=2,
            page=1,
            items_per_page=3
        )
        print(result.model_dump_json(indent=4, exclude_none=True))
    async def main2():
        result = await async_batch_substitute(
            source_teacher="顏永進",
            weekday=2,
            time_range="morning",
            source="wiki",
            page=1,
            items_per_page=5
        )
        print(result.model_dump_json(indent=4, exclude_none=True))

    #asyncio.run(main())
    asyncio.run(main2())