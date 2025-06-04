"""代課相關功能"""
from __future__ import annotations
from typing import Literal, TYPE_CHECKING
from math import ceil

from tnfsh_timetable_core import TNFSHTimetableCore
core = TNFSHTimetableCore()
logger = core.get_logger()

from tnfsh_class_table.ai_tools.scheduling.models import CourseInfoWithTime, StreakTime, random_seed, PaginatedSubstituteResult
from tnfsh_class_table.ai_tools.scheduling.cache import scheduling_cache, CacheKey

async def async_substitute(
        source_teacher:str, 
        weekday:int, 
        period:int, 
        source: Literal["official_website", "wiki"], 
        page:int,
        items_per_page: int = 10
) -> PaginatedSubstituteResult:
    """
    async 方法，請調用非 async 方法 `substitute` 來使用。
    """
    # logger: start
    logger.info(f"[Substitute] 開始尋找代課教師：{source_teacher}, 星期={weekday}, 節次={period}, 模式={source}, 頁碼={page}")
    try:
        # 驗證基本參數
        if not isinstance(weekday, int) or not 1 <= weekday <= 5:
            raise ValueError(f"無效的星期：{weekday}，必須是 1-5 之間的整數")
        if not isinstance(period, int) or not 1 <= period <= 8:
            raise ValueError(f"無效的節次：{period}，必須是 1-8 之間的整數")
        if not source_teacher:
            raise ValueError("教師名稱不能為空")

        # 獲取原課程節點
        scheduling = await core.fetch_scheduling()
        try:
            src_course_node = await scheduling.fetch_course_node(
                teacher_name=source_teacher, 
                weekday=weekday, 
                period=period,
                ignore_condition=False  # 忽略條件，確保能找到節點
            )
            streak = src_course_node.time.streak
            src_course_info_with_time = CourseInfoWithTime(
                subject=src_course_node.subject,
                time=src_course_node.time
            )
        except Exception as e:
            logger.warning(f"無法找到原課程節點: {str(e)}")
            streak = 1  # 如果找不到節點，預設為 1
            src_course_info_with_time = CourseInfoWithTime(
                subject="unknown",
                time=StreakTime(weekday=weekday, period=period, streak=streak)
            )

        logger.info(f"[Substitute] 開始尋找代課教師：{source_teacher}, 星期={weekday}, 節次={period}, 模式={source}, 頁碼={page}")

        # 嘗試從快取獲取結果
        cache_key = CacheKey(
            teacher_name=source_teacher,
            weekday=weekday,
            period=period,
            func_name="substitute",
            params=(source,)
        )
        
        cached_result = scheduling_cache.get(cache_key)
        if cached_result is not None:
            # 使用快取的結果
            free_substitute_teachers, src_teacher_category = cached_result
            logger.debug("使用快取的代課教師列表")
        else:
            if source == 'official_website':
                # ... official_website 處理邏輯 ...
                forward_wiki_index = await core.fetch_index()
                reversed_wiki_index = forward_wiki_index.reverse_index
                teacher_info = reversed_wiki_index.get(source_teacher)
                
                if not teacher_info:
                    logger.warning(f"在官網找不到教師：{source_teacher}")
                    return PaginatedSubstituteResult(
                        target=source_teacher,
                        mode=source,
                        teacher_category="unknown",
                        weekday=weekday,
                        period=period,
                        streak=1,
                        source_course=CourseInfoWithTime(
                            subject="unknown",
                            time=StreakTime(weekday=weekday, period=period, streak=1)
                        ),
                        current_page=1,
                        total_pages=0,
                        options={}
                    )

                src_teacher_category = teacher_info.category
                src_teacher_url = teacher_info.url
                if not src_teacher_category or not src_teacher_url:
                    logger.warning(f"教師 {source_teacher} 缺少必要資訊")
                    return PaginatedSubstituteResult(
                        target=source_teacher,
                        mode=source,
                        teacher_category="unknown",
                        weekday=weekday,
                        period=period,
                        streak=1,
                        source_course=src_course_info_with_time,
                        current_page=1,
                        total_pages=0,
                        options={}
                    )

                # 取得官網的代課教師列表
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
                # ... wiki 處理邏輯 ...
                from tnfsh_wiki_teachers_core import TNFSHWikiTeachersCore
                wiki_core = TNFSHWikiTeachersCore()
                wiki_index = await wiki_core.fetch_index()
                forward_wiki_index = wiki_index.index
                reversed_wiki_index = wiki_index.reverse_index
                
                teacher_info = reversed_wiki_index.get(source_teacher)
                if not teacher_info:
                    logger.warning(f"在 Wiki 中找不到教師：{source_teacher}")
                    return PaginatedSubstituteResult(
                        target=source_teacher,
                        mode=source,
                        teacher_category="unknown",
                        source_course=src_course_info_with_time,
                        current_page=1,
                        total_pages=0,
                        options={}
                    )

                src_teacher_category = teacher_info.category
                if not src_teacher_category:
                    logger.warning(f"教師 {source_teacher} 在 Wiki 中缺少類別資訊")
                    return PaginatedSubstituteResult(
                        target=source_teacher,
                        mode=source,
                        teacher_category="unknown",
                        weekday=weekday,
                        period=period,
                        streak=1,
                        source_course=src_course_info_with_time,
                        current_page=1,
                        total_pages=0,
                        options={}
                    )
                    
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

            else:
                logger.error(f"❌ 無效的資料來源：{source}")
                raise ValueError(f"無效的資料來源：{source}")

            base_url = "http://w3.tnfsh.tn.edu.tw/deanofstudies/course"   

            # 找出有空的代課教師
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
                        and substitute_course_node.is_free
                    ):
                        period_delta = src_course_node.time.period - substitute_course_node.time.period if src_course_node else 0
                        if (
                            substitute_course_node.time.streak >=
                            period_delta + streak
                        ):
                            free_substitute_teachers[substitute_teacher] = f"{base_url}/{url}"
                except Exception as e:
                    # 忽略無法獲取課程節點的教師
                    logger.error(f"無法獲取 {substitute_teacher} 的課程節點: {e}")
                    continue

            # 如果沒有找到可用的代課教師，返回空結果
            if not free_substitute_teachers:
                logger.warning(f"沒有找到可用的代課教師")
                return PaginatedSubstituteResult(
                    target=source_teacher,
                    mode=source,
                    current_page=1,
                    total_pages=0,
                    weekday=src_course_node.time.weekday if src_course_node else weekday,
                    period=src_course_node.time.period if src_course_node else period,
                    streak=src_course_node.time.streak if src_course_node else streak,
                    teacher_category=str(src_teacher_category),
                    source_course=src_course_info_with_time,
                    options={}
                )

            # 在找到可用的代課教師後，存入快取
            scheduling_cache.set(cache_key, (free_substitute_teachers, src_teacher_category))
            logger.debug("代課教師列表已快取")

        # 無論是使用快取還是新計算的結果，都用相同的邏輯處理分頁
        total_items = len(free_substitute_teachers)
        total_pages = ceil(total_items / items_per_page)

        logger.debug(f"[Substitute] 代課教師數量：{total_items}, 總頁數：{total_pages}, 頁碼={page}")
        result = PaginatedSubstituteResult(
            target=source_teacher,
            mode=source,
            weekday=src_course_node.time.weekday if src_course_node else weekday,
            period=src_course_node.time.period if src_course_node else period,
            streak=src_course_node.time.streak if src_course_node else streak,
            current_page=page,
            total_pages=total_pages,
            teacher_category=str(src_teacher_category),
            source_course=src_course_info_with_time,
            options=free_substitute_teachers,
            items_per_page=items_per_page
        )
        return result.get_page(page)

    except Exception as e:
        logger.error(f"查詢代課教師時發生錯誤: {str(e)}")
        return PaginatedSubstituteResult(
            target=source_teacher,
            mode=source,
            teacher_category="unknown",
            weekday=weekday,
            period=period,
            streak=streak,
            source_course=src_course_info_with_time,
            current_page=1,
            total_pages=0,
            options={}
        )


if __name__ == "__main__":
    import asyncio
    source_teacher = "顏永進"
    weekday = 1
    period = 3
    mode = "official_website"  # or "wiki"
    page = 1
    
    result = asyncio.run(async_substitute(source_teacher, weekday, period, mode, page))
    print(result)