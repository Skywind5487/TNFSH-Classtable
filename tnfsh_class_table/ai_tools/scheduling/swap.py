"""交換課程相關功能"""
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from tnfsh_class_table.ai_tools.scheduling.models import PaginatedResult


from tnfsh_timetable_core import TNFSHTimetableCore
from tnfsh_class_table.ai_tools.scheduling.filter_func.filters import SwapFirstCandidateFilter, TeacherPathFilter
from tnfsh_class_table.ai_tools.scheduling.filter_func.base import FilterParams
from tnfsh_class_table.ai_tools.scheduling.cache import scheduling_cache, CacheKey

core = TNFSHTimetableCore()
logger = core.get_logger()

from tnfsh_class_table.ai_tools.scheduling.models import random_seed



async def async_swap(
        source_teacher: str, 
        weekday: int, 
        period: int, 
        teacher_involved: int, 
        page: int = 1,
        items_per_page: int = 3,
        filter_params: 'FilterParams' = None
    ) -> "PaginatedResult":
    """
    async 方法，請調用非 async 方法 `swap` 來使用。
    """
    teacher_involved = teacher_involved - 1 # 因為 source_teacher 已經算在內了，所以實際上參與交換的教師數量是 teacher_involved - 1
    
    # logger: start
    logger.info(f"開始交換課程：教師={source_teacher}, 星期={weekday}, 節次={period}, 最大深度={teacher_involved}, 頁碼={page}")
    
    # 獲取原課程節點
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
        func_name="swap",
        params=(teacher_involved,)
    )
    
    options = scheduling_cache.get(cache_key)
    if options is None:
        # 快取未命中，重新計算並存入快取
        options = await core.scheduling_swap(
            teacher_name=source_teacher,
            weekday=weekday,
            period=period,
            max_depth=teacher_involved
        )
        scheduling_cache.set(cache_key, options)
        logger.debug("排課結果已快取")

    if not options:
        logger.warning("無法找到交換課程")
        from tnfsh_class_table.ai_tools.scheduling.models import PaginatedResult
        return PaginatedResult(
            target=source_teacher,
            mode="swap",
            weekday=weekday,
            period=period,
            streak=streak,  # 使用從節點獲取到的或預設的 streak
            current_page=1,
            total_pages=0,
            options=[],
            items_per_page=items_per_page
        )

    # 建立過濾器
    first_candidate_filter = SwapFirstCandidateFilter(
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
        # 先檢查長度 (對調路徑長度必須為 teacher_involved * 2 + 2)
        if len(path) != teacher_involved * 2 + 2:
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
        from tnfsh_class_table.ai_tools.scheduling.models import PaginatedResult
        logger.warning("過濾後沒有符合條件的交換課程")
        return PaginatedResult(
            target=source_teacher,
            mode="swap",
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

    from math import ceil
    from tnfsh_class_table.ai_tools.scheduling.models import SwapStep, Path, PaginatedResult

    # 處理所有路徑並轉換成 SwapStep 物件
    swap_paths = []
    for path in options:
        path = path[1:-1]  # 去除第一個跟最後一個
        path_steps = []
        for j in range(0, len(path)-1, 2):
            if j + 1 < len(path):  # 確保有下一個節點
                node1, node2 = path[j], path[j+1]
                step = await SwapStep.create(node1, node2, j//2)  # j//2 因為每兩個節點算一步
                path_steps.append(step)
        if path_steps:  # 只有當有步驟時才加入路徑
            swap_paths.append(Path(route=path_steps, route_id=len(swap_paths) + 1))

    # 創建分頁結果
    total_pages = ceil(len(swap_paths) / items_per_page)
    from tnfsh_class_table.ai_tools.scheduling.models import PaginatedResult
    result = PaginatedResult(
        target=source_teacher,
        mode="swap",
        weekday=src_course_node.time.weekday if src_course_node else weekday,  # 從節點獲取 weekday，如果節點不存在則使用輸入參數
        period=src_course_node.time.period if src_course_node else period,      # 從節點獲取 period，如果節點不存在則使用輸入參數
        streak=src_course_node.time.streak if src_course_node else streak,      # 從節點獲取 streak，如果節點不存在則使用預設值
        current_page=page,
        total_pages=total_pages,
        options=swap_paths,
        items_per_page=items_per_page
    )

    # 返回指定頁碼的結果
    logger.debug(f"交換課程結果：總頁數={total_pages}, 頁碼={page}, 項目數={len(swap_paths)}")
    return result.get_page(page)

if __name__ == "__main__":
    import asyncio
    source_teacher = "顏永進"
    weekday = 1
    period = 3
    max_depth = 3
    page = 1

    result = asyncio.run(async_swap(source_teacher, weekday, period, max_depth, page))
    print(result)