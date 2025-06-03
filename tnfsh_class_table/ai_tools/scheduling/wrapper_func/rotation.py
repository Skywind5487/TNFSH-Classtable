def rotation(
    source_teacher: str,
    weekday: int,
    period: int,
    teacher_involved: int,
    page: int,
    # 第一候選課程過濾條件
    include_weekdays: list[int | None] = [],
    exclude_weekdays: list[int | None] = [],
    include_periods: list[int | None] = [],
    exclude_periods: list[int | None] = [],
    morning_only: bool = False,
    afternoon_only: bool = False,
    destination_teacher: str | None = None,
    # 路徑過濾條件
    exclude_teachers: list[str | None] = []
):
    """
    多角調，內部又稱為輪調，是用於調課的其中一種方法。
    是教師通常習慣的調課方法。

    使用場景：
        1. 當涉及三人(含)以上的教師時，優先推薦多角調。
        2. 參數可能是用在「我不要跟某個老師調」、「我不要星期三早上的(開afternoon only)」之類的


    預設值說明：
        不啟用過濾條件時，使用以下預設值：
        - include_weekdays: [] (空列表，表示不限制包含的星期)
        - exclude_weekdays: [] (空列表，表示不限制排除的星期)
        - include_periods: [] (空列表，表示不限制包含的節次)
        - exclude_periods: [] (空列表，表示不限制排除的節次)
        - morning_only: False (不限制只能早上)
        - afternoon_only: False (不限制只能下午)
        - destination_teacher: None (None 表示不指定目標教師)
        - exclude_teachers: [] (空列表，表示不限制排除的教師)
        

    Args:
        source_teacher: 原授課教師名稱
        weekday: 星期（1-5）
        period: 節次（1-8）
        teacher_involved（2-5）: 參與多角調的教師總數
        page: 分頁頁碼（從1開始計數）
        
        # 從源頭開始找到的第一個選擇的過濾條件
        include_weekdays: 要包含的星期清單，例如 [1,2,3]
        exclude_weekdays: 要排除的星期清單，例如 [4,5]
        include_periods: 要包含的節次清單，例如 [1,2,3,4]
        exclude_periods: 要排除的節次清單，例如 [5,6,7,8]
        morning_only: 是否只要早上的課（1-4節）
        afternoon_only: 是否只要下午的課（5-8節）
        destination_teacher: 目標教師名稱（作為第一候選的教師）
        
        # 過濾條件
        exclude_teachers: 要排除的教師清單
        

    Raises:
        ValueError: 如果無法找到多角調課程，或參數不正確
    
    Returns:
        PaginatedResult: 分頁結果，包含輪調課程的詳細資訊

    Note:
        如果不需要使用過濾條件，可以傳入空列表([])或False。
        所有的過濾條件都是選用的，不使用時會採用預設值。
    """
    import asyncio
    from tnfsh_class_table.ai_tools.scheduling.rotation import async_rotation
    from tnfsh_class_table.ai_tools.scheduling.filter_func.base import FilterParams, FirstCandidateCourseFilters, PathFilters
    from tnfsh_timetable_core import TNFSHTimetableCore
    core = TNFSHTimetableCore()
    logger = core.get_logger()
    logger.info(f"開始輪調課程：教師={source_teacher}, 星期={weekday}, 節次={period}, 最大深度={teacher_involved}, 頁碼={page}")
    logger.debug(f"過濾條件：包含星期={include_weekdays}, 排除星期={exclude_weekdays}, \n包含節次={include_periods}, 排除節次={exclude_periods}, \n只要早上課={morning_only}, 只要下午課={afternoon_only}, \n排除教師={exclude_teachers}, 目標教師={destination_teacher}")


    # 將 list 轉換成 set
    filter_params = FilterParams(
        source=FirstCandidateCourseFilters(
            weekdays=set(include_weekdays) if include_weekdays else None,
            exclude_weekdays=set(exclude_weekdays) if exclude_weekdays else None,
            periods=set(include_periods) if include_periods else None,
            exclude_periods=set(exclude_periods) if exclude_periods else None,
            morning_only=morning_only,
            afternoon_only=afternoon_only,
            destination_teacher=destination_teacher
        ),
        path=PathFilters(
            exclude_teachers=set(exclude_teachers) if exclude_teachers else None
        )
    )

    # 檢查參數邏輯
    filter_params.logic_check()
    result = asyncio.run(async_rotation(
        source_teacher=source_teacher, 
        weekday=weekday, 
        period=period, 
        teacher_involved=teacher_involved, 
        page=page,
        filter_params=filter_params
    ))
    logger.info(f"找到 {len(result.options)} 條輪調課程")
    return result

def explain_rotation() -> str:
    """
    返回多角調的解釋說明。

    使用場景：
        1. 當使用者需要了解多角調的概念和使用情境時。

    Returns:
        str: 多角調的解釋說明
    """
    return """
    多角調（又稱輪調、Rotation）是一種調課方法，通常用於涉及三人(含)以上的教師。
    是教師通常習慣的調課方法。
    當涉及三人(含)以上的教師時，優先推薦多角調。

    具體的實作方法是：
    1. 選定**原課程**
    2. 從**原課程**所在的**原班級**中找到可以換的**對應課程**
    3. 檢查**原課程**對應的**原老師**，在**對應課程**時是否有空
    4. 如果有空，則將**對應課程**作為新的**原課程**，並重複步驟2-4，直到找到最一開始的課程，形成一個環狀結構。

    """

if __name__ == "__main__":    # 測試輪調功能
    result = rotation(
        source_teacher="顏永進",  # 替換成實際的教師名稱
        weekday=3,               # 星期三
        period=2,               # 第二節
        teacher_involved=2,      # 兩位教師參與
        page=1,                 # 第一頁結果
        include_weekdays=[4],     # 限制只能是星期四
        exclude_weekdays=[],     # 不排除任何星期
        include_periods=[],      # 不限制節次
        exclude_periods=[],      # 不排除任何節次
        morning_only=False,      # 不限制只能早上
        afternoon_only=False,    # 不限制只能下午
        exclude_teachers=[],     # 不排除任何教師
        destination_teacher="黃先明"      # 指定要找這位老師的課
    )
    from google.genai import types
    from google import genai
    import os
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    fn_decl = types.FunctionDeclaration.from_callable(callable=rotation, client=client)
    import json
    print(f"函數聲明: {json.dumps(fn_decl.to_json_dict(), indent=2, ensure_ascii=False)}")  

    from tnfsh_class_table.ai_tools.scheduling.models import PaginatedResult
    result: PaginatedResult = result  # 假設返回的結果是 PaginatedResult 類型

    print("輪調結果:")
    print(f"頁數: {result.current_page}/{result.total_pages}")
    for option in result.options:
        print(f"路徑 ID: {option.route_id}")
        for step in option.route:
            print(f"路徑: {step.main_instruction}")  # 假設每個 node 有 name 屬性
            