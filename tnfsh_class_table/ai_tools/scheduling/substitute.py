from __future__ import annotations
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from tnfsh_class_table.ai_tools.scheduling.models import PaginatedSubstituteResult

from tnfsh_timetable_core import TNFSHTimetableCore 
core = TNFSHTimetableCore()
logger = core.get_logger()

from tnfsh_class_table.ai_tools.scheduling.models import random_seed

async def async_substitute(
        source_teacher:str, 
        weekday:int, 
        period:int, 
        source: Literal["official_website", "wiki"], 
        page:int) -> PaginatedSubstituteResult:
    """
    async 方法，請調用非 async 方法 `substitute` 來使用。
    """
    from math import ceil
    from tnfsh_class_table.ai_tools.scheduling.models import PaginatedSubstituteResult, CourseInfoWithTime, StreakTime
    from tnfsh_class_table.ai_tools.scheduling.models import TeacherNotFoundError, CourseNotFoundError, InvalidDataError

    logger.info(f"開始尋找代課教師：{source_teacher}, 星期={weekday}, 節次={period}, 模式={source}, 頁碼={page}")

    # 驗證基本參數
    if not isinstance(weekday, int) or not 1 <= weekday <= 5:
        raise ValueError(f"無效的星期：{weekday}，必須是 1-5 之間的整數")
    if not isinstance(period, int) or not 1 <= period <= 8:
        raise ValueError(f"無效的節次：{period}，必須是 1-8 之間的整數")
    if not source_teacher:
        raise ValueError("教師名稱不能為空")


    from tnfsh_timetable_core import TNFSHTimetableCore
    core = TNFSHTimetableCore()
    src_teacher_category = None    
    if source == 'official_website':
        forward_wiki_index = await core.fetch_index()
        reversed_wiki_index = forward_wiki_index.reverse_index
        teacher_info = reversed_wiki_index.get(source_teacher)
        
        if not teacher_info:
            logger.error(f"❌ 在官網找不到教師：{source_teacher}")
            raise TeacherNotFoundError(f"在官網找不到教師：{source_teacher}")

        src_teacher_category = teacher_info.category
        src_teacher_url = teacher_info.url
        if not src_teacher_category or not src_teacher_url:
            logger.error(f"❌ 教師 {source_teacher} 缺少必要資訊")
            raise InvalidDataError(f"教師 {source_teacher} 缺少必要資訊")
            
        src_teacher_prefix = src_teacher_url[1]
        index_index = forward_wiki_index.index
        candidate_teachers = index_index.teacher.data.get(src_teacher_category, {})
        substitute_teachers = {}
        for teacher, url in candidate_teachers.items():
            if teacher == source_teacher:
                continue
            if url[1] == src_teacher_prefix:
                substitute_teachers[teacher] = url
    elif source == 'wiki':
        from tnfsh_wiki_teachers_core import TNFSHWikiTeachersCore
        wiki_core = TNFSHWikiTeachersCore()
        wiki_index = await wiki_core.fetch_index()
        forward_wiki_index = wiki_index.index
        reversed_wiki_index = wiki_index.reverse_index
        
        teacher_info = reversed_wiki_index.get(source_teacher)
        if not teacher_info:
            logger.error(f"❌ 在 Wiki 中找不到教師：{source_teacher}")
            raise TeacherNotFoundError(f"在 Wiki 中找不到教師 {source_teacher} 的資訊")
            
        src_teacher_category = teacher_info.category
        if not src_teacher_category:
            logger.error(f"❌ 教師 {source_teacher} 在 Wiki 中缺少類別資訊")
            raise InvalidDataError(f"教師 {source_teacher} 在 Wiki 中缺少類別資訊")
            
        logger.debug(f"📚 找到教師類別：{src_teacher_category}")
        candidate_teachers = forward_wiki_index.get(src_teacher_category, {}).teachers
        substitute_teachers = {}
        for teacher, wiki_url in candidate_teachers.items():
            if teacher == source_teacher:
                continue
            substitute_teachers[teacher] = wiki_url
        
        index = await core.fetch_index()
        reversed_index = index.reverse_index
        substitute_teachers = {
            teacher: 
            reversed_index.get(teacher, {}).url 
            for teacher in substitute_teachers.keys() 
            if reversed_wiki_index.get(teacher, None) is not None
            and reversed_index.get(teacher, None) is not None
        }
    base_url = "http://w3.tnfsh.tn.edu.tw/deanofstudies/course"   

    scheduling = await core.fetch_scheduling()
    src_course_node = await scheduling.fetch_course_node(
        teacher_name=source_teacher,
        weekday=weekday,
        period=period
    )
    
    if not src_course_node:
        logger.error(f"❌ 找不到課程節點：週{weekday}第{period}節")
        raise CourseNotFoundError(f"找不到 {source_teacher} 在週{weekday}第{period}節的課程")

    timetable = await core.fetch_timetable(target=source_teacher)
    if not timetable or not timetable.table:
        logger.error(f"❌ 無法獲取課表：{source_teacher}")
        raise InvalidDataError(f"無法獲取 {source_teacher} 的課表")

    src_course_info = timetable.table[weekday-1][period-1]
    if not src_course_info:
        logger.error(f"❌ 指定時段沒有課程：週{weekday}第{period}節")
        raise CourseNotFoundError(f"{source_teacher} 在週{weekday}第{period}節沒有課程")

    logger.debug(f"✅ 成功找到課程：{src_course_info.subject}")
    src_course_info_with_time = CourseInfoWithTime(
        subject=src_course_info.subject,
        counterpart=[
            cp.participant for cp in (src_course_info.counterpart or [])
            if cp and cp.participant
        ],
        time=StreakTime(
            weekday=weekday,
            period=period,
            streak=getattr(src_course_node.time, 'streak', 1)
        )
    )

    free_substitute_teachers = {}
    for substitute_teacher, url in substitute_teachers.items():
        try:
            
            substitute_course_node = await scheduling.fetch_course_node(
                teacher_name=substitute_teacher,
                weekday=weekday,
                period=period,
                ignore_condition=True 
            )
            
            if (
                substitute_course_node
                and substitute_course_node.is_free):
                period_delta = src_course_node.time.period - substitute_course_node.time.period
                if (
                        substitute_course_node.time.streak >=
                        period_delta + src_course_node.time.streak
                    ):
                    free_substitute_teachers[substitute_teacher] = f"{base_url}/{url}"
        except Exception as e:
            # 忽略無法獲取課程節點的教師
            logger.error(f"無法獲取 {substitute_teacher} 的課程節點: {e}")
            continue
    logger.info(f"teacher_category: {src_teacher_category}")
    # 將結果分頁
    items_per_page = 5
    total_items = len(free_substitute_teachers)
    total_pages = ceil(total_items / items_per_page)
    
    # logger
    logger.debug(f"代課教師數量：{total_items}, 總頁數：{total_pages}, 頁碼：{page}")

    return PaginatedSubstituteResult(
        target=source_teacher,
        mode=source,
        current_page=page,
        total_pages=total_pages,
        teacher_category=str(src_teacher_category),
        source_course=src_course_info_with_time,
        options=free_substitute_teachers,
        items_per_page=items_per_page
    ).get_page(page)


if __name__ == "__main__":
    import asyncio
    source_teacher = "顏永進"
    weekday = 1
    period = 3
    mode = "official_website"  # or "wiki"
    page = 1
    
    result = asyncio.run(async_substitute(source_teacher, weekday, period, mode, page))
    print(result)