# logger.py
import logging
import os
import inspect
from dotenv import load_dotenv

load_dotenv()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

def get_logger(logger_level:str="DEBUG") -> logging.Logger:
    # 自動取得呼叫此函數的模組名稱
    caller_frame = inspect.stack()[1]
    module = inspect.getmodule(caller_frame[0])
    name = module.__name__ if module else "unknown"

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, logger_level, logging.INFO))

    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        formatter = logging.Formatter(f"[%(levelname)s] [{name}] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
