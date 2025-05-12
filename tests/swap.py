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

        if time in teacher.courses:
            raise ValueError(f"{teacher.name} already has course at time {time}")
        teacher.courses[time] = self

    def __repr__(self) -> str:
        return f"{self.teacher.name.lower()}{self.time}"  # 直接返回 "教師名稱+時間" 的格式

def connect_neighbors(neighbors: List[CourseNode]) -> None:
    """連接課程節點的鄰居
    
    Args:
        neighbors: 需要互相連接的課程節點列表
    """
    for course in neighbors:
        course.neighbors = [n for n in neighbors if n != course]

def get_fwd(src: CourseNode, dst: CourseNode) -> Optional[CourseNode]:
    """獲取目標教師在來源課程時段的課程
    
    即：目標教師在 src.time 時段的課程
    
    Args:
        src: 來源課程節點（提供時間）
        dst: 目標課程節點（提供教師）
    
    Returns:
        Optional[CourseNode]: 目標教師在該時段的課程，如果沒有則返回 None
    """
    return dst.teacher.courses.get(src.time)

def get_bwd(src: CourseNode, dst: CourseNode) -> Optional[CourseNode]:
    """獲取來源教師在目標課程時段的課程
    
    即：來源教師在 dst.time 時段的課程
    
    Args:
        src: 來源課程節點（提供教師）
        dst: 目標課程節點（提供時間）
    
    Returns:
        Optional[CourseNode]: 來源教師在該時段的課程，如果沒有則返回 None
    """
    return src.teacher.courses.get(dst.time)

def bwd_check(src: CourseNode, dst: CourseNode) -> bool:
    """檢查來源教師在目標時段是否可以上課
    
    即：檢查 src 的教師在 dst.time 時段是否沒課或是空堂
    
    Args:
        src: 來源課程節點（提供教師）
        dst: 目標課程節點（提供時間）
    
    Returns:
        bool: 如果該時段教師沒課或是空堂則返回 True，否則返回 False
    """
    course = get_bwd(src, dst)
    return course is None or course.is_free

def fwd_check(src: CourseNode, dst: CourseNode) -> bool:
    """檢查目標教師在來源時段是否可以上課
    
    即：檢查 dst 的教師在 src.time 時段是否沒課或是空堂
    
    Args:
        src: 來源課程節點（提供時間）
        dst: 目標課程節點（提供教師）
    
    Returns:
        bool: 如果該時段教師沒課或是空堂則返回 True，否則返回 False
    """
    course = get_fwd(src, dst)
    return course is None or course.is_free

from typing import List, Set, Optional, Generator

MAX_DEPTH      = 10   # 全域遞迴深度限制
SRC_BWD_LIMIT  = 1    # 起點老師最多允許 1 次 bwd 分支

def paths_bwd_side(alt: CourseNode) -> List[List[CourseNode]]:
    """
    從 alt 出發，沿『bwd_check 通過』的邊前進，
    每步都延伸 fwd 分支直到遇到 free₁。
    回傳路徑： [start, nxt, …, free₁]
    """
    results: List[List[CourseNode]] = []
    stack = [(alt, [alt], {alt})]                  # (current, path, visited)

    while stack:
        cur, p, vis = stack.pop()
        #print(f"DFS: {cur} -> {p} ({len(vis)})")
        if cur.is_free:                            # 抵達 free₁
            results.append(p)
            continue

        for nxt in cur.neighbors:
            if nxt in vis or not bwd_check(cur, nxt):
                continue                           # 只走 bwd 成功的邊
            
            next_node = get_fwd(cur, nxt)
            if next_node is None or next_node in vis:
                continue
            new_path, new_visited = (
                p + [nxt, next_node],
                vis | {nxt, next_node}
            )

            if fwd_check(cur, nxt):
                # ✅ fwd_check 成功：把新路徑立刻加入結果或續走
                results.append(new_path)
                #print(f"Add path: {new_path}")
            else:
                # ❌ fwd_check 失敗：仍要延伸 fwd 分支 (按照你「視角」需求)
                stack.append((next_node, new_path, new_visited))

    return results



def paths_fwd_side(start: CourseNode, nxt: CourseNode) -> List[List[CourseNode]]:
    """固定先踏出 nxt，再沿『合法 fwd』直到 free₂。"""
    nx = get_fwd(start, nxt)
    #print(f"paths_fwd_side: {start} -> {nxt} -> {nx}")  
    if nx is None:
        return []
    init_path = [start, nxt, nx]
    init_vis  = {start, nxt, nx}
    if nx.is_free:
        return [init_path]

    results = []
    stack = [(nx, init_path, init_vis)]
    while stack:
        cur, p, vis = stack.pop()
        for n2 in cur.neighbors:
            print(f"DFS: {cur} -> {p} -> {n2} ({len(vis)})")
            print(f"bwd_check : {bwd_check(cur, n2)}")
            if n2 in vis or not bwd_check(cur, n2):
                continue
            print(f"fwd_check : {fwd_check(cur, n2)}")
            if fwd_check(cur, n2):
                
                nn = get_fwd(cur, n2)
                print(f"DFSt: {cur} -> {p} -> {n2} -> {nn} ({len(vis)})")
                if nn is None or nn in vis: 
                    continue
                new_p = p + [n2, nn]
                new_v = vis | {n2, nn}
                results.append(new_p)
            else:
                nn = get_fwd(cur, n2)
                print(f"DFS: {cur} -> {p} -> {n2} -> {nn} ({len(vis)})")
                if nn is None or nn in vis:
                    continue
                stack.append((nn, p + [n2, nn], vis | {n2, nn}))
    return results


def swap_paths_cartesian(start: CourseNode) -> List[List[CourseNode]]:
    """滿足條件 (A)(B) 的最終路徑產生器。"""
    all_paths = []
    
    for nxt in start.neighbors:
        alt = get_bwd(start, nxt)
        if not bwd_check(start, nxt):
            #print(f"bwd_check failed: {start} -> {nxt}")
            bwd_raw = paths_bwd_side(alt)          # start → … → free₁
        else:
            if alt is None or alt in (start, nxt):
                continue
            bwd_raw = [alt]
        fwd_raw = paths_fwd_side(start, nxt)   # start → nxt → … → free₂

        # 笛卡兒積
        for b in bwd_raw:
            br = list(reversed(b))       # free₁ … start_neighbor
            #print(f"bwd: {br}, fwd: {fwd_raw}")
            if fwd_raw == []:
                all_paths.append(br + [start])    
                continue
            for f in fwd_raw:
                all_paths.append(br + f[1:])   # free₁ … start … free₂
                
    return all_paths




# ✅ 建立測資
A = TeacherNode('A')
B = TeacherNode('B')
C = TeacherNode('C')
D = TeacherNode('D')

a1 = CourseNode('1', A)
a2 = CourseNode('2', A)
a3 = CourseNode('3', A, is_free=True)
a4 = CourseNode('4', A)
a5 = CourseNode('5', A, is_free=True)


b1 = CourseNode('1', B)
b2 = CourseNode('2', B)
b3 = CourseNode('3', B)
b4 = CourseNode('4', B)
b5 = CourseNode('5', B, is_free=True)

c1 = CourseNode('1', C)
c2 = CourseNode('2', C)
c3 = CourseNode('3', C, is_free=True)
c4 = CourseNode('4', C)
c5 = CourseNode('5', C)


d1 = CourseNode('1', D, is_free=True)
d2 = CourseNode('2', D, is_free=True)
d3 = CourseNode('3', D)
d4 = CourseNode('4', D)
d5 = CourseNode('5', D)


# ✅ 建立換課環路
connect_neighbors([a1, b2])  
connect_neighbors([a2, d5])
connect_neighbors([c1, d3])
connect_neighbors([b1, c2])

print("DFS Cycle:")
# ✅ 測試 DFS
print(swap_paths_cartesian(a1))
"""

for i, cycle in enumerate(swap_paths_cartesian(a1)):
    # 直接打印課程節點，使用 CourseNode 的 __repr__ 方法
    print(" -> ".join(repr(course) for course in cycle))
    print(f"Cycle: {i+1}")
"""

