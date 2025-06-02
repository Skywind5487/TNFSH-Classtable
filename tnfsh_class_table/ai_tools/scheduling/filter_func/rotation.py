"""主要過濾功能實作"""
from typing import List, TYPE_CHECKING
from .base import FilterParams, FilterBuilder
from .filters import (
    WeekdayFilter, 
    ExcludeWeekdayFilter,
    PeriodFilter, 
    MorningFilter,
    AfternoonFilter,
    ExcludeTeacherFilter,
    IncludeTeacherFilter
)

if TYPE_CHECKING:
    from tnfsh_class_table.ai_tools.scheduling.models import Path


def create_filter_chain(params: FilterParams):
    """根據參數建立過濾器鏈"""
    builder = FilterBuilder()

    # 源頭課程過濾條件
    source = params.source
    if source.weekdays:
        builder.add_filter(WeekdayFilter(source.weekdays))
    
    if source.exclude_weekdays:
        builder.add_filter(ExcludeWeekdayFilter(source.exclude_weekdays))

    if source.periods:
        builder.add_filter(PeriodFilter(source.periods))

    if source.morning_only:
        builder.add_filter(MorningFilter())
    
    if source.afternoon_only:
        builder.add_filter(AfternoonFilter())

    # 路徑過濾條件
    path = params.path
    if path.include_teachers:
        builder.add_filter(IncludeTeacherFilter(path.include_teachers))
    
    if path.exclude_teachers:
        builder.add_filter(ExcludeTeacherFilter(path.exclude_teachers))

    return builder.build()


def filter_rotation_paths(paths: List['Path'], params: FilterParams) -> List['Path']:
    """
    根據過濾參數篩選輪調路徑
    
    Args:
        paths: 原始路徑列表
        params: 過濾參數

    Returns:
        List[Path]: 過濾後的路徑列表
    """
    # 執行邏輯檢查
    params.logic_check()
    
    # 建立過濾器鏈
    filter_chain = create_filter_chain(params)
    
    # 如果沒有任何過濾條件，直接返回原始路徑
    if not filter_chain:
        return paths
        
    # 只遍歷一次路徑，應用所有過濾條件
    return [path for path in paths if filter_chain.apply(path)]