"""課程交換的 DFS 搜尋實作"""
from typing import Generator, List, Set
from .node import TeacherNode, CourseNode
from .utils import (
    connect_neighbors,
    get_fwd, get_bwd,
    is_free, bwd_check, fwd_check
)

def merge_paths(start: CourseNode, max_depth: int=100) -> Generator[List[CourseNode], None, None]:
    """產生完整的交換路徑
    
    搜尋策略：
    1. 對每個相鄰節點，檢查前向和後向路徑
    2. 若找到合法路徑，將前向和後向路徑拼接
    3. 路徑必須以空堂結束
    
    Args:
        start: 起始課程節點
        
    Yields:
        List[CourseNode]: 完整的交換路徑（後向路徑 + 起點 + 前向路徑）
    """
    def _dfs_swap_path(
        start: CourseNode,
        current: CourseNode | None = None,
        *,
        depth: int = 0,
        path: List[CourseNode] | None = None,
    ) -> Generator[List[CourseNode], None, None]:
        """深度優先搜尋可行的交換路徑
        
        搜尋規則：
        1. 路徑上的節點視為已釋放（freed）
        2. 遇到空堂時產生一個路徑
        3. 每次移動需檢查前向和後向的可行性
        
        Args:
            start: 起始課程節點
            current: 當前課程節點
            depth: 當前搜尋深度
            path: 當前路徑
            
        Yields:
            List[CourseNode]: 找到的合法交換路徑
        """
        print(f"\n=== DFS (深度: {depth}) ===")
        print(f"當前節點: {current or start}")
        if path:
            print(f"當前路徑 ({len(path)}): {' -> '.join(str(c) for c in path)}")

        if path is None:
            path = []
        if current is None:
            current = start

        if depth >= max_depth:
            print(f"達到最大深度 {max_depth}，停止搜尋")
            return

        if current.is_free:
            result = path + [current]
            print(f"找到空堂！產生路徑: {' -> '.join(str(c) for c in result)}")
            yield result
            return

        freed: Set[CourseNode] = set(path)
        for next_node in current.neighbors:
            if next_node == start:
                print(f"- 跳過 {next_node} (起點)")
                continue
                
            if not bwd_check(current, next_node, freed=freed):
                print(f"- 跳過 {next_node} (後向檢查失敗)")
                continue

            hop2 = get_fwd(current, next_node)
            print(f"- 前向課程: {hop2}")
            
            if hop2 is None or hop2 == start:
                print("- 跳過（前向課程無效）")
                continue

            if fwd_check(current, next_node, freed=freed):
                result = path + [current, next_node, hop2]
                print(f"- 產生路徑: {' -> '.join(str(c) for c in result)}")
                yield result
            else:
                print(f"- 繼續搜尋（從 {hop2} 開始）")
                yield from _dfs_swap_path(
                    start, hop2, 
                    depth=depth + 1, 
                    path=path + [current, next_node]
                )

    print(f"\n========= 搜尋交換路徑 =========")
    print(f"起點課程: {start}")
    
    for course in start.neighbors:
        print(f"\n檢查相鄰課程: {course}")
        
        hop2 = get_fwd(start, course)
        bwd_neighbor = get_bwd(start, course)
        
        print(f"前向課程: {hop2}")
        print(f"後向課程: {bwd_neighbor}")
        
        if hop2 is None or hop2 == start or bwd_neighbor is None:
            print("- 跳過（無效的前向或後向課程）")
            continue

        print("\n=== 搜尋後向路徑 ===")
        if bwd_check(start, course, freed=set()):
            bwd_slices = [[bwd_neighbor]]
            print("後向路徑可直接使用")
        else:
            print("開始後向深度搜尋...")
            bwd_slices = list(_dfs_swap_path(start, bwd_neighbor))

        print("\n=== 搜尋前向路徑 ===")
        if hop2.is_free:
            fwd_slices = [[course, hop2]]
            print("前向路徑是空堂")
        else:
            print("開始前向深度搜尋...")
            fwd_slices = list(_dfs_swap_path(start, hop2, path=[course]))

        print("\n=== 合併路徑 ===")
        for fwd in fwd_slices:
            for bwd in bwd_slices:
                complete_path = list(reversed(bwd)) + [start] + fwd
                print(f"完整路徑: {' -> '.join(str(c) for c in complete_path)}")
                yield complete_path

