from typing import List, Set


class TeacherNode:
    def __init__(self, name):
        self.name: str = name
        self.courses: List['CourseNode'] = []

class CourseNode:
    def __init__(self, time: str, teacher: TeacherNode, is_free: bool = False):
        self.is_free: bool = is_free
        self.time:str = time
        self.teacher: TeacherNode = teacher
        self.neighbors: List['CourseNode'] = []

    def __repr__(self):
        # 獲取物件在程式碼中的名稱
        import gc
        for var in gc.get_referrers(self):
            if isinstance(var, dict):
                for k, v in var.items():
                    if v is self:
                        return k
        return f"{self.teacher.name}{self.time}"  # 如果找不到變數名稱，就返回預設格式

def connect_neighbors(neighbors: List[CourseNode]):
    """連接課程節點的鄰居"""
    for course in neighbors:
        course.neighbors = [n for n in neighbors if n != course]

def bwd_check(src: CourseNode, dst: CourseNode):
    # 目標課程 dst 的時間不能與 src 的老師已有課衝突
    for c in src.teacher.courses:
        if c.time == dst.time and c.is_free is False:
            return False
    return True

def dfs_cycle(start: CourseNode,
              current: CourseNode = None,
              depth: int = 0,
              path: List[CourseNode] = None,
              visited: Set[CourseNode] = None):
    """使用深度優先搜索（DFS）來尋找換課環路
    
    Args:
        start (CourseNode): 起始課程節點
        current (CourseNode, optional): 當前課程節點. Defaults to None.
        depth (int, optional): 當前搜索深度. Defaults to 0.
        path (List[CourseNode], optional): 目前經過的路徑. Defaults to None.
        visited (Set[CourseNode], optional): 已訪問過的節點集合. Defaults to None.

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
A.courses = [a1, a2, a3, a4]

b1 = CourseNode('1', B, is_free=True)
b2 = CourseNode('2', B)
b3 = CourseNode('3', B, is_free=True)
b4 = CourseNode('4', B, is_free=True)
B.courses = [b1, b2, b3, b4]

c1 = CourseNode('1', C, is_free=True)
c2 = CourseNode('2', C, is_free=True)
c3 = CourseNode('3', C)
c4 = CourseNode('4', C, is_free=True)
C.courses = [c1, c2, c3, c4]

d1 = CourseNode('1', D, is_free=True)
d2 = CourseNode('2', D, is_free=True)
d3 = CourseNode('3', D, is_free=True)
d4 = CourseNode('4', D)
D.courses = [d1, d1, d3, d4]

# ✅ 建立換課環路
connect_neighbors([a1, b2, c3, d4])  # 形成閉環！

print("DFS Cycle:")
# ✅ 測試 DFS
for i, cycle in enumerate(dfs_cycle(a1)):
    # 直接打印課程節點，使用 CourseNode 的 __repr__ 方法
    print(" -> ".join(repr(course) for course in cycle))
    print(f"Cycle: {i+1}")

