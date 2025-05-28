from operator import index
import tnfsh_timetable_core
from typing import List, Optional
from pydantic import BaseModel
from math import ceil

class RotationStep(BaseModel):
    """輪調步驟的資料模型"""
    current_step: int
    main_instruction: str
    teacher_url_dict: dict[str, str] = {}

    @classmethod
    async def create(cls, node1, node2, current_step: int):
        """建立 RotationStep 實例的工廠方法"""
        # 取得節點資訊
        teacher1 = ','.join(t.teacher_name for t in node1.teachers.values())
        class1 = ','.join(c.class_code for c in node1.classes.values())
        teacher2 = ','.join(t.teacher_name for t in node2.teachers.values())
        class2 = ','.join(c.class_code for c in node2.classes.values())

        # 設定主要指令
        main_instruction = (
            f"將 {teacher1} 老師週{node1.time.weekday}第{node1.time.period}節的{node1.subject}"
            f"{str(node1.time.streak)+'連堂' if node1.time.streak and node1.time.streak != 1 else ''} "
            f"({class1}) 搬到 週{node2.time.weekday}第{node2.time.period}節"
            f"{str(node2.time.streak)+'連堂' if node2.time.streak and node2.time.streak != 1 else ''} ({class2})"
        )

        # 建立實例
        instance = cls(
            current_step=current_step + 1, # 步驟從1開始
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

class RotationPath(BaseModel):
    """輪調路徑的資料模型"""
    rotation_steps: List[RotationStep]

class PaginatedRotationResult(BaseModel):
    """分頁後的輪調結果"""
    target: str
    current_page: int
    total_pages: int
    items_per_page: int = 5
    paths: List[RotationPath]
    
    @property
    def total_items(self) -> int:
        return len(self.paths)
    
    def get_page(self, page: int) -> 'PaginatedRotationResult':
        """獲取指定頁碼的結果"""
        if page < 1 or page > self.total_pages:
            raise ValueError(f"頁碼必須在 1 到 {self.total_pages} 之間")
            
        start_idx = (page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        
        return PaginatedRotationResult(
            target=self.target,
            current_page=page,
            total_pages=self.total_pages,
            paths=self.paths[start_idx:end_idx],
            items_per_page=self.items_per_page
        )

async def rotation(teacher_name: str, weekday: int, period: int, max_depth: int, page: int = 1) -> PaginatedRotationResult:
    """輪調課程的AI助手"""
    from tnfsh_timetable_core import TNFSHTimetableCore
    core = TNFSHTimetableCore()
    paths = await core.scheduling_rotation(
        teacher_name=teacher_name,
        weekday=weekday,
        period=period,
        max_depth=max_depth
    )
    if not paths:
        raise ValueError("無法找到輪調課程，請確認教師名稱、星期和節次是否正確。")
    
    # 過濾掉深度不符合要求的路徑
    paths = [path for path in paths if len(path) == max_depth + 1]
    
    # random shuffle paths
    import random
    random.shuffle(paths)

    # 處理所有路徑並轉換成 RotationStep 物件
    rotation_paths = []
    for path in paths:
        path_steps = []
        for j in range(len(path)-1):
            node1, node2 = path[j], path[j+1]
            step = await RotationStep.create(node1, node2, j)
            path_steps.append(step)
        rotation_paths.append(RotationPath(rotation_steps=path_steps))

    # 創建分頁結果
    items_per_page = 5
    total_pages = ceil(len(rotation_paths) / items_per_page)
    
    result = PaginatedRotationResult(
        target=teacher_name,
        current_page=page,
        total_pages=total_pages,
        paths=rotation_paths,
        items_per_page=items_per_page
    )
    
    # 返回指定頁碼的結果
    return result.get_page(page)

if __name__ == "__main__":
    import asyncio
    # 測試函數
    async def test_rotation():
        result = await rotation("顏永進", 3, 2, max_depth=3, page=1)
        print(result.model_dump_json(indent=4))

    asyncio.run(test_rotation())