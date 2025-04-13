from tnfsh_class_table.backend import TNFSHClassTable
from typing import Tuple, List, Dict, Union
def get_status_class_table(class_:TNFSHClassTable):
    """
    獲取班級課表狀態(transposed_table)
    Args:
        class_: 班級節點
    Returns:
        課程節點
    """
    table = class_.transposed_table
    status_table = []
    i , j = 0, 0
    for i in range(len(table)):
        for j in range(len(table[i])):
            streak, start_time = get_streak(class_, (i, j))
def get_class_code(teacher:TNFSHClassTable, time: tuple[int, int]):
    """
    獲取某課程的班級
    Args:
        teacher: 老師節點
        time: 課程時間 (day, period)
    Returns:
        課程節點
    """
    table = teacher.transposed_table 
    course = table[time[0]][time[1]]
    class_code = list(list(course.values())[0].keys())
    print(class_code)
    #class_code = [code for code in class_code.keys() if code != ""]
    if class_code == ['']:
        return -1 # 無班級不能調課
    if len(class_code) > 1:
        return -2 # 多班級不能調課
    return class_code[0] # 返回班級代碼
def is_course_free(teacher:TNFSHClassTable, time: tuple[int, int]) -> bool:
    """
    判斷老師的課程是否為空
    Args:
        teacher: 老師節點
        time: 課程時間 (day, period)
    Returns:
        bool: 是否為空課程
    """
    table = teacher.transposed_table 
    course = table[time[0]][time[1]]
    if course == {"":{"":""}}:
        return True
    return False
def get_streak(teacher:TNFSHClassTable, time: tuple[int, int])-> Union[int, Tuple[int, Tuple[int, int]]]: 
    """
    獲取老師的連續課程節點
    Args:
        teacher: 老師節點
        time: 課程時間 (day, period)
    Returns:
        連續課程節點列表
    """
    streak = 0
    table = teacher.transposed_table 
    course = table[time[0]][time[1]]
    day = table[time[0]]
    i = time[1]  # 從當前時間開始向前遍歷
    while i >= 0:
        if day[i] == course:
            first_course_time = i
            streak += 1
        i -= 1
    i = time[1]  # 從當前時間開始向後遍歷
    while i < len(day):
        if day[i] == course:
            streak += 1
        i += 1
    streak -= 1 # 減去多算的當前時間的課程
    return streak, (time[0], first_course_time)  # 返回連續課程的長度與第一節
    
def change_course(teacher_name:str, time: tuple[int, int]):
    """
    將老師的課程代碼轉換為對應的課程節點
    Args:
        teacher_name: 老師名稱
        time: 課程時間 (day, period)
    """
    time = (time[0]-1, time[1]-1)
    print(teacher_name, time)
    teacher = TNFSHClassTable(teacher_name)
    
    is_free = is_course_free(teacher, time)
    if is_free:
        raise ValueError("課程時間為空，無法調課")
    streak, strar_time = get_streak(teacher, time)
    class_code = get_class_code(teacher, strar_time) # 獲取班級代碼
    if class_code == -1:
        raise ValueError("無班級，無法調課")
    if class_code == -2:
        raise ValueError("多班級，無法調課")

    class_ = TNFSHClassTable(class_code) # 獲取班級課表



    return streak, strar_time  # 返回連續課程的長度與第一節



def test():
    streak = get_class_code(TNFSHClassTable("顏永進"), (3, 3))
    print(streak)  # 測試場景1: 老師在某天有連續課程
    #print(TNFSHClassTable("顏永進").transposed_table[3][7])
if __name__ == "__main__":
    test()