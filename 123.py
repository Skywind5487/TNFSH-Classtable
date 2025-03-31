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

class CourseNode:
    def __init__(self, course:tuple[int,int], parent=None):
        self.neighbours = []
        self.parent = parent
        self.time: tuple[int,int] = course

class TeacherNode:
    def __init__(self, name:str, course:tuple[int,int], parent=None):
        self
        self.children = []
    

def search(src_course, src_teacher: , max_depth:int):
