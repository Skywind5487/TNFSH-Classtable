def _swap_period_day(course: tuple[int, int]):
        return (course[1] - 1, course[0] - 1)
def _get_table(target:str):
    pass
def _is_streak(table, course):
    pass
def _is_empty(table, course):
    pass

def _get_target(table, course) -> list[str]:
    pass

def _find_all_streak_and_empty(table, streak):
    pass

def _src_check(src_teacher_table, src_course):
    if _is_streak(src_teacher_table, src_course):
        pass
    else:
        return False

    if _is_empty(src_teacher_table, src_course):
        pass
    else:
        return False

def search(src_teacher: str, src_course: tuple[int, int], src_course_streak: int, path: list[tuple[str, tuple[int, int]]], tables: dict[str, list[list[bool]]], depth:int, max_depth: int):
    if _is_empty(src_teacher, src_course):
        return path
    if depth >= max_depth:
        return []
           

def bi_side_search(src_teacher: str, src_course: tuple[int, int], src_course_streak: int):
    
    src_course = _swap_period_day(src_course)
    src_teacher_table = _get_table(src_teacher)
    
    if not _src_check(src_teacher_table, src_course):
        return

    target_class = _get_target(src_teacher_table, src_course)
    if len(target_class) != 1:
        return "不支援多班級調課"
    
    target_class_streak_and_empty = _find_all_streak_and_empty(_get_table(target_class[0]), src_course_streak)
    
    for target_course in target_class_streak_and_empty:
        target_teacher = _get_target(_get_table(target_class[0]), target_course)
        target_teacher_table = _get_table(target_teacher[0])
        if _is_empty(target_teacher_table, src_course):
            pass
        elif _is_streak(src_teacher_table, target_course):
            seacrch()
