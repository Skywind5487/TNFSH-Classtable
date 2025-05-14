"""實作課程輪調的搜尋演算法"""
from typing import List, Set, Optional, Generator
from .node import TeacherNode, CourseNode
from .utils import connect_neighbors, get_bwd

def bwd_check(src: CourseNode, dst: CourseNode) -> bool:
    """檢查後向移動是否合法
    不考慮路徑上的節點，只看最終狀態
    """
    course = get_bwd(src, dst)
    print(f"{'可以移動' if course is None or course.is_free else '不可移動'}")
    return course is None or course.is_free

def rotation(start: CourseNode, max_depth: int = 5) -> Generator[List[CourseNode], None, None]:
    """深度優先搜尋環路的主函式
    
    Args:
        start: 起始課程節點
        max_depth: 最大搜尋深度
        
    Yields:
        List[CourseNode]: 找到的環路，包含起點（結尾會重複一次起點）
    """
    def dfs_cycle(start: CourseNode,
              current: Optional[CourseNode] = None,
              depth: int = 0,
              path: Optional[List[CourseNode]] = None,
              visited: Optional[Set[CourseNode]] = None,
              ) -> Generator[List[CourseNode], None, None]:
        """深度優先搜尋環路
        
        Args:
            start: 起始節點（也是目標節點）
            current: 當前節點
            depth: 當前深度
            path: 當前路徑
            visited: 已訪問的節點集合
        """
        # 初始化
        if current is None:
            current = start
            print(f"\n=== DFS (深度: {depth}) ===")
            print(f"起點: {start}")
            path = [start]
            visited = set()
        
        # 最大深度限制
        if depth >= max_depth:
            print(f"達到最大深度 {max_depth}，停止搜尋")
            return

        # 遍歷當前節點的所有鄰居
        for next_course in current.neighbors:
            print(f"\n=== DFS (深度: {depth}) ===")
            if path:
                print(f"當前路徑 ({len(path)}): {' -> '.join(str(node) for node in path)}")
            print(f"檢查相鄰課程: {next_course}")
            
            # 檢查換課是否可行
            if not bwd_check(current, next_course):
                print(f"- 跳過 {next_course} (換課不可行)")
                continue
            
            # 跳過已訪問過的節點
            if next_course in visited:
                print(f"- 跳過 {next_course} (已訪問)")
                continue
                
            # 找到環路
            if next_course == start:
                complete_path = path + [start]
                print(f"\n找到環路:")
                print(f"路徑 ({len(complete_path)}): {' -> '.join(str(node) for node in complete_path)}")
                yield complete_path
                continue

            # 繼續搜索
            visited.add(next_course)
            yield from dfs_cycle(start, next_course, depth + 1, path + [next_course], visited)
            visited.remove(next_course)
            
    yield from dfs_cycle(start)

def _print_cycles(cycles):
    """以更清晰的格式輸出找到的環路"""
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
