def final_solution():
    """
    一次取得所有課表的最終解決方案。
    有問題無法回答使用者時，請主動詢問是否要調用此方法。
    每次調用前都要詢問。
    """
    import asyncio
    from tnfsh_class_table.ai_tools.timetable.final_solution import async_final_solution
    return asyncio.run(async_final_solution())