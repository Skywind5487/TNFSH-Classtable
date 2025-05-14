import pytest
from model.swap import TeacherNode, CourseNode, connect_neighbors, merge_paths
from typing import List, Dict, Optional, Generator, Set, Tuple
import string
# -----------------------------------------------------------------------------

def _build_simple_graph():
    """建立一個最簡單的課程交換路徑測試圖
    
    路徑結構：
    (a2_)A1 -> B2(b1_)
    
    回傳值：
        (a1, b1): 其中 a1 是起點，b1 是預期的終點（空堂）
    """
    A = TeacherNode("A")
    B = TeacherNode("B")
    a1 = CourseNode("1", A)              # 起點課程，需要交換
    a2 = CourseNode("2", A, is_free=True)  # A老師的空堂，用於接收 A1
    b1 = CourseNode("1", B, is_free=True)  # B老師的空堂，是終點
    b2 = CourseNode("2", B)              # 中間交換點
    connect_neighbors([a1, b2])
    return a1, b1


def test_basic_path_stops_at_first_free():
    """測試基本路徑尋找功能：路徑應在找到第一個空堂時停止
    
    情境：最簡單的交換情況
    A1 -> B2，其中 B1 是空堂，應立即結束
    
    預期：
    1. 只找到一條路徑
    2. 路徑結尾應該是第一個遇到的空堂(b1_)
    """
    start, expected_last = _build_simple_graph()
    paths = list(merge_paths(start))
    assert len(paths) == 1, "應該只找到一條路徑"
    assert paths[0][-1] == expected_last, "路徑應在第一個空堂結束"


def test_isolated_courses_have_no_path():
    """測試孤立課程節點的情況
    
    情境：兩個課程節點之間沒有任何連接
    
    預期：
    - 不應找到任何路徑，因為課程之間沒有可能的交換方式
    """
    A = TeacherNode("A"); B = TeacherNode("B")
    a1 = CourseNode("1", A)
    b2 = CourseNode("2", B)
    # 不建立任何連接 -> 應該找不到路徑
    paths = list(merge_paths(a1))
    assert paths == [], "孤立的課程節點不應該找到任何路徑"



def test_no_valid_path_in_long_chain(n: int = 15):
    """測試長鏈路超出路徑長度限制的情況
    
    描述：
    建立一個長的課程交換鏈，其中：
    1. 有 n 位老師（預設15位）
    2. 每位老師 i 有 i+2 節課
    3. 課程連接方式：A1 -> B2 -> C3 -> D4 -> ...
    4. 最後一位老師的第一節課和倒數第二位老師最後一節是空堂
    
    結構特點：
    1. 每個老師的課程數量不同
    2. 雖然所有連接都是有效的，但路徑長度超過演算法的限制
    3. 空堂分布在鏈的兩端
    
    預期：
    - 由於路徑長度超過限制，不會找到任何路徑
    - 測試搜索算法的路徑長度限制處理機制
    """
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
    
def test_single_swap_path() -> None:
    """測試簡單的單一交換路徑
    
    路徑結構：
    (a2_)A1 -> B2(b1_)

    情境：
    - A1 課程需要移動
    - A2 是空堂，可以接收 A1
    - B2 可以和 A1 交換
    - B1 是空堂，可以接收 B2

    預期：
    1. 找到一條路徑：A2_ -> A1 -> B2 -> B1_
    2. 路徑應該在遇到第一個空堂時結束
    """
    A = TeacherNode('A'); B = TeacherNode('B'); C = TeacherNode('C'); D = TeacherNode('D')

    # A老師的課程，大部分設為空堂
    a1 = CourseNode('1', A)  # 起點，需要交換
    a2 = CourseNode('2', A, is_free=True)  # 空堂，用於接收 A1
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
    
def test_complex_swap_chain() -> None:
    """測試複雜的交換鏈路徑
    
    路徑結構：
    D2_ -> D5 -> A2 -> A1 -> B2 -> B1 -> C2 -> C1 -> D3 -> D1_
    
    情境：
    - 需要通過多個老師的課程進行連續交換
    - 包含多個空堂和非空堂的交換
    - 測試更長的交換鏈是否能正確建立
    
    預期：
    1. 找到一條完整的交換路徑
    2. 路徑應該包含所有必要的中間交換節點
    3. 最終到達空堂 D1_
    """
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

def test_forked_path_with_two_ends() -> None:
    """測試具有兩個終點的分叉路徑
    
    描述：
    測試一個複雜的分叉路徑情況，其中從同一個起點可以到達兩個不同的終點空堂。
    這個測試情況在真實環境中可能不會發生（因為同一個班級的課程通常是全連接的），
    但這個測試可以幫助我們驗證路徑搜索演算法的正確性。
    路徑結構：
                            E3(E1_)
                             /
    (a2_)A1 -> B2(b1) -> C3(c1)
                             \
                            D2(D1_)

    路徑檢查機制：
    1. 後向檢查(bwd)：確保目標老師在當前時段有空堂可接收課程
       - 例如：A1 -> B2 移動時，檢查 A2 是否為空堂以接收 A1
       - 後向檢查失敗時程式會嘗試下一個可能的路徑
       
    2. 前向檢查(fwd)：確保當前課程在目標時段有空堂可移動
       - 例如：A1 -> B2 移動時，檢查 B1 是否為空堂以讓 B2 移動
       - 前向檢查失敗時會以目標課程為新起點繼續搜尋
       
    移動分析：
    1. A1 -> B2 移動：
       * 後向：A2_ 為空堂，可接收 A1
       * 前向：B1 需為空堂，讓 B2 移動
    
    2. B2 -> C3 移動：
       * 後向：B1_ 為空堂，可接收 B2
       * 前向：C1 需為空堂，使 C3 可移動
    
    3. C3 分叉處理：
       路徑一：C3 -> D2
       * 後向：C1_ 為空堂，可接收 C3
       * 前向：D1_ 為空堂，D2 可移動
       
       路徑二：C3 -> E3
       * 後向：C1_ 為空堂，可接收 C3
       * 前向：E1_ 為空堂，E3 可移動
    
    預期路徑：
    1. A2_ -> A1 -> B2 -> B1 -> C3 -> C1 -> D2 -> D1_  # 透過 D2 到達空堂
    2. A2_ -> A1 -> B2 -> B1 -> C3 -> C1 -> E3 -> E1_  # 透過 E3 到達空堂
    """
    # 建立所有老師節點
    A = TeacherNode('A')
    B = TeacherNode('B')
    C = TeacherNode('C')
    D = TeacherNode('D')
    E = TeacherNode('E')

    # A老師的課程
    a1 = CourseNode('1', A)              # 起點，需要移動
    a2 = CourseNode('2', A, is_free=True)  # 空堂，用於接收 A1

    # B老師的課程
    b1 = CourseNode('1', B)              # B2 移動時的目標位置
    b2 = CourseNode('2', B)              # 中間交換點

    # C老師的課程
    c1 = CourseNode('1', C)              # C3 移動時的目標位置
    c2 = CourseNode('2', C, is_free=True) # 空堂，用於接收 D2
    c3 = CourseNode('3', C)              # 分叉點

    # D老師的課程
    d1 = CourseNode('1', D, is_free=True)  # 空堂，用於結束路徑
    d2 = CourseNode('2', D)              # 分叉路徑之一

    # E老師的課程
    e1 = CourseNode('1', E, is_free=True)  # 空堂，用於結束路徑
    e3 = CourseNode('3', E)              # 分叉路徑之二

    # 建立交換關係
    connect_neighbors([a1, b2])          # A1 可以和 B2 交換
    connect_neighbors([b1, c3])          # B1 可以和 C3 交換
    connect_neighbors([c1, d2])          # C1 可以和 D2 交換
    connect_neighbors([c1, e3])          # C1 也可以和 E3 交換

    print("\n可行交換路徑 (start = a1):")
    paths = list(merge_paths(a1))
    for idx, cycle in enumerate(paths, 1):
        print(f"{idx:>2}. " + " -> ".join(map(str, cycle)))    # 檢查是否找到兩條預期的路徑
    expected_paths = [
        [a2, a1, b2, b1, c3, c1, d2, d1],
        [a2, a1, b2, b1, c3, c1, e3, e1]
    ]
    assert len(paths) == 2, f"預期找到2條路徑，實際找到{len(paths)}條"
    
    # 檢查每條路徑都存在，但不依賴順序
    for expected_path in expected_paths:
        assert any(all(a == b for a, b in zip(path, expected_path)) for path in paths), \
            f"找不到預期路徑：{expected_path}，實際找到的路徑：{paths}"

def test_interconnected_path_with_cycle() -> None:
    """測試具有循環與互相連接的分叉路徑
    
    描述：
    這個測試代表了更真實的課程交換情境，其中：
    1. 同一個班級的課程之間都是互相連接的
    2. 存在循環路徑（比如 C1 -> D2 -> E3 -> C1）
    3. 有多個可能的終點和路徑選擇
    
    路徑結構：
                            E3 --- E1
                             |      |
    (a2_)A1 -> B2(b1) -> C3(c1) -> D2 -> D1_
                             |      |
                             +------+

    路徑說明：
    1. 基本路徑和 test_demo3 類似，但現在所有相關課程都互相連接
    2. 新增了 E1 -> D2 的連接，創造了一個新的可能路徑

    路徑檢查機制：
    1. 後向檢查(bwd)：確保目標老師在當前時段有空堂可接收課程
       - 例如：A1 -> B2 移動時，檢查 A2 是否為空堂以接收 A1
       
    2. 前向檢查(fwd)：確保當前課程在目標時段有空堂可移動
       - 例如：A1 -> B2 移動時，檢查 B1 是否為空堂以讓 B2 移動

    預期找到兩條路徑：
    1. A2_ -> A1 -> B2 -> B1 -> C3 -> C1 -> D2 -> D1_  # 直接到 D1_
    2. A2_ -> A1 -> B2 -> B1 -> C3 -> C1 -> E3 -> E1 -> D2 -> D1_  # 經過 E1 到 D1_
    """
    # 建立所有老師節點
    A = TeacherNode('A')
    B = TeacherNode('B')
    C = TeacherNode('C')
    D = TeacherNode('D')
    E = TeacherNode('E')

    # A老師的課程
    a1 = CourseNode('1', A)              # 起點，需要移動
    a2 = CourseNode('2', A, is_free=True)  # 空堂，用於接收 A1

    # B老師的課程
    b1 = CourseNode('1', B)              # B2 移動時的目標位置
    b2 = CourseNode('2', B)              # 中間交換點

    # C老師的課程
    c1 = CourseNode('1', C)              # C3 移動時的目標位置
    c2 = CourseNode('2', C, is_free=True) # 空堂，用於接收其他課程
    c3 = CourseNode('3', C)              # 分叉點

    # D老師的課程
    d1 = CourseNode('1', D, is_free=True)  # 空堂，最終目標
    d2 = CourseNode('2', D)              # 分叉路徑之一

    # E老師的課程
    e1 = CourseNode('1', E)              # E1 不是空堂
    e3 = CourseNode('3', E)              # 分叉路徑之二

    # 建立交換關係 - 注意：現在所有相關課程都互相連接
    connect_neighbors([a1, b2])          # A1 可以和 B2 交換
    connect_neighbors([b1, c3])          # B1 可以和 C3 交換
    connect_neighbors([c1, d2, e3])      # C1、D2、E3 互相都可以交換
    connect_neighbors([e1, d2])          # E1 可以和 D2 交換

    print("\n可行交換路徑 (start = a1):")
    paths = list(merge_paths(a1))
    for idx, cycle in enumerate(paths, 1):
        print(f"{idx:>2}. " + " -> ".join(map(str, cycle)))    # 檢查是否找到兩條預期的路徑
    expected_paths = [
        [a2, a1, b2, b1, c3, c1, d2, d1],
        [a2, a1, b2, b1, c3, c1, e3, e1, d2, d1]
    ]
    assert len(paths) == 2, f"預期找到2條路徑，實際找到{len(paths)}條"
    
    # 將路徑轉換為字串進行完整比較
    found_paths = [" -> ".join(str(node) for node in path) for path in paths]
    expected_path_strs = [" -> ".join(str(node) for node in path) for path in expected_paths]
    
    # 檢查每條預期路徑是否都能在實際路徑中找到（不考慮順序）
    for expected_str in expected_path_strs:
        assert expected_str in found_paths, \
            f"找不到預期路徑：{expected_str}\n實際找到的路徑：\n" + "\n".join(found_paths)

if __name__ == "__main__":
    #test_basic_path_stops_at_first_free()
    #test_isolated_courses_have_no_path()
    #test_single_swap_path()
    #test_complex_swap_chain()
    #test_forked_path_with_two_ends()
    #test_interconnected_path_with_cycle()
    test_no_valid_path_in_long_chain()
