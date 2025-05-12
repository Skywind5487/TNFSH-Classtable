from typing import List, Set, Optional, Generator, Dict, Any

class TeacherNode:
    """代表一位教師的節點類別"""
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.courses: Dict[str, 'CourseNode'] = {}  # 使用時間作為鍵的字典

class CourseNode:
    """代表一節課程的節點類別"""
    def __init__(self, time: str, teacher: TeacherNode, is_free: bool = False) -> None:
        self.is_free: bool = is_free
        self.time: str = time
        self.teacher: TeacherNode = teacher
        self.neighbors: List['CourseNode'] = []

    def __repr__(self) -> str:
        return f"{self.teacher.name.lower()}{self.time}"  # 直接返回 "教師名稱+時間" 的格式

def connect_neighbors(neighbors: List[CourseNode]) -> None:
    """連接課程節點的鄰居
    
    Args:
        neighbors: 需要互相連接的課程節點列表
    """
    for course in neighbors:
        course.neighbors = [n for n in neighbors if n != course]

def bwd_check(src: CourseNode, dst: CourseNode) -> bool:
    """檢查換課是否會造成教師課程時間衝突
    
    Args:
        src: 來源課程節點
        dst: 目標課程節點
    
    Returns:
        bool: 如果換課可行返回 True，否則返回 False
    """
    # 檢查目標時段教師是否已有課且不是空堂
    course = src.teacher.courses.get(dst.time)
    return course is None or course.is_free  # 如果該時段沒有課，可以換課

def dfs_cycle(start: CourseNode,
              current: Optional[CourseNode] = None,
              depth: int = 0,
              path: Optional[List[CourseNode]] = None,
              visited: Optional[Set[CourseNode]] = None) -> Generator[List[CourseNode], None, None]:
    """使用深度優先搜索（DFS）來尋找換課環路
    
    Args:
        start: 起始課程節點
        current: 當前課程節點
        depth: 當前搜索深度
        path: 目前經過的路徑
        visited: 已訪問過的節點集合

    Yields:
        List[CourseNode]: 找到的換課環路
    """
    # 初始化當前節點
    if current is None:
        current = start
    # 初始化路徑
    if path is None:
        path = [start]
    # 初始化已訪問集合
    if visited is None:
        visited = set()  # 注意：這裡要創建一個空集合實例

    # 設定最大深度限制，避免無限遞迴
    if depth >= 10:
        return

    # 遍歷當前節點的所有鄰居
    for next_course in current.neighbors:
        # 檢查換課是否可行（教師課程時間不衝突）
        if not bwd_check(current, next_course):
            continue
        # 跳過已訪問過的節點，避免產生小環路
        if next_course in visited:
            continue
        # 如果回到起點，就找到一個完整的換課環路
        if next_course == start:
            yield path + [start]
            continue

        # 將下一個節點加入已訪問集合
        visited.add(next_course)
        # 遞迴搜索
        yield from dfs_cycle(start, next_course, depth + 1, path + [next_course], visited)
        # 回溯時移除節點
        visited.remove(next_course)


# ✅ 建立測資
A = TeacherNode('A')
B = TeacherNode('B')
C = TeacherNode('C')
D = TeacherNode('D')

a1 = CourseNode('1', A)
a2 = CourseNode('2', A, is_free=True)
a3 = CourseNode('3', A, is_free=True)
a4 = CourseNode('4', A, is_free=True)
A.courses = {'1': a1, '2': a2, '3': a3, '4': a4}

b1 = CourseNode('1', B, is_free=True)
b2 = CourseNode('2', B)
b3 = CourseNode('3', B, is_free=True)
b4 = CourseNode('4', B, is_free=True)
B.courses = {'1': b1, '2': b2, '3': b3, '4': b4}

c1 = CourseNode('1', C, is_free=True)
c2 = CourseNode('2', C, is_free=True)
c3 = CourseNode('3', C)
c4 = CourseNode('4', C, is_free=True)
C.courses = {'1': c1, '2': c2, '3': c3, '4': c4}

d1 = CourseNode('1', D, is_free=True)
d2 = CourseNode('2', D, is_free=True)
d3 = CourseNode('3', D, is_free=True)
d4 = CourseNode('4', D)
D.courses = {'1': d1, '2': d2, '3': d3, '4': d4}

# ✅ 建立換課環路
connect_neighbors([a1, b2, c3, d4])  # 形成閉環！

print("DFS Cycle:")
# ✅ 測試 DFS
for i, cycle in enumerate(dfs_cycle(a1)):
    # 直接打印課程節點，使用 CourseNode 的 __repr__ 方法
    print(" -> ".join(repr(course) for course in cycle))
    print(f"Cycle: {i+1}")

