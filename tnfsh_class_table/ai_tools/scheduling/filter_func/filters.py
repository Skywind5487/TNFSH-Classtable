"""輪調和對調專用過濾器"""
from .base import FirstCandidateCourseFilter, FirstCandidateCourseFilters, PathFilter, PathFilters
from tnfsh_timetable_core.scheduling.models import CourseNode
from typing import List


class RotationFirstCandidateFilter(FirstCandidateCourseFilter):
    """輪調情況下的第一個課程選擇過濾器"""
    def __init__(self, src_teacher: str, weekday: int, period: int, filters: FirstCandidateCourseFilters = None, next_filter=None):
        """初始化過濾器

        Args:
            src_teacher: 源頭老師名稱
            weekday: 星期幾(1-5)
            period: 第幾節(1-8)
            filters: 第一候選課程的過濾條件
            next_filter: 下一個過濾器
        """
        super().__init__(next_filter)
        self.src_teacher = src_teacher
        self.weekday = weekday
        self.period = period
        self.filters = filters or FirstCandidateCourseFilters()
        self.source_node = None

    async def _init_source_node(self):
        """初始化源頭節點"""
        if self.source_node is None:
            from tnfsh_timetable_core import TNFSHTimetableCore
            core = TNFSHTimetableCore()
            scheduling = await core.fetch_scheduling()
            self.source_node = await scheduling.fetch_course_node(
                self.src_teacher,
                self.weekday,
                self.period,
                ignore_condition=True
            )

    def _check_condition(self, node: 'CourseNode') -> bool:
        """檢查節點是否符合過濾條件"""
        # 檢查星期
        if self.filters.weekdays and node.time.weekday not in self.filters.weekdays:
            return False
        if self.filters.exclude_weekdays and node.time.weekday in self.filters.exclude_weekdays:
            return False

        # 檢查節次
        if self.filters.periods and node.time.period not in self.filters.periods:
            return False
        if self.filters.exclude_periods and node.time.period in self.filters.exclude_periods:
            return False

        # 檢查早午時段
        if self.filters.morning_only and node.time.period > 4:
            return False
        if self.filters.afternoon_only and node.time.period <= 4:
            return False

        # 檢查目標教師
        if self.filters.destination_teacher:
            teacher_id = list(node.teachers.keys())[0] if node.teachers else None
            if teacher_id != self.filters.destination_teacher:
                from tnfsh_timetable_core import TNFSHTimetableCore
                core = TNFSHTimetableCore()
                core.get_logger().debug(f"節點 {node.short()} 的教師 {teacher_id} 不是目標教師 {self.filters.destination_teacher}")
                return False

        return True

    async def apply(self, path: 'List[CourseNode]') -> bool:
        """應用過濾器到路徑上"""
        await self._init_source_node()
        
        # 找到源頭位置
        source_index = -1
        for i, node in enumerate(path):
            if node == self.source_node:
                source_index = i
                break
                
        if source_index == -1:
            return False

        # 檢查下一個點（作為第一候選）是否符合條件
        if source_index < len(path) - 1:
            next_node = path[source_index + 1]
            # 檢查過濾條件
            if not self._check_condition(next_node):
                return False

        return True

class SwapFirstCandidateFilter(FirstCandidateCourseFilter):
    """對調情況下的第一個課程選擇過濾器"""
    def __init__(self, src_teacher: str, weekday: int, period: int, filters: FirstCandidateCourseFilters = None, next_filter=None):
        """初始化過濾器

        Args:
            src_teacher: 源頭老師名稱
            weekday: 星期幾(1-5)
            period: 第幾節(1-8)
            filters: 第一候選課程的過濾條件
            next_filter: 下一個過濾器
        """
        super().__init__(next_filter)
        self.src_teacher = src_teacher
        self.weekday = weekday
        self.period = period
        self.filters = filters or FirstCandidateCourseFilters()
        self.source_node = None

    async def _init_source_node(self):
        """初始化源頭節點"""
        if self.source_node is None:
            from tnfsh_timetable_core import TNFSHTimetableCore
            core = TNFSHTimetableCore()
            scheduling = await core.fetch_scheduling()
            self.source_node = await scheduling.fetch_course_node(
                self.src_teacher,
                self.weekday,
                self.period,
                ignore_condition=True
            )

    def _check_condition(self, node: 'CourseNode') -> bool:
        """檢查節點是否符合過濾條件"""
        # 檢查星期
        if self.filters.weekdays and node.time.weekday not in self.filters.weekdays:
            return False
        if self.filters.exclude_weekdays and node.time.weekday in self.filters.exclude_weekdays:
            return False

        # 檢查節次
        if self.filters.periods and node.time.period not in self.filters.periods:
            return False
        if self.filters.exclude_periods and node.time.period in self.filters.exclude_periods:
            return False

        # 檢查早午時段
        if self.filters.morning_only and node.time.period > 4:
            return False
        if self.filters.afternoon_only and node.time.period <= 4:
            return False

        # 檢查目標教師
        if self.filters.destination_teacher:
            teacher_id = list(node.teachers.keys())[0] if node.teachers else None
            if teacher_id != self.filters.destination_teacher:
                from tnfsh_timetable_core import TNFSHTimetableCore
                core = TNFSHTimetableCore()
                core.get_logger().debug(f"節點 {node.short()} 的教師 {teacher_id} 不是目標教師 {self.filters.destination_teacher}")
                return False

        return True

    async def apply(self, path: 'List[CourseNode]') -> bool:
        """應用過濾器到路徑上"""
        await self._init_source_node()
        
        # 找到源頭節點在路徑中的位置
        source_index = -1
        for i, node in enumerate(path):
            if node == self.source_node:
                source_index = i
                break

        if source_index == -1:
            return False

        
        if source_index < len(path) - 1:
            # 檢查第一候選是否符合條件
            next_node = path[source_index + 1]
            if not self._check_condition(next_node):
                return False
            
            # 1. 檢查前一個節點是否為空堂
            previous_node = path[source_index - 1] if source_index > 0 else None
            if previous_node and previous_node.is_free:
                if source_index > 0:
                    # 如果是空堂，不需要做額外檢查
                    return True
                
            # 2. 檢查前二個節點是否符合對調條件
            previous_2_hop_node = path[source_index - 2] if source_index > 1 else None
            if not self._check_condition(previous_2_hop_node):
                return False

        return True

class TeacherPathFilter(PathFilter):
    """路徑上的教師過濾器（適用於輪調和對調）"""
    def __init__(self, filters: PathFilters = None, next_filter=None):
        super().__init__(next_filter)
        self.filters = filters or PathFilters()
        from tnfsh_timetable_core import TNFSHTimetableCore
        self.core = TNFSHTimetableCore()

    def _get_teacher_id(self, node: CourseNode) -> str:
        """取得節點的教師 ID"""
        if not node.teachers:
            return None
        return list(node.teachers.keys())[0]

    def _check_condition(self, node: CourseNode) -> bool:
        """檢查節點是否符合教師過濾條件"""
        teacher_id = self._get_teacher_id(node)
        if not teacher_id:
            return True  # 允許空堂

        if self.filters.exclude_teachers and teacher_id in self.filters.exclude_teachers:
            self.core.get_logger().debug(f"節點 {node} 的教師 {teacher_id} 在排除的教師清單中")
            return False

        return True

    async def apply(self, path: List[CourseNode]) -> bool:
        """檢查整條路徑是否符合過濾條件"""
        if not path:
            return True

        for node in path:
            if not self._check_condition(node):
                return False

        return True