from __future__ import annotations
from crawler import RawParsedResult
from typing import List, Dict, TypeAlias, Optional, Any, Literal
from pydantic import BaseModel
from datetime import datetime
from typing import ClassVar
import json


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

class CounterPart(BaseModel):
    participant: str
    url: str

class CourseInfo(BaseModel):
    subject: str
    main: str # name of the class or teacher
    counterpart: Optional[List[CounterPart]] # name of the class or teacher


class ClassTable(BaseModel):
    table: List[List[Optional[CourseInfo]]]  # 5 weekdays x 8 periods
    type: Literal["class", "teacher"]
    target: str
    target_url: str

    @classmethod
    def from_parsed(cls, target: str, parsed: RawParsedResult) -> "ClassTable":
        from tnfsh_class_table.backend import TNFSHClassTableIndex

        reverse_index = TNFSHClassTableIndex.get_instance().reverse_index
        target_url = reverse_index[target]["url"]
        type_ = "class" if target.isdigit() else "teacher"

        # ✅ 新增：轉置 parsed["table"] → weekday-major
        raw_table = parsed["table"]  # shape: [period][weekday]
        rotated_table = list(map(list, zip(*raw_table)))  # shape: [weekday][period]

        table: List[List[Optional[CourseInfo]]] = []

        for row in rotated_table:  # ✅ 改成處理轉置後的 row
            parsed_row: List[Optional[CourseInfo]] = []
            for cell in row:
                if not cell or cell == {"": {"": ""}}:
                    parsed_row.append(None)
                    continue

                subject = next(iter(cell))
                teachers_or_classes = cell[subject]  # Dict[name, url]

                # Prepare counterpart list
                counterpart_list = [
                    CounterPart(participant=name, url=url)
                    for name, url in teachers_or_classes.items()
                    if url and url != target_url
                ]

                # 判斷主體名稱
                main_name = target
                for name, url in teachers_or_classes.items():
                    if url == target_url:
                        main_name = name
                        break

                parsed_row.append(CourseInfo(
                    subject=subject,
                    main=main_name,
                    counterpart=counterpart_list if counterpart_list else None
                ))
            table.append(parsed_row)

        return cls(
            table=table,
            type=type_,
            target=target,
            target_url=target_url
        )

    @classmethod
    async def request(cls, target: str) -> "ClassTable":
        from crawler import fetch_raw_html, parse_html
        soup = await fetch_raw_html(target)
        parsed = parse_html(soup)
        return cls.from_parsed(target, parsed)


if __name__ == "__main__":
    # Example usage
    import asyncio
    class_table = asyncio.run(ClassTable.request("307"))
    print(json.dumps(class_table.model_dump(), indent=4, ensure_ascii=False))