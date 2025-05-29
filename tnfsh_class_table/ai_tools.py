from __future__ import annotations
from typing import List, Optional
from matplotlib.pylab import rand
from pydantic import BaseModel
from math import ceil

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
    items_per_page = 5
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
    items_per_page = 5
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

if __name__ == "__main__":
    import asyncio
    # 測試函數
    async def test():
        # 測試輪調
        print("\n=== 測試輪調功能 ===")
        rotation_result = await rotation("顏永進", 3, 2, max_depth=3, page=1)
        print("輪調結果:")
        print(rotation_result.model_dump_json(indent=4))
        
        # 測試互換
        print("\n=== 測試互換功能 ===")
        swap_result = await swap("顏永進", 3, 2, max_depth=3, page=2)
        print("互換結果:")
        print(swap_result.model_dump_json(indent=4))

    asyncio.run(test())