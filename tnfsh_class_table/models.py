from pydantic import BaseModel
from typing import List, Optional, Union

from pydantic_core import Url
from yarl import URL


class URLMap(BaseModel):
    """URL資料結構
    
    如果提供 base_url，url 屬性會自動加上 base_url 前綴。
    """
    name: str  # key
    url: str  # URLd


class CourseInfo(BaseModel):
    """課程資訊基本資料結構"""
    teacher: List[URLMap]  # 教師名稱列表
    subject: str  # 課程名稱
    class_: List[URLMap]  # 班級列表，使用 class_ 避免與 Python 關鍵字衝突
    weekday: int  # 星期幾(1-5)
    period: int  # 第幾節(1-8)
    streak: Optional[int] = None  # 連續課程長度（若非連續課程則為 None）


class SwapStep(BaseModel):
    """課程交換步驟"""
    from_: CourseInfo  # 來源課程
    to: CourseInfo  # 目標課程


class SwapSinglePath(BaseModel):
    """單一交換路徑"""
    steps: List[SwapStep]  # 交換步驟列表


class SwapPaths(BaseModel):
    """所有可能的交換路徑"""
    target: str  # 目標教師
    paths: List[SwapSinglePath]  # 可能的交換路徑列表


class TeacherClassInfo(BaseModel):
    """教師課程資訊的基本資料結構，用於輪調功能"""
    teacher: List[URLMap]  # 教師資訊列表
    class_: List[URLMap]  # 班級資訊列表
    subject: str  # 課程名稱
    weekday: int  # 星期幾(1-5)
    period: int  # 第幾節(1-8)
    streak: Optional[int] = None  # 連續課程長度（若非連續課程則為 None）


class RotationStep(BaseModel):
    """輪調步驟"""
    from_: TeacherClassInfo  # 來源課程
    to: TeacherClassInfo  # 目標課程
    next_teacher: List[URLMap]  # 下一個位置的老師資訊


class RotationSinglePath(BaseModel):
    """單一輪調路徑"""
    steps: List[RotationStep]  # 輪調步驟列表


class RotationPaths(BaseModel):
    """所有可能的輪調路徑"""
    target: str  # 目標教師
    paths: List[RotationSinglePath]  # 可能的輪調路徑列表