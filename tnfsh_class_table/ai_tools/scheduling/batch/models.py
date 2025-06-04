"""批量處理結果的資料模型"""
from typing import List, Literal
from pydantic import BaseModel
from tnfsh_class_table.ai_tools.scheduling.models import PaginatedResult, PaginatedSubstituteResult

class BatchResult(BaseModel):
    """一位老師在一個時段內的多堂課調課結果"""
    teacher: str
    mode: Literal["rotation", "swap"]
    time_range: Literal["morning", "afternoon", "full_day"]
    results: List[PaginatedResult]


class BatchSubstituteResult(BaseModel):
    """一位老師在一個時段內的多堂課代課結果"""
    teacher: str
    mode: Literal["substitute"]
    time_range: Literal["morning", "afternoon", "full_day"]
    results: List[PaginatedSubstituteResult]
