"""
定義課程調度所需的節點類別
"""

from typing import Dict, List, Optional, TypeAlias
from dataclasses import dataclass, field
from functools import total_ordering
from tnfsh_class_table.model import class_table
from tnfsh_class_table.new_backend.crawler import Course
from tnfsh_class_table.new_backend.models import ClassTable
import logging
from tnfsh_class_table.new_backend.models import CounterPart, CourseInfo
 
logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")


@dataclass
class CourseTime:
    """代表一個時間段"""
    weekday: int # 星期幾 (1-5)
    period: int # 課節 (1-8)
    streak: int # 連堂數

    def __eq__(self, other):
        if not isinstance(other, CourseTime):
            return NotImplemented
        return (self.weekday == other.weekday and 
                self.period == other.period)
    def __hash__(self):
        return hash((self.weekday, self.period))
    

@dataclass
class TeacherNode:
    """代表一位教師的節點類別"""
    name: str
    courses: Dict[CourseTime, 'CourseNode'] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return f"Teacher({self.name})"
    
    def __eq__(self, other):
        if not isinstance(other, TeacherNode):
            return NotImplemented
        return self.name == other.name

    @classmethod
    async def fetch_cached(cls, name: str) -> "TeacherNode":
        """從快取中獲取或建立教師節點，同時處理連堂課程
        
        Args:
            name: 教師名稱
            
        Returns:
            TeacherNode: 包含該教師所有課程的節點
        """
               
        logger = logging.getLogger(__name__)
        logger.info(f"Fetching teacher node for {name}")
        
        # 建立教師節點實例
        instance = TeacherNode(name=name, courses={})
        
        # 獲取課表資料
        class_table: ClassTable = await ClassTable.fetch_cached(name)
        table = class_table.table
        
        # 追蹤連堂資訊
        current_course_node: Optional[CourseNode] = None
        current_subject: str = ""
        current_counterpart: Optional[List[CounterPart]] = None
        
        # 建立課程節點
        for weekday_index, weekday in enumerate(table):
            for period_index, course in enumerate(weekday):
                course_time = CourseTime(
                    weekday=weekday_index + 1,
                    period=period_index + 1,
                    streak=1  # 預設為1，表示單節課
                )
                
                # 處理空堂
                if course is None:
                    current_course_node = CourseNode(
                        time=course_time,
                        is_free=True,
                        class_code=None,
                        teacher_name=name,
                        teacher=instance,
                        neighbors=None
                    )
                    instance.courses[course_time] = current_course_node
                    # 重置連堂追蹤
                    current_subject = ""
                    current_counterpart = None
                    continue
                
                # 檢查是否為連堂
                is_continuous = (
                    current_course_node is not None and
                    course.subject == current_subject and 
                    course.counterpart == current_counterpart
                )
                
                if is_continuous and current_course_node is not None:
                    # 更新前一節的連堂數
                    current_course_node.time.streak += 1
                    logger.debug(f"Extended streak at {course_time}, now {current_course_node.time.streak}")
                    continue
                
                # 不是連堂，建立新節點
                current_subject = course.subject
                current_counterpart = course.counterpart
                
                # 跳過多班級課程
                if course.counterpart is not None and len(course.counterpart) > 1:
                    current_course_node = None
                    continue
                
                # 建立新的課程節點
                current_course_node = CourseNode(
                    time=course_time,
                    is_free=course.counterpart is None,
                    class_code=course.counterpart[0].participant if course.counterpart else None,
                    teacher_name=name,
                    teacher=instance,
                    neighbors=None
                )
                
                instance.courses[course_time] = current_course_node
                
                logger.debug(
                    f"Created new course node at {course_time}: "
                    f"subject={course.subject}, "
                    f"class={current_course_node.class_code}"
                )
        
        logger.info(f"Completed fetching teacher node for {name}")
        return instance
    


@total_ordering
@dataclass
class CourseNode:
    """代表一節課程的節點類別"""
    time: CourseTime
    is_free: bool = False
    class_code: Optional[str] = None
    teacher_name: Optional[str] = None
    teacher: Optional[TeacherNode] = None
    neighbors: Optional[List['CourseNode']] = None

    def __post_init__(self) -> None:
        """初始化後的處理
        
        1. 檢查時間衝突
        2. 將課程加入教師的課程表
        
        Raises:
            ValueError: 如果該時段教師已有課程
        """
        if self.teacher is None:
            logger.error("Teacher reference is None in CourseNode initialization")
            raise ValueError("Teacher cannot be None")
            
        if self.time in self.teacher.courses:
            logger.error(f"Time conflict for teacher {self.teacher.name} at {self.time}")
            raise ValueError(f"{self.teacher.name} already has course at {self.time}")
            
        logger.debug(f"Adding course to teacher {self.teacher.name} at {self.time}")
        self.teacher.courses[self.time] = self
    
    def __repr__(self) -> str:
        if self.teacher is None:
            return f"Unknown{self.time}{'_' if self.is_free else ''}"
        return f"{self.teacher.name.lower()}{self.time}{'_' if self.is_free else ''}"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CourseNode):
            return NotImplemented
        return (self.time == other.time and 
                self.teacher == other.teacher)
    
    def __lt__(self, other: "CourseNode") -> bool:
        if not isinstance(other, CourseNode):
            return NotImplemented
        # 先比較老師名稱，再比較時間
        return ((self.teacher.name, self.time) < 
                (other.teacher.name, other.time)) if self.teacher and other.teacher else False
    
    def __hash__(self) -> int:
        if self.teacher is None:
            return hash((None, self.time))
        return hash((self.teacher.name, self.time))


TeacherName: TypeAlias = str
course_node_cache: Dict[CourseTime, CourseNode] = {}
teacher_node_cache: Dict[TeacherName, TeacherNode] = {}
