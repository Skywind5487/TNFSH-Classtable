"""輪調相關功能"""
from __future__ import annotations
from typing import Literal, TYPE_CHECKING, Callable, List
from math import ceil
from click import option
from pydantic import BaseModel

from tnfsh_timetable_core.scheduling.models import CourseNode
from tnfsh_class_table.ai_tools.scheduling.filter_func.filters import RotationFirstCandidateFilter, TeacherPathFilter
from tnfsh_class_table.ai_tools.scheduling.cache import scheduling_cache, CacheKey

from tnfsh_timetable_core import TNFSHTimetableCore

core = TNFSHTimetableCore()
logger = core.get_logger()

from tnfsh_class_table.ai_tools.scheduling.models import random_seed, RotationStep, Path, PaginatedResult
from tnfsh_class_table.ai_tools.scheduling.filter_func.base import FilterParams




async def async_rotation(
        source_teacher: str, 
        weekday: int, 
        period: int, 
        teacher_involved: int, 
        page: int = 1,
        items_per_page: int = 3,
        filter_params: FilterParams = None
    ) -> PaginatedResult:
    """
    async 方法，請調用非 async 方法 `rotation` 來使用。

    Args:
        source_teacher: 原授課教師名稱
        weekday: 星期（1-5）
        period: 節次（1-8）
        teacher_involved: 參與輪調的教師總數（2-5）
        page: 分頁頁碼（從1開始計數）
        filter_params: 過濾器參數，包含：
            - source.destination_teacher: 目標教師名稱（作為第一候選的教師）
            - source: 其他第一候選課程的過濾條件
            - path: 路徑過濾條件
    """
    # logger: start
    logger.info(f"[Rotation] 開始輪調課程：教師={source_teacher}, 星期={weekday}, 節次={period}, 最大深度={teacher_involved}, 頁碼={page}")
    logger.info(f"[Rotation] 過濾條件: {filter_params}")

    scheduling = await core.fetch_scheduling()
    try:
        src_course_node = await scheduling.fetch_course_node(
            teacher_name=source_teacher, 
            weekday=weekday, 
            period=period,
            ignore_condition=False  # 忽略條件，確保能找到節點
        )
        streak = src_course_node.time.streak
    except Exception as e:
        logger.warning(f"無法找到原課程節點: {str(e)}")
        streak = 1  # 如果找不到節點，預設為 1

    # 嘗試從快取獲取結果
    cache_key = CacheKey(
        teacher_name=source_teacher,
        weekday=weekday,
        period=period,
        func_name="rotation",
        params=(teacher_involved,)
    )
    
    options = scheduling_cache.get(cache_key)
    if options is None:
        # 快取未命中，重新計算並存入快取
        options = await core.scheduling_rotation(
            teacher_name=source_teacher,
            weekday=weekday,
            period=period,
            max_depth=teacher_involved
        )
        scheduling_cache.set(cache_key, options)
        logger.debug("排課結果已快取")

    # 如果沒有選項，返回空結果
    if not options:
        logger.warning("無法找到輪調課程")
        from tnfsh_class_table.ai_tools.scheduling.models import PaginatedResult
        return PaginatedResult(
            target=source_teacher,
            mode="rotation",
            weekday=weekday,
            period=period,
            streak=streak,  # 使用從節點獲取到的或預設的 streak
            current_page=1,
            total_pages=0,
            options=[],
            items_per_page=items_per_page
        )

    # 建立過濾器
    first_candidate_filter = RotationFirstCandidateFilter(
        source_teacher, 
        weekday, 
        period,
        filters=filter_params.source if filter_params else None
    )
    
    path_filter = None
    if filter_params and filter_params.path:
        path_filter = TeacherPathFilter(filters=filter_params.path)

    # 過濾選項
    filtered_options = []
    for path in options:
        # 先檢查長度
        if len(path) != teacher_involved + 1:
            continue
            
        # 應用第一候選過濾器
        if not await first_candidate_filter.apply(path):
            continue
            
        # 應用路徑過濾器
        if path_filter and not await path_filter.apply(path):
            continue
            
        filtered_options.append(path)

    # 如果過濾後沒有結果，直接返回空結果
    if not filtered_options:
        logger.warning("過濾後沒有符合條件的輪調課程")
        from tnfsh_class_table.ai_tools.scheduling.models import PaginatedResult
        return PaginatedResult(
            target=source_teacher,
            mode="rotation",
            weekday=weekday,
            period=period,
            streak=streak,  # 使用從節點獲取到的或預設的 streak
            current_page=1,
            total_pages=0,
            options=[],
            items_per_page=items_per_page
        )

    options = filtered_options
    
    # random shuffle paths with fixed seed
    import random
    random.seed(random_seed)  # 設定固定的 seed
    random.shuffle(options)
    random.seed()    # 重設 seed


    # 處理所有路徑並轉換成 RotationStep 物件
    rotation_paths = []
    for path in options:
        path_steps = []        
        for j in range(len(path)-1):
            node1, node2 = path[j], path[j+1]
            step = await RotationStep.create(node1, node2, j)
            path_steps.append(step)
        rotation_paths.append(Path(route=path_steps, route_id=len(rotation_paths) + 1))
    
    # 如果沒有可用的路徑，返回空結果
    if not rotation_paths:
        from tnfsh_class_table.ai_tools.scheduling.models import PaginatedResult
        return PaginatedResult(
            target=source_teacher,
            mode="rotation",
            weekday=weekday,
            period=period,
            streak=streak,  # 使用從節點獲取到的或預設的 streak
            current_page=1,
            total_pages=0,
            options=[],
            items_per_page=items_per_page
        )

    # 創建分頁結果
    total_pages = ceil(len(rotation_paths) / items_per_page)
    from tnfsh_class_table.ai_tools.scheduling.models import PaginatedResult
    result = PaginatedResult(
        target=source_teacher,
        mode="rotation",
        weekday=src_course_node.time.weekday,  # 從節點獲取 weekday
        period=src_course_node.time.period,    # 從節點獲取 period
        streak=src_course_node.time.streak,    # 從節點獲取 streak
        current_page=page,
        total_pages=total_pages,
        options=rotation_paths,
        items_per_page=items_per_page
    )
    
    # 返回指定頁碼的結果
    logger.debug(f"[Rotation] 輪調課程結果：總頁數={total_pages}, 頁碼={page}, 項目數={len(rotation_paths)}")
    return result.get_page(page)


if __name__ == "__main__":
    import asyncio
    source_teacher = "顏永進"
    weekday = 1
    period = 3
    max_depth = 3
    page = 1
    
    result = asyncio.run(async_rotation(source_teacher, weekday, period, max_depth, page))
    print(result)