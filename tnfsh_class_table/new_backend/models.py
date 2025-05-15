from typing import List, Dict, TypeAlias, Optional, Any, Literal
from pydantic import BaseModel
from datetime import datetime


class ScheduleEntry(BaseModel):
    weekday: int   # 1–5 (Mon–Fri)
    period: int    # 1–8
    subject: str
    teacher: str
    class_code: str


TimeSlot: TypeAlias = tuple[int, int]  # (weekday, period)

class Lookup(BaseModel):
    """
    用兩層 dict 取代複雜 SQL：
    - teacher_lookup[teacher][(weekday, period)] = ScheduleEntry
    - class_lookup[class_code][(weekday, period)] = ScheduleEntry
    """
    teacher_lookup: Dict[str, Dict[TimeSlot, ScheduleEntry]]
    class_lookup:  Dict[str, Dict[TimeSlot, ScheduleEntry]]
    last_update:   datetime  # 嚴格格式：%Y/%m/%d %H:%M:%S


class CourseInfo(BaseModel):
    subject: str
    main: str
    counterpart: str
    url: Optional[str] = None

class ClassTable(BaseModel):
    table: List[List[Optional[CourseInfo]]]
    # 5 weekdays x 8 periods
    type: Literal["class", "teacher"]
    target: str # name of the class or teacher
    target_url: str # URL of the class or teacher   
