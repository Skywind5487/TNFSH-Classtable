"""
定義課程調度所需的節點類別
"""
from typing import Dict, List
from dataclasses import dataclass, field
from functools import total_ordering

@dataclass
class TeacherNode:
    """代表一位教師的節點類別"""
    name: str
    courses: Dict[str, 'CourseNode'] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return f"Teacher({self.name})"
    
    def __eq__(self, other):
        if not isinstance(other, TeacherNode):
            return NotImplemented
        return self.name == other.name


@total_ordering
@dataclass
class CourseNode:
    """代表一節課程的節點類別"""
    time: str
    teacher: TeacherNode
    is_free: bool = False
    neighbors: List['CourseNode'] = field(default_factory=list)
    
    def __post_init__(self):
        """初始化後的處理
        
        1. 檢查時間衝突
        2. 將課程加入教師的課程表
        """
        if self.time in self.teacher.courses:
            raise ValueError(f"{self.teacher.name} already has course at {self.time}")
        self.teacher.courses[self.time] = self
    
    def __repr__(self) -> str:
        return f"{self.teacher.name.lower()}{self.time}{'_' if self.is_free else ''}"
    
    def __eq__(self, other):
        if not isinstance(other, CourseNode):
            return NotImplemented
        return (self.time == other.time and 
                self.teacher == other.teacher)
    
    def __lt__(self, other):
        if not isinstance(other, CourseNode):
            return NotImplemented
        # 先比較老師名稱，再比較時間
        return ((self.teacher.name, self.time) < 
                (other.teacher.name, other.time))
    
    def __hash__(self):
        return hash((self.teacher.name, self.time))