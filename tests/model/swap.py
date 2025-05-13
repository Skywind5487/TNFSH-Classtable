"""swap_dfs.py — Core library for DFS-based course swapping logic.

Classes
-------
TeacherNode, CourseNode

Public helpers
--------------
connect_neighbors, merge_paths

Example usage is provided in `tests/test_swap_dfs.py`.
"""
from __future__ import annotations

from typing import List, Dict, Optional, Generator, Set

__all__ = [
    "TeacherNode",
    "CourseNode",
    "connect_neighbors",
    "merge_paths",
]

# -----------------------------------------------------------------------------
# 基本節點類別
# -----------------------------------------------------------------------------

class TeacherNode:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.courses: Dict[str, "CourseNode"] = {}

    def __repr__(self) -> str:  # pragma: no cover
        return f"Teacher({self.name})"


class CourseNode:
    def __init__(self, time: str, teacher: TeacherNode, *, is_free: bool = False) -> None:
        if time in teacher.courses:
            raise ValueError(f"{teacher.name} already has course at {time}")
        self.time: str = time
        self.teacher: TeacherNode = teacher
        self.is_free: bool = is_free
        self.neighbors: List["CourseNode"] = []
        teacher.courses[time] = self

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.teacher.name.lower()}{self.time}{'_' if self.is_free else ''}"


# -----------------------------------------------------------------------------
# 工具函式
# -----------------------------------------------------------------------------

def connect_neighbors(nodes: List["CourseNode"]) -> None:
    """Fully connect a group of courses so each becomes each other's neighbor."""
    for course in nodes:
        course.neighbors = [n for n in nodes if n is not course]


def _get_fwd(src: "CourseNode", dst: "CourseNode") -> Optional["CourseNode"]:
    return dst.teacher.courses.get(src.time)


def _get_bwd(src: "CourseNode", dst: "CourseNode") -> Optional["CourseNode"]:
    return src.teacher.courses.get(dst.time)


def _is_free(course: Optional["CourseNode"], freed: Set["CourseNode"]) -> bool:
    """A course is considered free if it is None, explicitly marked free, or already freed."""
    return course is None or (course and course.is_free) or course in freed


def _bwd_check(src: "CourseNode", dst: "CourseNode", *, freed: Set["CourseNode"]) -> bool:
    return _is_free(_get_bwd(src, dst), freed)


def _fwd_check(src: "CourseNode", dst: "CourseNode", *, freed: Set["CourseNode"]) -> bool:
    return _is_free(_get_fwd(src, dst), freed)


# -----------------------------------------------------------------------------
# DFS 搜尋
# -----------------------------------------------------------------------------

_MAX_DEPTH: int = 10


def _dfs_swap_path(
    start: "CourseNode",
    current: Optional["CourseNode"] = None,
    *,
    depth: int = 0,
    path: Optional[List["CourseNode"]] = None,
) -> Generator[List["CourseNode"], None, None]:
    """Enumerate forward-legal slices, treating nodes on *path* as already freed."""
    print(f"\n=== DFS 開始 (深度: {depth}) ===")
    print(f"起點: {start}")
    print(f"當前節點: {current}")
    print(f"當前路徑: {path}")

    if path is None:
        path = []
    if current is None:
        current = start

    if depth >= _MAX_DEPTH:
        print(f"達到最大深度 {_MAX_DEPTH}，停止搜尋")
        return

    if current.is_free:
        result = path + [current]
        print(f"找到空堂！產生路徑: {' -> '.join(str(c) for c in result)}")
        yield result
        return

    freed: Set["CourseNode"] = set(path)
    print(f"已釋放的節點: {freed}")

    print(f"\n檢查 {current} 的所有相鄰節點:")
    for hop1 in current.neighbors:
        print(f"\n考慮相鄰節點 {hop1}:")
        
        if hop1 == start:
            print(f"- 跳過 {hop1} (是起點)")
            continue
            
        if not _bwd_check(current, hop1, freed=freed):
            print(f"- 跳過 {hop1} (後向檢查失敗)")
            continue

        hop2 = _get_fwd(current, hop1)
        print(f"- 前向節點 {hop2}")
        
        if hop2 is None or hop2 == start:
            print(f"- 跳過路徑 (前向節點無效)")
            continue

        if _fwd_check(current, hop1, freed=freed):
            result = path + [current, hop1, hop2]
            print(f"- 前向檢查成功，產生路徑: {' -> '.join(str(c) for c in result)}")
            yield result
        else:
            print(f"- 繼續深度搜尋，從 {hop2} 開始")
            yield from _dfs_swap_path(start, hop2, depth=depth + 1, path=path + [current, hop1])


# -----------------------------------------------------------------------------
# 拼接前後半路徑
# -----------------------------------------------------------------------------

def merge_paths(start: "CourseNode") -> Generator[List["CourseNode"], None, None]:
    """Yield complete swap paths that start and end with a free slot reached via forward moves."""
    print(f"\n========= 開始搜尋交換路徑 =========")
    print(f"起點課程: {start}")
    print(f"相鄰課程: {start.neighbors}")
    
    for course in start.neighbors:
        print(f"\n檢查相鄰課程: {course}")
        
        hop2 = _get_fwd(start, course)
        print(f"前向跳轉課程：{hop2}")
        if hop2 is None or hop2 == start:
            print("無效的前向課程，跳過")
            continue

        bwd_neighbor = _get_bwd(start, course)
        print(f"後向相鄰課程：{bwd_neighbor}")
        if bwd_neighbor is None:
            print("無效的後向課程，跳過")
            continue

        print("\n=== 搜尋後向路徑 ===")
        if _bwd_check(start, course, freed=set()):
            bwd_slices = [[bwd_neighbor]]
            print(f"後向課程可直接使用: {bwd_slices}")
        else:
            print("開始後向深度搜尋...")
            bwd_slices = list(_dfs_swap_path(start, bwd_neighbor))
            print(f"找到的後向路徑: {bwd_slices}")

        print("\n=== 搜尋前向路徑 ===")
        if hop2.is_free:
            fwd_slices = [[course, hop2]]
            print(f"前向課程是空堂，直接使用: {fwd_slices}")
        else:
            print("開始前向深度搜尋...")
            fwd_slices = list(_dfs_swap_path(start, hop2, path=[course]))
            print(f"找到的前向路徑: {fwd_slices}")

        print("\n=== 合併路徑 ===")
        for fwd in fwd_slices:
            for bwd in bwd_slices:
                complete_path = list(reversed(bwd)) + [start] + fwd
                print(f"產生完整路徑: {' -> '.join(str(c) for c in complete_path)}")
                yield complete_path

