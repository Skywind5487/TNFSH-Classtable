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

def _get_bwd(src: "CourseNode", dst: "CourseNode") -> Optional["CourseNode"]:
    result = src.teacher.courses.get(dst.time)
    if result:
        print(f"{'可以移動' if result.is_free else '不可移動'} (課程狀態：{'空堂' if result.is_free else '有課'})")
    else:
        print("可以移動 (無課程)")
    return result

def bwd_check(src: CourseNode, dst: CourseNode) -> bool:
    course = _get_bwd(src, dst)
    return course is None or course.is_free

def rotation(start:CourseNode, max_depth: int = 5) -> Generator[List[CourseNode], None, None]:
    """輪調算法的主函式"""
    def dfs_cycle(start: CourseNode,
              current: Optional[CourseNode] = None,
              depth: int = 0,
              path: Optional[List[CourseNode]] = None,
              visited: Optional[Set[CourseNode]] = None,
              ) -> Generator[List[CourseNode], None, None]:
        # 初始化
        if current is None:
            current = start
            print("\n" + "="*50)
            print("開始搜索環路")
            print("="*50)
            path = [start]
            visited = set()
        
        # 最大深度限制
        if depth >= max_depth:
            return

        # 遍歷當前節點的所有鄰居
        for next_course in current.neighbors:
            print(f"\n當前路徑: {' -> '.join(str(node) for node in path)}")
            print(f"準備檢查: {current} -> {next_course}")
            
            # 檢查換課是否可行
            if not bwd_check(current, next_course):
                continue
            
            # 跳過已訪問過的節點
            if next_course in visited:
                print(f"已訪問過 {next_course}，跳過")
                continue
                
            # 找到環路
            if next_course == start:
                complete_path = path + [start]
                print("\n" + "-"*50)
                print(f"找到環路: {' -> '.join(str(node) for node in complete_path)}")
                print("-"*50)
                yield complete_path
                continue

            # 繼續搜索
            visited.add(next_course)
            yield from dfs_cycle(start, next_course, depth + 1, path + [next_course], visited)
            visited.remove(next_course)
    yield from dfs_cycle(start)

def _print_cycles(cycles):
    """
    以更清晰的格式輸出找到的環路
    """
    if not cycles:
        print("未找到任何環路")
        return

    # 依照環路長度排序
    sorted_cycles = sorted(cycles, key=len)
    print("\n=== 環路清單（依長度排序）===")
    for i, cycle in enumerate(sorted_cycles, 1):
        actual_length = len(cycle)  # 實際長度（包含重複的起點）
        depth = actual_length - 1   # 深度（不含重複的起點）
        path_str = " -> ".join(str(node) for node in cycle)
        print(f"\n環路 {i}:")
        print(f"深度: {depth}, 實際長度: {actual_length}")
        print(f"路徑: {path_str}")

    print("\n總共找到", len(cycles), "個環路")
