import random
from urllib import response

from tenacity import retry
from tnfsh_class_table.ai_tools.index.timetable_index import get_timetable_index
from tnfsh_class_table.backend import TNFSHClassTableIndex, TNFSHClassTable, NewWikiTeacherIndex

from typing import Any, List, Union, Optional, Literal, Dict, Generator
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
        self.model_name = "gemini-2.5-flash-preview-05-20"
        self.get_chat()

    @log_func
    def get_chat(self) -> None:
        chat = self.client.chats.create(
            model=self.model_name,
            config=self.get_config()
        )
        self.chat = chat
        
    def get_config(self):
        from tnfsh_class_table.ai_tools.system.system_instruction import get_system_instruction
        return types.GenerateContentConfig(
            temperature=0.3,
            top_p=0.95,
            max_output_tokens=6000,
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

    from google.genai.types import Content  # 👈 加上這行

    def convert_to_gemini_format(self, history: list[dict]) -> list[Content]:
        from google.genai.types import Content, Part
        new_history = []
        for h in history:
            role = h.get("role")
            content = h.get("content")

            if role == "assistant":
                role = "model"  # ✅ Gemini 用 "model" 表示 AI 回應者
            elif role == "user":
                role = "user"   # ✅ OK

            if role and content:
                new_history.append(
                    Content(role=role, parts=[Part(text=content)])
                )
        return new_history
      
    

    def send_message(self, message: str, history: Any) -> Generator[str, None, None]:
        """
        發送訊息並以字符流的形式返回回應
        
        Args:
            message: 用戶輸入的訊息
            history: 聊天歷史記錄
            
        Yields:
            str: 逐字符的回應
        """
        from google.genai.errors import ServerError
        from tnfsh_timetable_core import TNFSHTimetableCore
        import time
        
        core = TNFSHTimetableCore()
        logger = core.get_logger()
        print("test")
        logger.info(f"[User Input] {message}")


        from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_fixed(2),
            retry=retry_if_exception_type(ValueError)   
        )
        def send_message_stream(message: str, history: list[dict]) -> Generator[str, None, None]:
            self.chat = self.client.chats.create(
                model=self.model_name,
                config=self.get_config(),
                history=self.convert_to_gemini_format(history)
            )        # 使用流式輸出        
            response_stream = self.chat.send_message_stream(message)
            # 測試 tenacity retry 功能
            print("測試 tenacity retry 功能")
            return response_stream  # 返回生成器，逐步返回回應的片段
        response_stream = send_message_stream(message, history)


        
        accumulated_text = ""
        for chunk in response_stream:
            if not chunk.text:
                continue
                
            # 逐字符輸出
            for char in chunk.text:
                accumulated_text += char
                time.sleep(0.01)  # 模擬逐字符輸出，避免過快
                yield accumulated_text  # 返回目前累積的全部文本
            
            # 記錄日誌
            logger.info(f"[AI Assistant][Chunk] {chunk.text}")

            try:
                if hasattr(chunk, "candidates") and chunk.candidates:
                    finish_reason = chunk.candidates[0].finish_reason
                    logger.info(f"[Gemini] Finish reason: {finish_reason}")
            except Exception as e:
                logger.debug(f"[Logger] Finish reason 資訊無法取得: {e}")

            try:
                usage = chunk.usage_metadata
                if usage:
                    logger.info(
                        f"[Gemini] tokens: prompt={usage.prompt_token_count}, "
                        f"response={usage.candidates_token_count}, total={usage.total_token_count}"
                    )
            except Exception as e:
                logger.debug(f"[Logger] Token 資訊無法取得: {e}")

        if not accumulated_text:
            logger.warning("[AI Assistant] 回應內容為空，請檢查輸入訊息或模型狀態。")
            yield "⚠️ 抱歉，沒有收到有效的回應。請稍後再試。"
            return
        return

        




def main():
    assistant = AIAssistant()
    history = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什麼我可以幫忙的嗎？"}
    ]
    message = "請問今天的課表是什麼？"

    print("AI 回應：")
    for response in assistant.send_message(message, history):
        print(response)

if __name__ == "__main__":
    main()