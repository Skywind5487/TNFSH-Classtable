def final_solution():
    """
    一次取得所有課表的最終解決方案。

    使用指引:
        1. 每次調用前都要詢問。

    使用場景:
        1. 當使用者詢問「請給我所有課表」或「請給我所有老師的課表」時。
        2. 有問題無法回答使用者時，請主動詢問是否要調用此方法。

    """
    import asyncio
    from tnfsh_class_table.ai_tools.timetable.final_solution import async_final_solution
    return asyncio.run(async_final_solution())