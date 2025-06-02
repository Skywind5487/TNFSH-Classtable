"""基礎過濾器類別和過濾器參數模型"""
from abc import ABC, abstractmethod
from typing import Set, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from tnfsh_class_table.ai_tools.scheduling.models import Path
    from tnfsh_class_table.change_class import CourseNode


class SourceFilters(BaseModel):
    """源頭課程（第一堂課）的過濾條件"""
    weekdays: Set[int] | None = Field(None, description="要包含的星期（1-5）")
    exclude_weekdays: Set[int] | None = Field(None, description="要排除的星期（1-5）")
    periods: Set[int] | None = Field(None, description="要包含的節次（1-8）")
    exclude_periods: Set[int] | None = Field(None, description="要排除的節次（1-8）")
    morning_only: bool = Field(False, description="是否只要早上的課（1-4節）")
    afternoon_only: bool = Field(False, description="是否只要下午的課（5-8節）")

    def logic_check(self) -> None:
        """
        檢查源頭課程過濾器參數是否有邏輯衝突
        Raises:
            ValueError: 如果參數有邏輯衝突
        """
        # 檢查 weekdays 和 exclude_weekdays 是否有交集
        if self.weekdays and self.exclude_weekdays and (self.weekdays & self.exclude_weekdays):
            raise ValueError("包含的星期和排除的星期不能有交集")
            
        # 檢查 periods 和 exclude_periods 是否有交集
        if self.periods and self.exclude_periods and (self.periods & self.exclude_periods):
            raise ValueError("包含的節次和排除的節次不能有交集")
            
        # 檢查 morning_only 和 afternoon_only 是否同時為 True
        if self.morning_only and self.afternoon_only:
            raise ValueError("不能同時選擇早上和下午的課程")
        
        # 僅有早上則1~4不可完全被排除
        if self.morning_only and self.exclude_periods and (self.exclude_periods >= {1, 2, 3, 4}):
            raise ValueError("僅有早上課程時，1~4節不可完全被排除")

        # 僅有下午則5~8不可完全被排除
        if self.afternoon_only and self.exclude_periods and (self.exclude_periods >= {5, 6, 7, 8}):
            raise ValueError("僅有下午課程時，5~8節不可完全被排除")


class PathFilters(BaseModel):
    """整條路徑的過濾條件"""
    exclude_teachers: Set[str] | None = Field(None, description="整條路徑上要排除的教師名單")
    include_teachers: Set[str] | None = Field(None, description="整條路徑上要包含的教師名單")

    def logic_check(self) -> None:
        """
        檢查路徑過濾器參數是否有邏輯衝突
        Raises:
            ValueError: 如果參數有邏輯衝突
        """
        # 檢查 include_teachers 和 exclude_teachers 是否有交集
        if self.include_teachers and self.exclude_teachers and (self.include_teachers & self.exclude_teachers):
            raise ValueError("包含的教師和排除的教師不能有交集")


class FilterParams(BaseModel):
    """完整的過濾參數"""
    source: SourceFilters = Field(default_factory=SourceFilters, description="源頭課程的過濾條件")
    path: PathFilters = Field(default_factory=PathFilters, description="整條路徑的過濾條件")

    def logic_check(self) -> None:
        """執行所有邏輯檢查"""
        self.source.logic_check()
        self.path.logic_check()


class BaseFilter(ABC):
    """過濾器基礎類別"""
    def __init__(self, next_filter: 'BaseFilter | None' = None):
        self.next = next_filter

    def apply(self, path: 'Path') -> bool:
        """
        應用過濾條件到路徑上
        如果不符合條件則立即返回 False
        如果符合條件且有下一個過濾器，則繼續檢查
        """
        if not self._check_condition(path):
            return False
        
        if self.next:
            return self.next.apply(path)
            
        return True

    @abstractmethod
    def _check_condition(self, path: 'Path') -> bool:
        """
        檢查路徑是否符合此過濾器的條件
        子類別必須實作此方法
        """
        pass


class SourceFilter(BaseFilter):
    """源頭課程過濾器基礎類別"""
    def _check_condition(self, path: 'Path') -> bool:
        # 只檢查路徑的第一個節點
        return self._check_source_node(path[0])

    @abstractmethod
    def _check_source_node(self, node: 'CourseNode') -> bool:
        """檢查源頭節點是否符合條件"""
        pass


class PathFilter(BaseFilter):
    """路徑過濾器基礎類別"""
    def _check_condition(self, path: 'Path') -> bool:
        # 檢查路徑上的所有節點
        return all(self._check_path_node(node) for node in path)

    @abstractmethod
    def _check_path_node(self, node: 'CourseNode') -> bool:
        """檢查路徑上的節點是否符合條件"""
        pass


class FilterBuilder:
    """過濾器建造者"""
    def __init__(self):
        self.head: BaseFilter | None = None
        self.tail: BaseFilter | None = None

    def add_filter(self, filter_: BaseFilter) -> 'FilterBuilder':
        """添加一個過濾器到鏈的尾端"""
        if not self.head:
            self.head = filter_
            self.tail = filter_
        else:
            self.tail.next = filter_
            self.tail = filter_
        return self

    def build(self) -> BaseFilter | None:
        """建立並返回過濾器鏈"""
        return self.head
