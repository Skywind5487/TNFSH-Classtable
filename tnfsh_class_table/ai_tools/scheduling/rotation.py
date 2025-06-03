from __future__ import annotations
from typing import Literal, TYPE_CHECKING, Callable, List
from click import option
from pydantic import BaseModel

from tnfsh_timetable_core.scheduling.models import CourseNode
from tnfsh_class_table.ai_tools.scheduling.filter_func.filters import RotationFirstCandidateFilter, TeacherPathFilter

if TYPE_CHECKING:
    from tnfsh_class_table.ai_tools.scheduling.models import PaginatedResult

from tnfsh_timetable_core import TNFSHTimetableCore 
core = TNFSHTimetableCore()
logger = core.get_logger()

from tnfsh_class_table.ai_tools.scheduling.models import random_seed
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
    logger.info(f"開始輪調課程：教師={source_teacher}, 星期={weekday}, 節次={period}, 最大深度={teacher_involved}, 頁碼={page}")
    from tnfsh_timetable_core import TNFSHTimetableCore
    core = TNFSHTimetableCore()
    options = await core.scheduling_rotation(
        teacher_name=source_teacher,
        weekday=weekday,
        period=period,
        max_depth=teacher_involved
    )
    if not options:
        raise ValueError("無法找到輪調課程，請確認教師名稱、星期和節次是否正確。")
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

    options = filtered_options

    # random shuffle paths with fixed seed
    import random
    random.seed(random_seed)  # 設定固定的 seed
    random.shuffle(options)
    random.seed()    # 重設 seed


    from math import ceil
    from tnfsh_class_table.ai_tools.scheduling.models import RotationStep, Path, PaginatedResult
    # 處理所有路徑並轉換成 RotationStep 物件
    rotation_paths = []
    for path in options:
        path_steps = []        
        for j in range(len(path)-1):
            node1, node2 = path[j], path[j+1]
            step = await RotationStep.create(node1, node2, j)
            path_steps.append(step)
        rotation_paths.append(Path(route=path_steps, route_id=len(rotation_paths) + 1))    # 創建分頁結果
    total_pages = ceil(len(rotation_paths) / items_per_page)
    result = PaginatedResult(
        target=source_teacher,
        mode="rotation",
        weekday=weekday,
        period=period,
        current_page=page,
        total_pages=total_pages,
        options=rotation_paths,
        items_per_page=items_per_page
    )
    
    # 返回指定頁碼的結果
    logger.debug(f"輪調課程結果：總頁數={total_pages}, 頁碼={page}, 項目數={len(rotation_paths)}")
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