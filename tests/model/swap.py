from __future__ import annotations

from typing import List, Dict, Optional, Generator, Set

# -----------------------------------------------------------------------------
# 基本節點類別
# -----------------------------------------------------------------------------

class TeacherNode:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.courses: Dict[str, 'CourseNode'] = {}

    def __repr__(self) -> str:
        return f"Teacher({self.name})"


class CourseNode:
    def __init__(self, time: str, teacher: TeacherNode, *, is_free: bool = False) -> None:
        if time in teacher.courses:
            raise ValueError(f"{teacher.name} already has course at {time}")
        self.time: str = time
        self.teacher: TeacherNode = teacher
        self.is_free: bool = is_free
        self.neighbors: List['CourseNode'] = []
        teacher.courses[time] = self

    def __repr__(self) -> str:
        return f"{self.teacher.name.lower()}{self.time}{'_' if self.is_free else ''}"


# -----------------------------------------------------------------------------
# 工具函式
# -----------------------------------------------------------------------------

def connect_neighbors(nodes: List['CourseNode']) -> None:
    for course in nodes:
        course.neighbors = [n for n in nodes if n is not course]


def get_fwd(src: 'CourseNode', dst: 'CourseNode') -> Optional['CourseNode']:
    return dst.teacher.courses.get(src.time)


def get_bwd(src: 'CourseNode', dst: 'CourseNode') -> Optional['CourseNode']:
    return src.teacher.courses.get(dst.time)


def _is_free(course: Optional['CourseNode'], freed: Set['CourseNode']) -> bool:
    """判斷課程是否視為空堂：本身標記 is_free 或已在交換路徑中。"""
    return course is None or course.is_free or course in freed


def bwd_check(src: 'CourseNode', dst: 'CourseNode', *, freed: Set['CourseNode']) -> bool:
    return _is_free(get_bwd(src, dst), freed)


def fwd_check(src: 'CourseNode', dst: 'CourseNode', *, freed: Set['CourseNode']) -> bool:
    return _is_free(get_fwd(src, dst), freed)


# -----------------------------------------------------------------------------
# DFS 搜尋
# -----------------------------------------------------------------------------

MAX_DEPTH: int = 10


def dfs_swap_path(
    start: 'CourseNode',
    current: Optional['CourseNode'] = None,
    *,
    depth: int = 0,
    path: Optional[List['CourseNode']] = None,
) -> Generator[List['CourseNode'], None, None]:
    """列舉 *forward* 合法切片；把路徑上的節點視作『已騰空』。"""

    if path is None:
        path = []
    if current is None:
        current = start
    if depth >= MAX_DEPTH:
        return

    freed: Set['CourseNode'] = set(path)  # 這些節點已被換開，視為空堂

    for hop1 in current.neighbors:
        if hop1 == start:
            continue
        if not bwd_check(current, hop1, freed=freed):
            continue

        hop2 = get_fwd(current, hop1)
        if hop2 is None or hop2 == start:
            continue

        next_path = path + [current, hop1, hop2]
        next_freed = freed | {hop1}

        if fwd_check(current, hop1, freed=freed):
            yield next_path
        else:
            yield from dfs_swap_path(start, hop2, depth=depth + 1, path=path + [current, hop1])


# -----------------------------------------------------------------------------
# 拼接前後半路徑
# -----------------------------------------------------------------------------

def merge_paths(start: 'CourseNode') -> Generator[List['CourseNode'], None, None]:
    for course in start.neighbors:
        hop2 = get_fwd(start, course)
        if hop2 is None or hop2 == start:
            continue

        bwd_neighbor = get_bwd(start, course)
        if bwd_neighbor is None:
            continue

        # 後半段
        if bwd_check(start, course, freed=set()):
            bwd_slices = [[bwd_neighbor]]
        else:
            bwd_slices = list(dfs_swap_path(start, bwd_neighbor))

        # 前半段：start -> course 已佔用 course，故 freed={course}
        fwd_slices = list(dfs_swap_path(start, hop2, path=[course]))

        for fwd in fwd_slices:
            for bwd in bwd_slices:
                yield list(reversed(bwd)) + [start] + fwd


# -----------------------------------------------------------------------------
# Demo
# -----------------------------------------------------------------------------

def _demo() -> None:
    A = TeacherNode('A'); B = TeacherNode('B'); C = TeacherNode('C'); D = TeacherNode('D')

    # A老師的課程，大部分設為空堂
    a1 = CourseNode('1', A)  # 這節要交換，所以不是空堂
    a2 = CourseNode('2', A, is_free=True)
    a3 = CourseNode('3', A, is_free=True)
    a4 = CourseNode('4', A, is_free=True)
    a5 = CourseNode('5', A, is_free=True)

    # B老師的課程，大部分設為空堂
    b1 = CourseNode('1', B, is_free=True)
    b2 = CourseNode('2', B)  # 這節要交換，所以不是空堂
    b3 = CourseNode('3', B, is_free=True)
    b4 = CourseNode('4', B, is_free=True)
    b5 = CourseNode('5', B, is_free=True)

    # C老師的課程，大部分設為空堂
    c1 = CourseNode('1', C, is_free=True)
    c2 = CourseNode('2', C, is_free=True)
    c3 = CourseNode('3', C)  # 這節要交換，所以不是空堂
    c4 = CourseNode('4', C, is_free=True)
    c5 = CourseNode('5', C, is_free=True)

    # D老師的課程，大部分設為空堂
    d1 = CourseNode('1', D, is_free=True)
    d2 = CourseNode('2', D, is_free=True)
    d3 = CourseNode('3', D)  # 這節要交換，所以不是空堂
    d4 = CourseNode('4', D, is_free=True)
    d5 = CourseNode('5', D, is_free=True)

    # 建立課程之間可以交換的關係
    connect_neighbors([a1, b2])
    connect_neighbors([a2, d5])
    connect_neighbors([c1, d3])
    connect_neighbors([b1, c2])

    print("\n可行交換路徑 (start = a1):")
    for idx, cycle in enumerate(merge_paths(a1), 1):
        print(f"{idx:>2}. " + " -> ".join(map(str, cycle)))


if __name__ == "__main__":
    _demo()


__all__ = [
    "TeacherNode",
    "CourseNode",
    "connect_neighbors",
    "dfs_swap_path",
    "merge_paths",
]
