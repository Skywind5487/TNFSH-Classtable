from pydantic import BaseModel
from typing import Dict


class PeriodTime(BaseModel):
    start: str   # "08:00"
    end: str     # "08:50"

PeriodName = str  # "第一節"、"第二節"、"第三節"、"第四節"、"第五節"、"第六節"

class PeriodTimeTable(BaseModel):
    """課表時間表，存儲每節課的時間區段
    
    Attributes:
        time_table: 課節名稱到時間區段的映射，如 {"第一節": PeriodTime(start="08:00", end="08:50")}
    """
    time_table: Dict[PeriodName, PeriodTime]

    def __getitem__(self, key: PeriodName | int) -> PeriodTime:
        """透過課節名稱或索引取得時間區段
        
        Args:
            key: 課節名稱(如"第一節")或索引(0 代表第一節)
            
        Returns:
            PeriodTime: 該課節的時間區段
        """
        if isinstance(key, int):
            periods = list(self.time_table.keys())
            if 0 <= key < len(periods):
                return self.time_table[periods[key]]
            raise IndexError("課節索引超出範圍")
        return self.time_table[key]
    
    def get(self, key: PeriodName | int) -> PeriodTime | None:
        """安全地取得時間區段，如果不存在則返回 None"""
        try:
            return self[key]
        except (KeyError, IndexError):
            return None

    def to_raw_dict(self) -> dict[PeriodName, list[str]]:
        """轉換為原始字典格式，用於序列化"""
        return {
            name: [pt.start, pt.end]
            for name, pt in self.time_table.items()
        }

    @classmethod
    def from_raw_dict(cls, raw: Dict[PeriodName, list[str]]) -> "PeriodTimeTable":
        """從原始字典格式建立實例"""
        return cls(time_table={
            name: PeriodTime(start=pair[0], end=pair[1])
            for name, pair in raw.items()
        })
    
    def __iter__(self):
        """迭代所有課節時間區段"""
        return iter(self.time_table.items())

    def get_period_names(self) -> list[PeriodName]:
        """取得所有課節名稱的列表"""
        return list(self.time_table.keys())

    def get_period_by_index(self, index: int) -> PeriodTime:
        """透過索引取得課節的時間區段

        Args:
            index: 課節索引(0 代表第一節)
            
        Returns:
            tuple[PeriodName, PeriodTime]: (課節名稱, 時間區段)的元組
        """
        periods = list(self.time_table.keys())
        if 0 <= index < len(periods):
            period_name = periods[index]
            return self.time_table[period_name]
        raise IndexError("課節索引超出範圍")
        
    def __len__(self) -> int:
        """課節總數"""
        return len(self.time_table)

class CourseTable(BaseModel):
    """課表，存儲課程名稱和時間區段的映射
    
    Attributes:
        course_table: 課程名稱到時間區段的映射，如 {"數學": PeriodTime(start="08:00", end="08:50")}
    """
    course_table: Dict[str, PeriodTime]

    def __getitem__(self, key: str) -> PeriodTime:
        """透過課程名稱取得時間區段"""
        return self.course_table[key]
    
    def get(self, key: str) -> PeriodTime | None:
        """安全地取得時間區段，如果不存在則返回 None"""
        return self.course_table.get(key)