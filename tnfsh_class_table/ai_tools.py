from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel
from math import ceil
from typing import Literal
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
    target: str
    mode: str 
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
            current_page=page,
            mode=self.mode,
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

async def rotation(source_teacher: str, weekday: int, period: int, max_depth: int, page: int = 1) -> PaginatedResult:
    """輪調課程的AI助手"""
    from tnfsh_timetable_core import TNFSHTimetableCore
    core = TNFSHTimetableCore()
    options = await core.scheduling_rotation(
        teacher_name=source_teacher,
        weekday=weekday,
        period=period,
        max_depth=max_depth
    )
    if not options:
        raise ValueError("無法找到輪調課程，請確認教師名稱、星期和節次是否正確。")
    
    # 過濾掉深度不符合要求的路徑
    options = [path for path in options if len(path) == max_depth + 1]
    
    # random shuffle paths with fixed seed
    import random
    random.seed(random_seed)  # 設定固定的 seed
    random.shuffle(options)
    random.seed()    # 重設 seed

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
    return result.get_page(page)


async def swap(source_teacher: str, weekday: int, period: int, max_depth: int, page: int = 1) -> PaginatedResult:
    """交換課程的AI助手"""
    from tnfsh_timetable_core import TNFSHTimetableCore
    core = TNFSHTimetableCore()
    options = await core.scheduling_swap(
        teacher_name=source_teacher,
        weekday=weekday,
        period=period,
        max_depth=max_depth
    )
    if not options:
        raise ValueError("無法找到交換課程，請確認教師名稱、星期和節次是否正確。")
    
    # 過濾掉深度不符合要求的路徑
    #options = list(options)  # 確保 options 是列表
    options = [path for path in options if len(path) == max_depth * 2 + 2]
    


    # random shuffle paths with fixed seed
    import random
    random.seed(random_seed)  # 設定固定的 seed
    random.shuffle(options)
    random.seed()    # 重設 seed
    
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
    items_per_page = 3
    total_pages = ceil(len(swap_paths) / items_per_page)
    result = PaginatedResult(
        target=source_teacher,
        mode="swap",
        current_page=page,
        total_pages=total_pages,
        options=swap_paths,
        items_per_page=items_per_page
    )
    
    # 返回指定頁碼的結果
    return result.get_page(page)

class TeacherNotFoundError(Exception):
    """教師不存在時拋出的例外"""
    pass

class CourseNotFoundError(Exception):
    """課程不存在時拋出的例外"""
    pass

class InvalidDataError(Exception):
    """資料無效時拋出的例外"""
    pass

async def substitute(source_teacher:str, weekday:int, period:int, mode: Literal["official_website", "wiki"], page:int) -> PaginatedSubstituteResult:
    """尋找代課教師。

    Args:
        source_teacher: 原授課教師名稱
        weekday: 星期（1-5）
        period: 節次（1-8）
        mode: 搜尋模式（"official_website" 或 "wiki"）
        page: 分頁頁碼

    Raises:
        TeacherNotFoundError: 找不到指定的教師
        CourseNotFoundError: 指定的時段沒有課程
        InvalidDataError: 資料格式不正確或缺少必要資料
        ValueError: 參數錯誤或其他錯誤
    """

    # 驗證基本參數
    if not isinstance(weekday, int) or not 1 <= weekday <= 5:
        raise ValueError(f"無效的星期：{weekday}，必須是 1-5 之間的整數")
    if not isinstance(period, int) or not 1 <= period <= 8:
        raise ValueError(f"無效的節次：{period}，必須是 1-8 之間的整數")
    if not source_teacher:
        raise ValueError("教師名稱不能為空")


    from tnfsh_timetable_core import TNFSHTimetableCore
    core = TNFSHTimetableCore()
    src_teacher_category = None    
    if mode == 'official_website':
        forward_wiki_index = await core.fetch_index()
        reversed_wiki_index = forward_wiki_index.reverse_index
        teacher_info = reversed_wiki_index.get(source_teacher)
        
        if not teacher_info:
            logger.error(f"❌ 在官網找不到教師：{source_teacher}")
            raise TeacherNotFoundError(f"在官網找不到教師：{source_teacher}")

        src_teacher_category = teacher_info.category
        src_teacher_url = teacher_info.url
        if not src_teacher_category or not src_teacher_url:
            logger.error(f"❌ 教師 {source_teacher} 缺少必要資訊")
            raise InvalidDataError(f"教師 {source_teacher} 缺少必要資訊")
            
        src_teacher_prefix = src_teacher_url[1]
        index_index = forward_wiki_index.index
        candidate_teachers = index_index.teacher.data.get(src_teacher_category, {})
        substitute_teachers = {}
        for teacher, url in candidate_teachers.items():
            if teacher == source_teacher:
                continue
            if url[1] == src_teacher_prefix:
                substitute_teachers[teacher] = url
    elif mode == 'wiki':
        from tnfsh_wiki_teachers_core import TNFSHWikiTeachersCore
        wiki_core = TNFSHWikiTeachersCore()
        wiki_index = await wiki_core.fetch_index()
        forward_wiki_index = wiki_index.index
        reversed_wiki_index = wiki_index.reverse_index
        
        teacher_info = reversed_wiki_index.get(source_teacher)
        if not teacher_info:
            logger.error(f"❌ 在 Wiki 中找不到教師：{source_teacher}")
            raise TeacherNotFoundError(f"在 Wiki 中找不到教師 {source_teacher} 的資訊")
            
        src_teacher_category = teacher_info.category
        if not src_teacher_category:
            logger.error(f"❌ 教師 {source_teacher} 在 Wiki 中缺少類別資訊")
            raise InvalidDataError(f"教師 {source_teacher} 在 Wiki 中缺少類別資訊")
            
        logger.debug(f"📚 找到教師類別：{src_teacher_category}")
        candidate_teachers = forward_wiki_index.get(src_teacher_category, {}).teachers
        substitute_teachers = {}
        for teacher, wiki_url in candidate_teachers.items():
            if teacher == source_teacher:
                continue
            substitute_teachers[teacher] = wiki_url
        
        index = await core.fetch_index()
        reversed_index = index.reverse_index
        substitute_teachers = {
            teacher: 
            reversed_index.get(teacher, {}).url 
            for teacher in substitute_teachers.keys() 
            if reversed_wiki_index.get(teacher, None) is not None
            and reversed_index.get(teacher, None) is not None
        }
    base_url = "http://w3.tnfsh.tn.edu.tw/deanofstudies/course"   

    scheduling = await core.fetch_scheduling()
    src_course_node = await scheduling.fetch_course_node(
        teacher_name=source_teacher,
        weekday=weekday,
        period=period
    )
    
    if not src_course_node:
        logger.error(f"❌ 找不到課程節點：週{weekday}第{period}節")
        raise CourseNotFoundError(f"找不到 {source_teacher} 在週{weekday}第{period}節的課程")

    timetable = await core.fetch_timetable(target=source_teacher)
    if not timetable or not timetable.table:
        logger.error(f"❌ 無法獲取課表：{source_teacher}")
        raise InvalidDataError(f"無法獲取 {source_teacher} 的課表")

    src_course_info = timetable.table[weekday-1][period-1]
    if not src_course_info:
        logger.error(f"❌ 指定時段沒有課程：週{weekday}第{period}節")
        raise CourseNotFoundError(f"{source_teacher} 在週{weekday}第{period}節沒有課程")

    logger.debug(f"✅ 成功找到課程：{src_course_info.subject}")
    src_course_info_with_time = CourseInfoWithTime(
        subject=src_course_info.subject,
        counterpart=[
            cp.participant for cp in (src_course_info.counterpart or [])
            if cp and cp.participant
        ],
        time=StreakTime(
            weekday=weekday,
            period=period,
            streak=getattr(src_course_node.time, 'streak', 1)
        )
    )

    free_substitute_teachers = {}
    for substitute_teacher, url in substitute_teachers.items():
        try:
            
            substitute_course_node = await scheduling.fetch_course_node(
                teacher_name=substitute_teacher,
                weekday=weekday,
                period=period,
                ignore_condition=True 
            )
            
            if (
                substitute_course_node
                and substitute_course_node.is_free):
                period_delta = src_course_node.time.period - substitute_course_node.time.period
                if (
                        substitute_course_node.time.streak >=
                        period_delta + src_course_node.time.streak
                    ):
                    free_substitute_teachers[substitute_teacher] = f"{base_url}/{url}"
        except Exception as e:
            # 忽略無法獲取課程節點的教師
            logger.error(f"無法獲取 {substitute_teacher} 的課程節點: {e}")
            continue
    logger.info(f"teacher_category: {src_teacher_category}")
    # 將結果分頁
    items_per_page = 5
    total_items = len(free_substitute_teachers)
    total_pages = ceil(total_items / items_per_page)
    
    return PaginatedSubstituteResult(
        target=source_teacher,
        mode=mode,
        current_page=page,
        total_pages=total_pages,
        teacher_category=str(src_teacher_category),
        source_course=src_course_info_with_time,
        options=free_substitute_teachers,
        items_per_page=items_per_page
    ).get_page(page)


    


if __name__ == "__main__":
    import asyncio
    # 測試函數
    async def test():
        # 測試代課
        result = await substitute("顏永進", 1, 3, mode="wiki", page=1)
        print("代課結果：")
        for i in range(1, result.total_pages + 1):
            result = await substitute("顏永進", 1, 3, mode="wiki", page=i)
            print(result.model_dump_json(indent=4))

    asyncio.run(test())