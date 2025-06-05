from tnfsh_class_table.interface import main_process
from tnfsh_timetable_core.timetable.cache import preload_all
from cache_updater import start_cache_updater
import asyncio

# 預載入所有課表資料
asyncio.run(preload_all(only_missing=False, max_concurrent=5, delay=0.01))

# 啟動快取更新器
cache_updater_thread = start_cache_updater()

# 啟動主程序
main_process()
