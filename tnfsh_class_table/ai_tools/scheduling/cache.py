"""快取相關功能"""
from typing import Dict, List, Tuple, Any, Optional
import time
from dataclasses import dataclass
from tnfsh_timetable_core.scheduling.models import CourseNode

@dataclass
class CacheKey:
    """快取的鍵值"""
    teacher_name: str
    weekday: int
    period: int
    func_name: str
    params: tuple  # rotation 和 swap 用 (teacher_involved,)，substitute 用 (source,)

    def __hash__(self):
        return hash((self.teacher_name, self.weekday, self.period, self.func_name, self.params))

class SchedulingCache:
    """排課相關功能的快取
    使用 LRU (Least Recently Used) 策略管理快取
    """
    def __init__(self, max_size: int = 100, ttl: int = 36000):
        self._cache: Dict[CacheKey, Tuple[Any, float]] = {}  # (value, timestamp)
        self._max_size = max_size
        self._ttl = ttl  # Time To Live in seconds

    def get(self, key: CacheKey) -> Optional[Any]:
        """獲取快取的值"""
        if key not in self._cache:
            return None
        
        value, timestamp = self._cache[key]
        if time.time() - timestamp > self._ttl:
            # 超過 TTL，刪除快取
            del self._cache[key]
            return None

        # 更新使用時間
        self._cache[key] = (value, time.time())
        return value

    def set(self, key: CacheKey, value: Any):
        """設置快取的值"""
        # 如果快取已滿，移除最舊的項目
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache.items(), key=lambda x: x[1][1])[0]
            del self._cache[oldest_key]
        
        self._cache[key] = (value, time.time())

    def invalidate(self, teacher_name: str, weekday: int, period: int):
        """當課表發生變化時，清除相關的快取"""
        keys_to_remove = []
        for key in self._cache:
            if (key.teacher_name == teacher_name and 
                key.weekday == weekday and 
                key.period == period):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cache[key]

# 全域快取實例
scheduling_cache = SchedulingCache()
