import os
from typing import Dict
from pathlib import Path

# 全域緩存
_instruction_cache: Dict[str, str] = {}

def get_system_instruction() -> str:
    """
    Returns the system instruction for the AI assistant.
    使用緩存機制並從檔案讀取指令內容。
    
    Returns:
        str: 系統指令內容
    """

    # ============ 設定當前使用的版本 =============
    version = "v3"
    # ============================================


    # 檢查緩存
    if version in _instruction_cache:
        return _instruction_cache[version]
    
    # 獲取檔案路徑
    current_dir = Path(__file__).parent
    instruction_file = current_dir / "system_instruction" / f"{version}.txt"
    
    # 讀取檔案內容
    try:
        with open(instruction_file, "r", encoding="utf-8-sig") as f:
                content = f.read()
                _instruction_cache[version] = content  # 儲存到緩存
                return content
    except FileNotFoundError:
            raise FileNotFoundError(f"系統指令檔案不存在：{instruction_file}")
    except UnicodeDecodeError:
            raise UnicodeDecodeError(f"檔案編碼錯誤：{instruction_file}，請確保使用 UTF-8 編碼")
    
