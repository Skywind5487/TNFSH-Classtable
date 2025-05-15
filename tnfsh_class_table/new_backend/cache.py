from typing import Dict
from pathlib import Path
import json
import logging
import os
from tnfsh_class_table.new_backend.models import ClassTable

# 設定日誌
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 第一層：記憶體快取
prebuilt_cache: Dict[str, ClassTable] = {}

# 第二層：本地 JSON 快取目錄
CACHE_DIR = Path(__file__).resolve().parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

def load_from_disk(target: str) -> dict:
    """從磁碟載入快取的課表資料。

    Args:
        target: 目標班級代號

    Returns:
        dict: 快取的課表資料，如果載入失敗則返回空字典
    """
    path = CACHE_DIR / f"prebuilt_{target}.json"
    try:
        if path.exists() and path.stat().st_size > 0:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                logger.debug(f"成功從 {path} 載入快取資料")  # 改為 debug 層級
                return data
        else:
            logger.debug(f"快取檔案 {path} 不存在或為空")  # 改為 debug 層級
    except json.JSONDecodeError as e:
        logger.error(f"快取檔案 {path} JSON 格式無效: {e}")  # 保留 error 層級
    except Exception as e:
        logger.error(f"讀取快取檔案 {path} 時發生錯誤: {e}")  # 保留 error 層級
    return {}

def save_to_disk(target: str, table: ClassTable) -> bool:
    """將課表資料儲存到磁碟快取。

    Args:
        target: 目標班級代號
        table: 要儲存的課表物件

    Returns:
        bool: 儲存是否成功
    """
    path = CACHE_DIR / f"prebuilt_{target}.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json_data = table.model_dump_json(indent=4)
            f.write(json_data)
            logger.debug(f"成功將資料儲存至 {path}")  # 改為 debug 層級
            return True
    except Exception as e:
        logger.error(f"儲存資料至 {path} 時發生錯誤: {e}")  # 保留 error 層級
        return False


async def preload_all(only_missing: bool = True, max_concurrent: int = 5):
    """
    預載入所有課表，加入併發上限控制，避免同時連線過多導致請求失敗。
    """
    from tnfsh_class_table.backend import TNFSHClassTableIndex
    import asyncio

    table_index = TNFSHClassTableIndex.get_instance().reverse_index
    targets = list(table_index.keys())
    logger.info(f"🔄 開始預載入所有課表，共 {len(targets)} 項")

    semaphore = asyncio.Semaphore(max_concurrent)

    async def process(target: str):
        if only_missing and (target in prebuilt_cache or load_from_disk(target)):
            logger.debug(f"快取已存在，略過：{target}")
            return
        async with semaphore:
            try:
                logger.debug(f"➡️ 開始預載入：{target}")
                await ClassTable.fetch_cached(target)
                logger.debug(f"✅ 預載入成功：{target}")
            except Exception as e:
                logger.error(f"❌ 預載入失敗 {target}: {e}")

    await asyncio.gather(*(process(t) for t in targets))
    logger.info("🏁 預載入完成")


if __name__ == "__main__":
    # 測試用
    import asyncio
    asyncio.run(preload_all(only_missing=False))
    print("預載入完成")