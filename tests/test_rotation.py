import pytest
from model.rotation import TeacherNode, CourseNode, connect_neighbors, bwd_check, rotation
from typing import List, Dict, Optional, Generator, Set


"""
輪換算法只有後向檢查，沒有後向檢查
"""

def _build_simple_graph():
    """建立一個最簡單的課程輪調測試圖
    
    路徑結構：
    A1 -> B2 -> C3 -> D4 -> A1
    
    每位老師都有 4 節課，其中除了需要輪調的課程外，其他都是空堂。
    例如：A老師的 A2、A3、A4 都是空堂。
    這樣可以確保找到輪調路徑時，每位老師都有空堂可以接收調動的課程。
    
    回傳值：
        a1: 圖的起點節點（A1課程）
    """
    # 建立教師節點
    A = TeacherNode("A")
    B = TeacherNode("B")
    C = TeacherNode("C")
    D = TeacherNode("D")

    # 建立每位老師的課程節點
    # A 老師的課程
    a1 = CourseNode("1", A)              # 這節要交換，所以不是空堂
    a2 = CourseNode("2", A, is_free=True)
    a3 = CourseNode("3", A, is_free=True)
    a4 = CourseNode("4", A, is_free=True)
    A.courses = {"1": a1, "2": a2, "3": a3, "4": a4}

    # B 老師的課程
    b1 = CourseNode("1", B, is_free=True)
    b2 = CourseNode("2", B)              # 這節要交換，所以不是空堂
    b3 = CourseNode("3", B, is_free=True)
    b4 = CourseNode("4", B, is_free=True)
    B.courses = {"1": b1, "2": b2, "3": b3, "4": b4}

    # C 老師的課程
    c1 = CourseNode("1", C, is_free=True)
    c2 = CourseNode("2", C, is_free=True)
    c3 = CourseNode("3", C)              # 這節要交換，所以不是空堂
    c4 = CourseNode("4", C, is_free=True)
    C.courses = {"1": c1, "2": c2, "3": c3, "4": c4}

    # D 老師的課程
    d1 = CourseNode("1", D, is_free=True)
    d2 = CourseNode("2", D, is_free=True)
    d3 = CourseNode("3", D, is_free=True)
    d4 = CourseNode("4", D)              # 這節要交換，所以不是空堂
    D.courses = {"1": d1, "2": d2, "3": d3, "4": d4}

    # 建立換課環路
    connect_neighbors([a1, b2, c3, d4])

    return a1


def test_basic_cycle():
    """測試最基本的課程輪調環路
    
    情境：
    建立一個簡單的四節課輪調環路 A1 -> B2 -> C3 -> D4 -> A1
    每位老師除了需要輪調的課程外都是空堂，確保輪調可以進行。

    檢查項目：
    1. 確認可以找到所有可能的輪調環路
    2. 驗證每條路徑都是合法的
    3. 確認所有的前向檢查都通過
    """
    start = _build_simple_graph()
    cycles = list(rotation(start))

    # 找到所有可能的環路組合
    sorted_cycles = sorted(cycles, key=len)
    
    print(f"\n找到 {len(cycles)} 條環路：")
    print("\n=== 依照長度排序 ===")
    current_len = 0
    for i, cycle in enumerate(sorted_cycles, 1):
        if len(cycle) != current_len:
            current_len = len(cycle)
            print(f"\n長度 {current_len}:")
        print(f"{i:2d}. " + " -> ".join(str(node) for node in cycle))

    # 將所有路徑轉換成字串形式以便比對
    cycle_strs = set(" -> ".join(str(node) for node in cycle) for cycle in cycles)

    # 驗證基本路徑都存在
    basic_paths = {
        "a1 -> b2 -> a1",
        "a1 -> b2 -> c3 -> a1",
        "a1 -> b2 -> c3 -> d4 -> a1",
        "a1 -> b2 -> d4 -> a1",
        "a1 -> b2 -> d4 -> c3 -> a1",
        "a1 -> c3 -> a1",
        "a1 -> c3 -> b2 -> a1",
        "a1 -> c3 -> b2 -> d4 -> a1",
        "a1 -> c3 -> d4 -> a1",
        "a1 -> c3 -> d4 -> b2 -> a1",
        "a1 -> d4 -> a1",
        "a1 -> d4 -> b2 -> a1",
        "a1 -> d4 -> b2 -> c3 -> a1",
        "a1 -> d4 -> c3 -> a1",
        "a1 -> d4 -> c3 -> b2 -> a1"
    }
    
    # 驗證找到的環路數量正確
    assert len(cycles) == len(basic_paths), f"預期找到 {len(basic_paths)} 條環路，但找到 {len(cycles)} 條"
    
    # 驗證每條基本路徑都有被找到
    for path in basic_paths:
        assert path in cycle_strs, f"基本路徑 {path} 未在找到的路徑中"
    
    # 驗證沒有多餘的路徑
    assert cycle_strs == basic_paths, "找到了預期之外的環路"


def test_no_cycle_when_teacher_busy():
    """
    測試當教師不可用（is_free=False）時，不應形成包含該教師的環路

    圖示：
    a1 ---> b2 (is_free=False) ---> c3 ---> a1
                ↑__________________________|
    
    預期結果：
    1. 不應存在包含教師b2的環路
    2. 仍可能存在不經過b2的其他環路
    """
    A = TeacherNode("A")
    B = TeacherNode("B")
    C = TeacherNode("C")
    D = TeacherNode("D")

    # A 老師除了 A1 和 A2 外都是空堂
    a1 = CourseNode("1", A)                  # A1 是需要輪調的課程
    a2 = CourseNode("2", A, is_free=False)   # A2 已經有課，不是空堂
    a3 = CourseNode("3", A, is_free=True)
    a4 = CourseNode("4", A, is_free=True)
    A.courses = {"1": a1, "2": a2, "3": a3, "4": a4}

    # 其他老師的設置和基本測試相同
    b1 = CourseNode("1", B, is_free=True)
    b2 = CourseNode("2", B)
    b3 = CourseNode("3", B, is_free=True)
    b4 = CourseNode("4", B, is_free=True)
    B.courses = {"1": b1, "2": b2, "3": b3, "4": b4}

    c1 = CourseNode("1", C, is_free=True)
    c2 = CourseNode("2", C, is_free=True)
    c3 = CourseNode("3", C)
    c4 = CourseNode("4", C, is_free=True)
    C.courses = {"1": c1, "2": c2, "3": c3, "4": c4}

    d1 = CourseNode("1", D, is_free=True)
    d2 = CourseNode("2", D, is_free=True)
    d3 = CourseNode("3", D, is_free=True)
    d4 = CourseNode("4", D)
    D.courses = {"1": d1, "2": d2, "3": d3, "4": d4}

    # 建立相同的換課環路
    connect_neighbors([a1, b2, c3, d4])

    # 檢查 A1 -> B2 的移動是否被阻止（因為 A2 非空堂）
    assert not bwd_check(a1, b2), "當目標時段有課時，bwd_check 應該返回 False"

    # 找出所有輪調環路
    cycles = list(rotation(a1))
    cycle_strs = set(" -> ".join(str(node) for node in cycle) for cycle in cycles)

    # 確認不存在經過 b2 開頭的路徑
    blocked_paths = {
        "a1 -> b2 -> a1",
        "a1 -> b2 -> c3 -> a1",
        "a1 -> b2 -> c3 -> d4 -> a1",
        "a1 -> b2 -> d4 -> a1",
        "a1 -> b2 -> d4 -> c3 -> a1"
    }
    
    # 驗證所有被阻擋的路徑都不存在
    for path in blocked_paths:
        assert path not in cycle_strs, f"不應該找到被阻擋的路徑：{path}"


def test_long_cycle_max_depth():
    """
    測試最大深度限制下的輪調環路
    圖與basic_cycle相同，但最大深度設為3，所以：
    1. 實際長度 = 深度 + 1（因為起點節點會重複計算在結尾）
    2. 所以深度3最多形成長度4的路徑，例如：a1 -> b2 -> c3 -> a1

    可能的路徑：
    深度2路徑: a1 -> b2 -> a1 (實際長度3)
    深度2路徑: a1 -> c3 -> a1 (實際長度3)
    深度2路徑: a1 -> d4 -> a1 (實際長度3)
    """
    start = _build_simple_graph()
    cycles = list(rotation(start, max_depth=3))

    # 找到所有可能的環路組合
    sorted_cycles = sorted(cycles, key=lambda cycle: len(cycle)-1)  # -1 是因為最後一個節點重複了起點
    
    print(f"\n找到 {len(cycles)} 條環路：")
    print("\n=== 依照實際節點數排序 ===")
    current_nodes = 0
    for i, cycle in enumerate(sorted_cycles, 1):
        actual_nodes = len(cycle)-1  # 實際節點數 = 路徑長度-1
        if actual_nodes != current_nodes:
            current_nodes = actual_nodes
            print(f"\n包含 {current_nodes} 個不重複節點:")
        print(f"{i:2d}. " + " -> ".join(str(node) for node in cycle))

    # 將所有路徑轉換成字串形式以便比對
    cycle_strs = set(" -> ".join(str(node) for node in cycle) for cycle in cycles)

    # 根據深度限制，應該存在的基本路徑
    basic_paths = {
        # 深度2（實際長度3）的路徑
        "a1 -> b2 -> a1",
        "a1 -> c3 -> a1",
        "a1 -> d4 -> a1",
        # 深度3（實際長度4）的路徑
        "a1 -> b2 -> c3 -> a1",
        "a1 -> b2 -> d4 -> a1",
        "a1 -> c3 -> b2 -> a1",
        "a1 -> c3 -> d4 -> a1",
        "a1 -> d4 -> b2 -> a1",
        "a1 -> d4 -> c3 -> a1"
    }
    
    # 驗證找到的環路數量正確
    assert len(cycles) == len(basic_paths), f"預期找到 {len(basic_paths)} 條環路，但找到 {len(cycles)} 條"
    
    # 驗證每條基本路徑都有被找到
    for path in basic_paths:
        assert path in cycle_strs, f"基本路徑 {path} 未在找到的路徑中"
    
    # 驗證沒有多餘的路徑
    assert cycle_strs == basic_paths, "找到了預期之外的環路"


def test_no_valid_path_in_long_cycle():
    """
    測試長輪調環路中的路徑長度
    
    情境：
    建立一個簡單的環路，檢查每個環路的實際長度是否正確
    (注意：路徑回到原點時需要多算一步)

    正確的路徑長度：
    1. a1 -> b2 -> a1 = 2 + 1 = 3 (兩個節點加上回到原點)
    2. a1 -> b2 -> c3 -> a1 = 3 + 1 = 4 (三個節點加上回到原點)
    3. a1 -> b2 -> c3 -> d4 -> a1 = 4 + 1 = 5 (四個節點加上回到原點)
    """
    start = _build_simple_graph()
    cycles = list(rotation(start, max_depth=3))

    # 按照路徑節點數量排序
    sorted_cycles = sorted(cycles, key=lambda cycle: len(cycle)-1)  # -1 是因為最後一個節點重複了起點
    
    print(f"\n找到 {len(cycles)} 條環路：")
    print("\n=== 依照實際節點數排序 ===")
    current_nodes = 0
    for i, cycle in enumerate(sorted_cycles, 1):
        actual_nodes = len(cycle)-1  # 實際節點數 = 路徑長度-1
        if actual_nodes != current_nodes:
            current_nodes = actual_nodes
            print(f"\n包含 {current_nodes} 個不重複節點:")
        print(f"{i:2d}. " + " -> ".join(str(node) for node in cycle))

    # 驗證每種長度的環路數量
    length_2_cycles = [c for c in cycles if len(c)-1 == 2]  # 2節點環路
    length_3_cycles = [c for c in cycles if len(c)-1 == 3]  # 3節點環路

    # 2節點環路的路徑
    basic_2_node_paths = {
        "a1 -> b2 -> a1",
        "a1 -> c3 -> a1",
        "a1 -> d4 -> a1"
    }
    
    # 3節點環路的路徑
    basic_3_node_paths = {
        "a1 -> b2 -> c3 -> a1",
        "a1 -> b2 -> d4 -> a1",
        "a1 -> c3 -> b2 -> a1",
        "a1 -> c3 -> d4 -> a1",
        "a1 -> d4 -> b2 -> a1",
        "a1 -> d4 -> c3 -> a1"
    }



    # 驗證每種長度的環路數量
    assert len(length_2_cycles) == len(basic_2_node_paths), f"預期找到 {len(basic_2_node_paths)} 條 2節點環路，但找到 {len(length_2_cycles)} 條"
    assert len(length_3_cycles) == len(basic_3_node_paths), f"預期找到 {len(basic_3_node_paths)} 條 3節點環路，但找到 {len(length_3_cycles)} 條"

    # 將路徑轉換為字串以方便比對
    path_strs = set(" -> ".join(str(node) for node in cycle) for cycle in cycles)
    
    # 驗證所有基本路徑都存在
    for path in basic_2_node_paths | basic_3_node_paths :
        assert path in path_strs, f"基本路徑 {path} 未在找到的路徑中"

    # 驗證沒有多餘的路徑
    assert path_strs == basic_2_node_paths | basic_3_node_paths , "找到了預期之外的環路"


def test_isolated_course():
    """測試孤立課程的情況
    
    情境：
    建立一個沒有任何連接的課程節點，確認無法形成輪調環路
    
    檢查項目：
    1. 確認孤立的課程節點無法形成環路
    2. 驗證 rotation 返回空列表
    """
    # 建立一位老師和一節課
    A = TeacherNode("A")
    a1 = CourseNode("1", A)
    A.courses = {"1": a1}

    # 不建立任何連接

    # 尋找輪調環路
    cycles = list(rotation(a1))
    
    # 應該找不到任何環路
    assert len(cycles) == 0, "孤立的課程節點不應該能找到任何輪調環路"


if __name__ == "__main__":
    #test_basic_cycle()
    #test_no_cycle_when_teacher_busy()
    #test_multiple_cycles()
    test_long_cycle_max_depth()
    test_no_valid_path_in_long_cycle()
    #test_isolated_course()
    
    print("所有測試完成")
