import pytest
from model.swap import TeacherNode, CourseNode, connect_neighbors, merge_paths
from typing import List, Dict, Optional, Generator, Set, Tuple
import string
# -----------------------------------------------------------------------------

def _build_simple_graph():
    """Return a minimal graph matching the example in docs."""
    A = TeacherNode("A")
    B = TeacherNode("B")
    a1 = CourseNode("1", A)              # need swap
    a2 = CourseNode("2", A, is_free=True)
    b1 = CourseNode("1", B, is_free=True)
    b2 = CourseNode("2", B)              # need swap
    connect_neighbors([a1, b2])
    return a1, b1


def test_stop_at_first_free():
    start, expected_last = _build_simple_graph()
    paths = list(merge_paths(start))
    # Exactly one path & it ends at the first free slot b1_
    assert len(paths) == 1
    assert paths[0][-1] == expected_last


def test_no_path_when_isolated():
    A = TeacherNode("A"); B = TeacherNode("B")
    a1 = CourseNode("1", A)
    b2 = CourseNode("2", B)
    # no neighbors connected -> no path
    paths = list(merge_paths(a1))
    assert paths == []



def test_long_chain(n: int = 15):
    teachers = [TeacherNode(ch) for ch in string.ascii_uppercase[:n]]
    courses: Dict[str, CourseNode] = {}
    
    # 建立課程節點
    for idx, t in enumerate(teachers):
        for time in range(1, idx + 3):  # 確保 time idx+2 存在
            is_free = (time == idx + 2) or (t == teachers[-1] and time == 1)
            cid = f"{t.name}{time}"
            courses[cid] = CourseNode(str(time), t, is_free=is_free)
    
    # 列印初始課程狀態以便除錯
    print("\n課程初始狀態:")
    for t in teachers:
        course_list = [courses.get(f"{t.name}{i}") for i in range(1, n+2) if f"{t.name}{i}" in courses]
        print(f"{t.name}: {' '.join(str(c) for c in course_list)}")
    
    # 建立連接
    for idx in range(n - 1):
        start = courses[f"{teachers[idx].name}{1}"]
        end = courses[f"{teachers[idx + 1].name}{idx + 2}"]
        connect_neighbors([start, end])
        print(f"連接: {start} -> {end}")
    courses["O15"].is_free = True  # 將最後一個課程設為空堂    
    # 嘗試找出路徑
    print(courses["A1"].neighbors)
    paths = list(merge_paths(courses["A1"]))
    print("\n找到的路徑數量:", len(paths))
    
    # 檢查是否找到路徑
    assert paths == []
    
def test_demo1() -> None:
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
    paths = list(merge_paths(a1))
    for idx, cycle in enumerate(paths, 1):
        print(f"{idx:>2}. " + " -> ".join(map(str, cycle)))
    print("hi")
    # 檢查是否找到預期的路徑
    # 注意：a2 和 b1 會顯示為 a2_ 和 b1_，因為它們是空堂
    expected_path = [[a2, a1, b2, b1]]  # 預期的路徑
    assert paths == expected_path, \
        f"預期找到路徑：{expected_path}，實際找到：{paths}"
    
def test_demo2() -> None:
    A = TeacherNode('A')
    B = TeacherNode('B')
    C = TeacherNode('C')
    D = TeacherNode('D')

    # A老師的課程，大部分設為空堂
    a1 = CourseNode('1', A)  # 這節要交換，所以不是空堂
    a2 = CourseNode('2', A)
    a3 = CourseNode('3', A)
    a4 = CourseNode('4', A)
    a5 = CourseNode('5', A, is_free=True)

    # B老師的課程，大部分設為空堂
    b1 = CourseNode('1', B)
    b2 = CourseNode('2', B)  # 這節要交換，所以不是空堂
    b3 = CourseNode('3', B)
    b4 = CourseNode('4', B)
    b5 = CourseNode('5', B, is_free=True)

    # C老師的課程，大部分設為空堂
    c1 = CourseNode('1', C)
    c2 = CourseNode('2', C)
    c3 = CourseNode('3', C, is_free=True)  # 這節要交換，所以不是空堂
    c4 = CourseNode('4', C)
    c5 = CourseNode('5', C)

    # D老師的課程，大部分設為空堂
    d1 = CourseNode('1', D, is_free=True)
    d2 = CourseNode('2', D, is_free=True)
    d3 = CourseNode('3', D)  # 這節要交換，所以不是空堂
    d4 = CourseNode('4', D)
    d5 = CourseNode('5', D)

    # 建立課程之間可以交換的關係
    connect_neighbors([a1, b2])
    connect_neighbors([a2, d5])
    connect_neighbors([c1, d3])
    connect_neighbors([b1, c2])
    
    print("\n可行交換路徑 (start = a1):")
    paths = list(merge_paths(a1))
    for idx, cycle in enumerate(paths, 1):
        print(f"{idx:>2}. " + " -> ".join(map(str, cycle)))
    print("hi")
    # 檢查是否找到預期的路徑
    # 注意：a2 和 b1 會顯示為 a2_ 和 b1_，因為它們是空堂
    expected_path = [[d2, d5, a2, a1, b2, b1, c2, c1, d3, d1]]  # 預期的路徑
    assert paths == expected_path, \
        f"預期找到路徑：{expected_path}，實際找到：{paths}"

def test_demo3() -> None:
    """測試分叉路徑的情況
    路徑結構：
                 E3_
                /
    A1 -> B2 -> C3
                \
                 D2_

    期望找到兩條路徑：
    1. A1 -> B2 -> C3 -> D2_
    2. A1 -> B2 -> C3 -> E3_
    """
    A = TeacherNode('A')
    B = TeacherNode('B')
    C = TeacherNode('C')
    D = TeacherNode('D')
    E = TeacherNode('E')    # A老師的課程
    a1 = CourseNode('1', A)       # 要交換的課程
    a2 = CourseNode('2', A, is_free=True)  # B2 需要 A2 是空的才能交換
    a3 = CourseNode('3', A, is_free=True)
    
    # B老師的課程
    b1 = CourseNode('1', B, is_free=True)  # B1 需要是空的
    b2 = CourseNode('2', B)       # 中間交換點
    b3 = CourseNode('3', B, is_free=True)  # C3 需要 B3 是空的才能交換
    
    # C老師的課程
    c1 = CourseNode('1', C, is_free=True)  # B2 需要 C1 是空的
    c2 = CourseNode('2', C, is_free=True)  # C2 需要是空的
    c3 = CourseNode('3', C)       # 分叉點
    
    # D老師的課程（提供一個空堂）
    d1 = CourseNode('1', D, is_free=True)  # C3 需要 D1 是空的
    d2 = CourseNode('2', D, is_free=True)  # 第一個可能的終點（空堂）
    d3 = CourseNode('3', D, is_free=True)  # 需要空的來讓 C3 移動
    
    # E老師的課程（提供另一個空堂）
    e1 = CourseNode('1', E, is_free=True)  # C3 需要 E1 是空的
    e2 = CourseNode('2', E, is_free=True)  # 需要空的來讓 C3 移動
    e3 = CourseNode('3', E, is_free=True)  # 第二個可能的終點（空堂）

    # 建立課程之間可以交換的關係
    connect_neighbors([a1, b2])  # A1 可以和 B2 交換
    connect_neighbors([b2, c3])  # B2 可以和 C3 交換
    connect_neighbors([c3, d2])  # C3 可以和 D2 交換
    connect_neighbors([c3, e3])  # C3 也可以和 E3 交換
    
    print("\n可行交換路徑 (start = a1):")
    paths = list(merge_paths(a1))
    for idx, cycle in enumerate(paths, 1):
        print(f"{idx:>2}. " + " -> ".join(map(str, cycle)))
      # 檢查是否找到兩條預期的路徑
    expected_paths = [
        [a1, b2, c3, d2],
        [a1, b2, c3, e3]
    ]
    assert len(paths) == 2, f"預期找到2條路徑，實際找到{len(paths)}條"
    assert all(path in paths for path in expected_paths), \
        f"預期找到路徑：{expected_paths}，實際找到：{paths}"

if __name__ == "__main__":
    #test_stop_at_first_free()
    #test_demo1()
    #test_demo2()
    test_demo3()
    #test_long_chain()
