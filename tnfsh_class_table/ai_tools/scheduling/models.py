from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel
from math import ceil
from typing import Literal
from tnfsh_class_table.utils.log_func import log_func
from tnfsh_timetable_core import TNFSHTimetableCore
core = TNFSHTimetableCore()
logger = core.get_logger()

random_seed = 42  # 設定固定的隨機種子

class RotationStep(BaseModel):
    """輪調步驟的資料模型"""
    index: int
    main_instruction: str
    teacher_url_dict: dict[str, str] = {}

    @classmethod
    async def create(cls, node1, node2, index: int):
        """建立 RotationStep 實例的工廠方法"""
        # 取得節點資訊
        teacher1 = ','.join(t.teacher_name for t in node1.teachers.values())
        class1 = ','.join(c.class_code for c in node1.classes.values())
        teacher2 = ','.join(t.teacher_name for t in node2.teachers.values())
        class2 = ','.join(c.class_code for c in node2.classes.values())

        # 設定主要指令
        main_instruction = (
            f"將 {teacher1} 老師週{node1.time.weekday}第{node1.time.period}節上的{node1.subject}"
            f"{str(node1.time.streak)+'連堂' if node1.time.streak and node1.time.streak != 1 else ''} "
            f"({class1}) 搬到 週{node2.time.weekday}第{node2.time.period}節"
            f"{str(node2.time.streak)+'連堂' if node2.time.streak and node2.time.streak != 1 else ''} ({class2})"
        )

        # 建立實例
        instance = cls(
            index=index + 1, # 步驟從1開始
            main_instruction=main_instruction,
            teacher_url_dict={}
        )

        # 非同步取得教師URL
        instance.teacher_url_dict[teacher1] = await instance.fetch_teacher_url(teacher1)
        
        return instance

    async def fetch_teacher_url(self, teacher_name: str, base_url: str = None) -> str:
        """獲取教師的URL"""
        if base_url is None:
            base_url = "http://w3.tnfsh.tn.edu.tw/deanofstudies/course"
        from tnfsh_timetable_core import TNFSHTimetableCore
        core = TNFSHTimetableCore()
        index = await core.fetch_index()
        reverse_index = index.reverse_index
        url = reverse_index.get(teacher_name, "").url
        if url:
            teacher_url = f"{base_url}/{url}"
            return teacher_url
        return ""


class SwapStep(RotationStep):
    """交換步驟的資料模型，繼承自 RotationStep"""
    
    @classmethod
    async def create(cls, node1, node2, index: int):
        """建立 SwapStep 實例的工廠方法"""
        # 取得節點資訊
        teacher1 = ','.join(t.teacher_name for t in node1.teachers.values())
        class1 = ','.join(c.class_code for c in node1.classes.values())
        teacher2 = ','.join(t.teacher_name for t in node2.teachers.values())
        class2 = ','.join(c.class_code for c in node2.classes.values())

        # 設定主要指令（互換格式）
        main_instruction = (
            f"將 {teacher1} 老師週{node1.time.weekday}第{node1.time.period}節上的{node1.subject}"
            f"{str(node1.time.streak)+'連堂' if node1.time.streak and node1.time.streak != 1 else ''} "
            f"({class1}) 與 {teacher2} 老師週{node2.time.weekday}第{node2.time.period}節上的{node2.subject}"
            f"{str(node2.time.streak)+'連堂' if node2.time.streak and node2.time.streak != 1 else ''} "
            f"({class2}) 互換"
        )

        # 建立實例
        instance = cls(
            index=index + 1,  # 步驟從1開始
            main_instruction=main_instruction,
            teacher_url_dict={}
        )

        # 非同步取得教師URL
        instance.teacher_url_dict[teacher1] = await instance.fetch_teacher_url(teacher1)
        instance.teacher_url_dict[teacher2] = await instance.fetch_teacher_url(teacher2)
        
        return instance

class Path(BaseModel):
    """輪調路徑的資料模型"""
    route_id: int  # 路徑編號，從1開始
    route: List[RotationStep]
    

class PaginatedResult(BaseModel):
    """分頁後的輪調結果"""
    target: str  # 目標教師
    mode: str  # rotation或swap
    weekday: int  # 星期
    period: int  # 節次
    current_page: int
    total_pages: int
    items_per_page: int = 5
    options: List[Path]
    
    @property
    def total_items(self) -> int:
        return len(self.options)
    def get_page(self, page: int) -> 'PaginatedResult':
        """獲取指定頁碼的結果"""
        if page < 1 or page > self.total_pages:
            raise ValueError(f"頁碼必須在 1 到 {self.total_pages} 之間")
            
        start_idx = (page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        
        return PaginatedResult(
            target=self.target,
            mode=self.mode,
            weekday=self.weekday,  # 保持星期不變
            period=self.period,    # 保持節次不變
            current_page=page,
            total_pages=self.total_pages,
            options=self.options[start_idx:end_idx],
            items_per_page=self.items_per_page
        )

from tnfsh_timetable_core.timetable_slot_log_dict.models import StreakTime
from tnfsh_timetable_core.timetable.models import CourseInfo
class CourseInfoWithTime(CourseInfo):
    time: StreakTime
    counterpart: Optional[List[str]] = None  # 參與的班級或老師，包含名稱
class PaginatedSubstituteResult(BaseModel):
    """分頁後的代課結果"""
    target: str
    mode: Literal["official_website", "wiki"]
    current_page: int
    total_pages: int
    items_per_page: int = 5
    teacher_category: str  # 原老師的類別
    source_course: CourseInfoWithTime  # 原課程的資訊
    options: dict[str, str]  # 包含教師名稱和URL的字典
    
    @property
    def total_items(self) -> int:
        return len(self.options)


    def get_page(self, page: int) -> 'PaginatedSubstituteResult':
        """獲取指定頁碼的結果"""
        if page < 1 or page > self.total_pages:
            raise ValueError(f"頁碼必須在 1 到 {self.total_pages} 之間")
            
        start_idx = (page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        
        option_items = list(self.options.items())

        return PaginatedSubstituteResult(
            target=self.target,
            mode=self.mode,
            current_page=page,
            total_pages=self.total_pages,
            teacher_category=self.teacher_category,
            source_course=self.source_course,
            options={
                option[0] : option[1]
                for option in option_items[start_idx:end_idx]
            },
            items_per_page=self.items_per_page
        )


class TeacherNotFoundError(Exception):
    """教師不存在時拋出的例外"""
    pass

class CourseNotFoundError(Exception):
    """課程不存在時拋出的例外"""
    pass

class InvalidDataError(Exception):
    """資料無效時拋出的例外"""
    pass

