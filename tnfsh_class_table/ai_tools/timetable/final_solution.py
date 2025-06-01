
async def async_final_solution():
    """
    async 方法，請調用非 async 方法 `final_solution` 來使用。
    """
    import asyncio
    from tnfsh_timetable_core import TNFSHTimetableCore
    core = TNFSHTimetableCore()
    logger = core.get_logger()

    # logger: start
    logger.info("🟡 開始執行 final_solution")
    index = await core.fetch_index()
    reverse_index = index.reverse_index.root
    
    # 使用 gather 並行獲取所有課表
    tasks = [
        core.fetch_timetable(teacher)
        for teacher, map in reverse_index.items()
    ]
    
    result = await asyncio.gather(*tasks)
    import json
    result = json.dumps([timetable.model_dump() for timetable in result], ensure_ascii=False)
    logger.info("✅ final_solution 執行成功")
    logger.debug(f"結果: {result[:100]}...")  # 只顯示前100個字符以避免過長輸出
    return result

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(async_final_solution())
    print(result)