from tnfsh_class_table.backend import TNFSHClassTable, TNFSHClassTableIndex
from typing import Tuple, List, Dict, Union

def is_course_free(teacher:TNFSHClassTable, time: tuple[int, int]) -> bool:
    """
    檢查指定時間是否為空堂
    空堂的定義為課表中該時段的值為 {"":{"":""}}
    
    Args:
        teacher: TNFSHClassTable物件，代表教師的課表
        time: (星期, 節次) 的元組
    Returns:
        bool: True 表示是空堂，False 表示有課
    """
    table = teacher.transposed_table 
    course = table[time[0]][time[1]]
    if course == {"":{"":""}}:
        return True
    return False

def get_streak(teacher:TNFSHClassTable, time: tuple[int, int])-> Union[int, Tuple[int, Tuple[int, int]]]: 
    """
    分析指定時間點的連續課程情況
    
    此函數會：
    1. 向前搜尋相同課程
    2. 向後搜尋相同課程
    3. 計算連續課程總長度
    
    Args:
        teacher: TNFSHClassTable物件，代表教師的課表
        time: (星期, 節次) 的元組
    Returns:
        Tuple[int, Tuple[int, int]]: (連續課程長度, (星期, 起始節次))
    """
    streak = 0  # 連續課程計數器
    table = teacher.transposed_table 
    course = table[time[0]][time[1]]  # 獲取指定時間的課程
    day = table[time[0]]  # 獲取該天的所有課程
    
    # 向前搜尋相同課程
    i = time[1]
    while i >= 0:
        if day[i] == course:
            first_course_time = i
            streak += 1
            i -= 1
        else:
            break 
            
    # 向後搜尋相同課程
    i = time[1]
    while i < len(day):
        if day[i] == course:
            streak += 1
            i += 1
        else:
            break
        
    streak -= 1  # 減去重複計算的當前課程
    return streak, (time[0], first_course_time)

def get_class_code(teacher:TNFSHClassTable, time: tuple[int, int]):
    """
    獲取特定時間點的課程對應的班級代碼
    例如：若老師在星期一第一節教 111 班，則返回 '111'
    
    Args:
        teacher: TNFSHClassTable物件，代表教師的課表
        time: (星期, 節次) 的元組，例如 (0,0) 代表星期一第一節
    Returns:
        List[str]: 班級代碼列表
    """
    table = teacher.transposed_table 
    course = table[time[0]][time[1]]
    class_code = list(list(course.values())[0].keys())
    return class_code 

def get_status_class_table(class_:TNFSHClassTable):
    """
    獲取班級課表狀態(transposed_table)，用於分析連續課程
    此函數將課表轉換為狀態表，其中：
    - 正數表示連續課程的長度
    - 負數表示連續空堂的長度
    - 0 表示這是連續課程的一部分（非起始位置）
    
    Args:
        class_: TNFSHClassTable物件，代表某個班級或教師的課表
    Returns:
        List[List[int]]: 二維陣列，表示每個時段的課程狀態
    """
    table = class_.transposed_table
    status_table = []  # 初始化狀態表
    i , j = 0, 0
    streak = 0  # 連續課程計數器
    
    # 遍歷每一天的課表
    for i in range(len(table)):
        day_status = []  # 儲存當天的課程狀態
        # 遍歷當天的每節課
        for j in range(len(table[i])):
            # 如果是連續課程的一部分，標記為0並繼續
            if streak > 0:
                streak -= 1
                day_status.append(0)
                continue
            
            # 獲取當前位置的連續課程資訊
            streak, start_time = get_streak(class_, (i, j))
            
            # 判斷是空堂還是實際課程
            if table[start_time[0]][start_time[1]] == {"":{"":""}}:
                day_status.append(-streak)  # 空堂用負數表示
            else:
                day_status.append(streak)   # 實際課程用正數表示
            streak -= 1
        status_table.append(day_status)
    return status_table

def get_swap_courses(status_table: List[List[int]], streak: int) -> List[Tuple[Tuple[int, int]]]:
    """
    尋找可以調動的課程時段
    
    Args:
        status_table: 課程狀態表，由 get_status_class_table 生成
        streak: 需要調動的連續課程長度
    Returns:
        List[Tuple[Tuple[int, int], int]]: 可調動時段列表，每項為 ((星期,節次), 類型)
        類型：0 表示空堂，1 表示有課
    """
    can_swap_course = []
    # 遍歷整個狀態表
    for i in range(len(status_table)):
        for j in range(len(status_table[i])):
            # 檢查是否有相同長度的課程
            if status_table[i][j] == streak:
                can_swap_course.append(((i, j), 1))
                print(f"可以調課的時間: {i, j}")
            # 檢查是否有足夠長度的空堂
            if -status_table[i][j] >= streak: # 遍歷可能的空堂組合
                for k in range(-status_table[i][j] - streak + 1):
                    can_swap_course.append(((i, j+k), 0))
    return can_swap_course

def get_teacher_name(class_table:TNFSHClassTable, time: tuple[int, int]) -> TNFSHClassTable:
    """
    獲取特定時段的授課教師
    
    Args:
        class_table: TNFSHClassTable物件，代表班級的課表
        time: (星期, 節次) 的元組
    Returns:
        TNFSHClassTable: 教師的課表物件
    """
    table = class_table.transposed_table 
    course = table[time[0]][time[1]]
    teacher_name = list(list(course.values())[0].keys())
    return teacher_name

def check_free(teacher:TNFSHClassTable, time: tuple[int, int], streak) -> bool:
    """
    檢查教師在指定時段是否有足夠長度的空堂
    
    Args:
        teacher: TNFSHClassTable物件，代表教師的課表
        time: (星期, 節次) 的元組
        streak: 需要的連續空堂長度
    Returns:
        bool: True 表示有足夠的空堂，False 表示沒有
    """
    status_table = get_status_class_table(teacher)
    # 檢查是否為連續課程的一部分
    if status_table[time[0]][time[1]] == 0:
        i = time[1]
        # 向前搜尋空堂起始位置
        while i >= 0:
            if status_table[time[0]][i] == 0:
                i -= 1
            else:
                # 檢查空堂長度是否足夠
                if -status_table[time[0]][i] >= streak:
                    return True
                return False
        return False
    else:
        # 直接檢查當前位置的空堂長度
        if -status_table[time[0]][time[1]] >= streak:
            return True
    return False

def change_course(teacher_name:str, time: tuple[int, int]) -> dict[str, Union[str, int, tuple[int, int], dict[str, Union[str, int]]]]:
    """
    處理課程調動的主要函數
    
    執行流程：
    1. 檢查目標課程是否存在
    2. 獲取連續課程資訊
    3. 獲取可調動時段
    4. 檢查教師衝堂
    5. 產生可行的調課方案
    
    Args:
        teacher_name: 教師姓名
        time: (星期, 節次) 的元組，注意：使用者輸入的是從1開始的值

    Returns:
        dict[str, Union[str, int, tuple[int, int], dict[str, Union[str, int]]]]: 調課結果
        包含以下鍵值：
        - source_teacher: 來源教師姓名
        - streak_start_time: 連續課程的起始時間 (星期, 節次)
        - streak: 連續課程的長度
        - source_course: 來源課程名稱
        - can_swap_courses: 可調動的課程列表，每個元素包含目標教師、目標課程、目標時間等資訊        
    Example:
    {
        "source_teacher": "顏永進",
        "streak_start_time": (3, 2),
        "streak": 2,
        "source_course": "數學",
        "can_swap_courses": [
            {
                "target_teacher": "空堂，無老師",
                "target_course": "空堂，無課程",
                "target_day": 3,
                "target_period": 2
            },
            {
                "target_teacher": "王小明",
                "target_course": "物理",
                "target_day": 3,
                "target_period": 3
            }, ...
        ]
    }
    """
    # 轉換時間格式（使用者輸入從1開始，程式內部從0開始）
    time = (time[0]-1, time[1]-1)

    # 獲取教師課表
    teacher = TNFSHClassTable(teacher_name)
    
    # 檢查是否為空堂
    is_free = is_course_free(teacher, time)
    if is_free:
        raise ValueError("課程時間為空，無法調課")

    # 獲取連續課程資訊
    streak, start_time = get_streak(teacher, time)
    
    # 獲取並檢查班級代碼
    class_code = get_class_code(teacher, start_time)
    if class_code == ['']:
        raise ValueError("無班級，無法調課")
    if len(class_code) > 1:
        raise ValueError("多班級，無法調課")
    class_code = class_code[0]

    # 獲取班級課表和可調動時段
    class_ = TNFSHClassTable(class_code)
    class_status = get_status_class_table(class_)
    can_swap_course = get_swap_courses(class_status, streak)

    # 尋找可行的調課方案
    courses = []
    for can_swap in can_swap_course:
        # 檢查目標教師是否有空
        if check_free(teacher, can_swap[0], streak):
            print(f"來源教師 {teacher.target} 在 {can_swap[0]} 時間不衝堂，可以嘗試調課")
            if can_swap[1] == 0: # 將換到空堂
                course = {}
                course["target_teacher"] = "空堂，無老師"
                course["target_course"] = "空堂，無課程"
                course["target_day"] = can_swap[0][0] + 1
                course["target_period"] = can_swap[0][1] + 1
                courses.append(course)
                print(f"空堂，可以調課的時間: {can_swap[0]}")
                continue
            # 獲取並檢查對方教師是否有空
            opposite_teacher_name = get_teacher_name(class_, can_swap[0])
            if opposite_teacher_name == ['']:
                continue
            if len(opposite_teacher_name) > 1:
                continue
            opposite_teacher = TNFSHClassTable(opposite_teacher_name[0])
            if check_free(opposite_teacher, start_time, streak):
                course = {}
                course["target_teacher"] = opposite_teacher.target
                course["target_course"] = list(class_.transposed_table[can_swap[0][0]][can_swap[0][1]].keys())[0]
                course["target_day"] = can_swap[0][0] + 1
                course["target_period"] = can_swap[0][1] + 1
                courses.append(course)
                print(f"對方教師 {opposite_teacher.target} 在 {start_time} 時間不衝堂，可以完成調課")
        else:
            print(f"教師 {teacher.target} 在 {can_swap[0]} 時間衝堂，無法調課")
    result = {}
    result["source_teacher"] = teacher.target
    result["streak_start_time"] = start_time
    result["streak"] = streak
    result["source_course"] = list(teacher.transposed_table[start_time[0]][start_time[1]].keys())[0]
    result["can_swap_courses"] = courses
    return result

def test():
    """
    測試函數
    用於測試各種課表調動的場景
    """
    # 測試場景1: 檢查連續課程的識別
    streak = change_course("顏永進", (3, 2))
    # 以json輸出
    import json
    print(json.dumps(streak, indent=4, ensure_ascii=False))
    #print(streak)

if __name__ == "__main__":
    test()