"""具體過濾器實作"""
from typing import Set
from .base import SourceFilter, PathFilter


class WeekdayFilter(SourceFilter):
    """星期過濾器（作用於源頭課程）"""
    def __init__(self, weekdays: Set[int], next_filter=None):
        super().__init__(next_filter)
        self.weekdays = weekdays

    def _check_source_node(self, node) -> bool:
        return node.weekday in self.weekdays


class ExcludeWeekdayFilter(SourceFilter):
    """排除星期過濾器（作用於源頭課程）"""
    def __init__(self, weekdays: Set[int], next_filter=None):
        super().__init__(next_filter)
        self.weekdays = weekdays

    def _check_source_node(self, node) -> bool:
        return node.weekday not in self.weekdays


class PeriodFilter(SourceFilter):
    """節次過濾器（作用於源頭課程）"""
    def __init__(self, periods: Set[int], next_filter=None):
        super().__init__(next_filter)
        self.periods = periods

    def _check_source_node(self, node) -> bool:
        return node.period in self.periods


class MorningFilter(SourceFilter):
    """早上課程過濾器（作用於源頭課程）"""
    def _check_source_node(self, node) -> bool:
        return 1 <= node.period <= 4


class AfternoonFilter(SourceFilter):
    """下午課程過濾器（作用於源頭課程）"""
    def _check_source_node(self, node) -> bool:
        return 5 <= node.period <= 8


class ExcludeTeacherFilter(PathFilter):
    """排除教師過濾器（作用於整條路徑）"""
    def __init__(self, teachers: Set[str], next_filter=None):
        super().__init__(next_filter)
        self.teachers = teachers

    def _check_path_node(self, node) -> bool:
        return node.teacher not in self.teachers


class IncludeTeacherFilter(PathFilter):
    """包含教師過濾器（作用於整條路徑）"""
    def __init__(self, teachers: Set[str], next_filter=None):
        super().__init__(next_filter)
        self.teachers = teachers

    def _check_path_node(self, node) -> bool:
        return node.teacher in self.teachers
