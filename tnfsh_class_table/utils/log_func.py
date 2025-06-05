import functools

def log_func(func):
    """
    裝飾器：打印函數的執行過程與結果（同步函數專用）
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from tnfsh_timetable_core import TNFSHTimetableCore

        core = TNFSHTimetableCore()
        core.set_logger_level("DEBUG")
        logger = core.get_logger()

        logger.info(f"\n🟡 開始執行：{func.__name__}")
        logger.debug(f"參數 args={args}, kwargs={kwargs}")

        try:
            result = func(*args, **kwargs)
            logger.info(f"✅ {func.__name__} 執行成功")
            logger.debug(f"回傳值: {result}")
        except Exception as e:
            logger.error(f"❌ {func.__name__} 發生錯誤：{e}", exc_info=True)
            raise

        logger.info("🟢 執行結束 " + "=" * 30 + "\n")
        return result

    return wrapper