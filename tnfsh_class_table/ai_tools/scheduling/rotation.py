from __future__ import annotations
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from tnfsh_class_table.ai_tools.scheduling.models import PaginatedResult

from tnfsh_timetable_core import TNFSHTimetableCore 
core = TNFSHTimetableCore()
logger = core.get_logger()

from tnfsh_class_table.ai_tools.scheduling.models import random_seed


async def async_rotation(
        source_teacher: str, 
        weekday: int, 
        period: int, 
        teacher_involved: int, 
        page: int = 1) -> PaginatedResult:
    """
    async 方法，請調用非 async 方法 `rotation` 來使用。
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
    
    # 過濾掉深度不符合要求的路徑
    options = [path for path in options if len(path) == teacher_involved + 1]
    
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
        rotation_paths.append(Path(route=path_steps, route_id=len(rotation_paths) + 1))

    # 創建分頁結果
    items_per_page = 5 #waitingforadjustment
    total_pages = ceil(len(rotation_paths) / items_per_page)
    
    result = PaginatedResult(
        target=source_teacher,
        mode="rotation",
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