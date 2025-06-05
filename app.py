from tnfsh_class_table.interface import main_process
from tnfsh_timetable_core.timetable.cache import preload_all
import asyncio

asyncio.run(preload_all(only_missing=False, max_concurrent=5, delay=0.01))  # 預載入所有課表資料

main_process()
