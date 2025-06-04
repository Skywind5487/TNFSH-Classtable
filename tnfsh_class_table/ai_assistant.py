import random
from tnfsh_class_table.ai_tools.index.timetable_index import get_timetable_index
from tnfsh_class_table.backend import TNFSHClassTableIndex, TNFSHClassTable, NewWikiTeacherIndex

from typing import Any, List, Union, Optional, Literal, Dict
import requests
from google import genai
import asyncio
from bs4 import BeautifulSoup, Comment
from datetime import datetime
import os
from google.genai import types
from tnfsh_class_table.utils.log_func import log_func

random_seed = 42  # 固定隨機種子以確保可重現性

class AIAssistant:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.chat = None
        self.get_chat()

    @log_func
    def get_chat(self) -> None:
        chat = self.client.chats.create(
            model="gemini-2.5-flash-preview-05-20",
            config=self.get_config()
        )
        self.chat = chat
        
    def get_config(self):
        from tnfsh_class_table.ai_tools.system.system_instruction import get_system_instruction
        return types.GenerateContentConfig(
            temperature=0.3,
            top_p=0.95,
            max_output_tokens=4000,
            tools=self.get_tools(),
            system_instruction=get_system_instruction(),
            seed=random_seed
        )

    def get_tools(self):
        """
        Returns a list of tool functions that the AI assistant can use.
        """
        from tnfsh_class_table.ai_tools.index.timetable_index import get_timetable_index
        from tnfsh_class_table.ai_tools.index.timetable_official_website_url import get_timetable_official_website_url
        
        
        from tnfsh_class_table.ai_tools.timetable.timetable import get_table
        from tnfsh_class_table.ai_tools.timetable.specific_course import get_specific_course
        from tnfsh_class_table.ai_tools.timetable.timetable_link import get_timetable_link
        from tnfsh_class_table.ai_tools.timetable.lesson import get_lesson
        from tnfsh_class_table.ai_tools.timetable.wrapper_func.final_solution import final_solution

        from tnfsh_class_table.ai_tools.wiki.wiki_link import get_wiki_link
        from tnfsh_class_table.ai_tools.wiki.wiki_content import get_wiki_content
        from tnfsh_class_table.ai_tools.wiki.wiki_teacher_index import get_wiki_teacher_index
        
        from tnfsh_class_table.ai_tools.scheduling.wrapper_func.swap import swap
        from tnfsh_class_table.ai_tools.scheduling.wrapper_func.rotation import rotation
        from tnfsh_class_table.ai_tools.scheduling.wrapper_func.substitute import substitute
        from tnfsh_class_table.ai_tools.scheduling.wrapper_func.batch import batch_process

        from tnfsh_class_table.ai_tools.system.self_introduction import get_self_introduction
        from tnfsh_class_table.ai_tools.system.system_instruction import get_system_instruction
        from tnfsh_class_table.ai_tools.system.current_time import get_current_time


        return [
            # index
            get_timetable_index,
            get_timetable_official_website_url,

            # timetable
            get_table,
            get_specific_course,
            get_timetable_link,
            get_lesson,
            final_solution,

            # wiki
            get_wiki_link,
            get_wiki_content,
            get_wiki_teacher_index,

            # scheduling
            swap,
            rotation,
            substitute,
            batch_process,
            
            # system
            get_self_introduction,
            get_system_instruction,
            get_current_time,

            # self
            self.refresh_chat
        ]
    def refresh_chat(self) -> str:
        """
        當使用者說「重新初始化」、「刷新」、"refresh"時，調用此方法。
        重新初始化chat，請務必每次皆主動向使用者回傳取得值代表初始化成功。
        """
        print("重新初始化chat")
        self.get_chat()
        return "台灣的平均交流電電壓是220V，我已刷新紀錄，請問有什麼可以幫助您的？"

    def send_message(self, message: str, history: Any) -> str:
        from google.genai.errors import ServerError
        from tnfsh_timetable_core import TNFSHTimetableCore
        import time

        core = TNFSHTimetableCore()
        logger = core.get_logger()

        logger.info(f"[User Input] {message}")

        for attempt in range(3):
            try:
                raw_response = self.chat.send_message(message)
                try:
                    if hasattr(raw_response, "candidates") and raw_response.candidates:
                        finish_reason = raw_response.candidates[0].finish_reason
                        logger.info(f"[Gemini] Finish reason: {finish_reason}")
                    else:
                        logger.debug("[Logger] 無法取得 finish_reason，candidates 為空。")
                except Exception as e:
                    logger.debug(f"[Logger] Finish reason 資訊無法取得: {e}")

                logger.info(f"[AI Assistant][Full] {raw_response.text}")

                # 記錄模型與 token 資訊（如果有）
                try:
                    usage = raw_response.usage_metadata
                    if usage:
                        logger.info(
                            f"[Gemini] tokens: prompt={usage.prompt_token_count}, "
                            f"response={usage.candidates_token_count}, total={usage.total_token_count}"
                        )
                    else:
                        logger.debug("[Logger] 無法取得 usage_metadata。")
                except Exception as e:
                    logger.debug(f"[Logger] Token 資訊無法取得: {e}")
                if not raw_response.text:
                    logger.warning("[AI Assistant] 回應內容為空，請檢查輸入訊息或模型狀態。")
                    return "⚠️ 抱歉，沒有收到有效的回應。請稍後再試。"  
                return raw_response.text

            except ServerError as e:
                logger.warning(f"[Retry {attempt+1}] 模型過載，稍後再試... ({e})")
                time.sleep(2 * (attempt + 1))
            except Exception as e:
                logger.error(f"[錯誤] 發送訊息時發生非預期錯誤: {e}")
                break

        return "⚠️ 抱歉，目前模型過載或出現錯誤，請稍後再試一次。"
