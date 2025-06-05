from tnfsh_timetable_core.timetable.cache import preload_all
from tnfsh_class_table.ai_tools.scheduling.cache import scheduling_cache
import os
import asyncio
import logging
import threading
import time
from datetime import datetime
import shutil

# 設定日誌
from tnfsh_timetable_core import TNFSHTimetableCore
core = TNFSHTimetableCore()
logger = core.get_logger()

async def update_cache():
    try:
        # 1. 更新 timetable cache
        logger.info("開始更新課表快取...")
        await preload_all(only_missing=False, max_concurrent=5, delay=0.01)
        logger.info("課表快取更新完成")

        # 2. 清理 scheduling cache
        logger.info("開始清理排課快取...")
        scheduling_cache._cache.clear()
        logger.info("排課快取清理完成")


        
        logger.info("所有快取更新完成")
    except Exception as e:
        logger.error(f"快取更新過程中發生錯誤: {str(e)}")
        raise

def run_cache_update():
    while True:
        now = datetime.now()
        # 計算距離下一個凌晨 2 點的秒數
        next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
        if now.hour >= 2:
            next_run = next_run.replace(day=now.day + 1)
        
        delay = (next_run - now).total_seconds()
        logger.info(f"下次快取更新時間: {next_run}, 等待 {delay} 秒")
        time.sleep(delay)
        
        # 執行快取更新
        try:
            asyncio.run(update_cache())
            logger.info("快取更新完成")
        except Exception as e:
            logger.error(f"快取更新失敗: {str(e)}")

def start_cache_updater():
    """在新線程中啟動快取更新器"""
    updater_thread = threading.Thread(target=run_cache_update, daemon=True)
    updater_thread.start()
    return updater_thread

if __name__ == "__main__":
    start_cache_updater().join()  # 如果直接運行此腳本，會阻塞在這裡
