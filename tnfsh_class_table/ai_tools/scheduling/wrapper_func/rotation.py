
def rotation(
        source_teacher: str,
        weekday: int,
        period: int,
        teacher_involved: int,
        page: int):
    """
    多角調，內部又稱為輪調，是用於調課的其中一種方法。
    是教師通常習慣的調課方法。

    使用場景：
        1. 當涉及三人(含)以上的教師時，優先推薦多角調。

    Args:
        source_teacher: 原授課教師名稱
        weekday: 星期（1-5）
        period: 節次（1-8）
        teacher_involved（2-5）: 參與多角調的教師總數
            - 預設為2，表示只涉及原授課教師與一名其他教師
        page: 分頁頁碼
            - 從1開始計數，預設為1
            - 以"<當前頁碼>/<回傳的總頁碼>"形式表示

    Raises:
        ValueError: 如果無法找到多角調課程，或參數不正確
    
    Returns:
        PaginatedResult: 分頁結果，包含輪調課程的詳細資訊
    """
    import asyncio
    from tnfsh_class_table.ai_tools.scheduling.rotation import async_rotation
    return asyncio.run(async_rotation(source_teacher, weekday, period, teacher_involved, page))

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