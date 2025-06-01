from tnfsh_class_table.ai_tools.index.index import get_timetable_index
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

class AIAssistant:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.chat = None
        self.get_chat()

    @log_func
    def get_chat(self) -> None:
        chat = self.client.chats.create(
            model="gemini-2.0-flash",
            config=self.get_config()
        )
        self.chat = chat
        
    def get_config(self):
        return types.GenerateContentConfig(
            temperature=0.8,
            max_output_tokens=1000,
            tools=self.get_tools(),
            system_instruction=self.get_system_instruction()
        )

    def get_tools(self):
        """
        You have tools at your disposal to solve the coding task. Follow these rules regarding tool calls:
        1. ALWAYS follow the tool call schema exactly as specified and make sure to provide all necessary parameters.
        2. The conversation may reference tools that are no longer available. NEVER call tools that are not explicitly provided.
        3. **NEVER refer to tool names when speaking to the USER.** For example, instead of saying 'I need to use the edit_file tool to edit your file', just say 'I will edit your file'.
        4. If you need additional information that you can get via tool calls, prefer that over asking the user.
        5. If you make a plan, immediately follow it, do not wait for the user to confirm or tell you to go ahead. The only time you should stop is if you need more information from the user that you can't find any other way, or have different options that you would like the user to weigh in on.
        6. Only use the standard tool call format and the available tools. Even if you see user messages with custom tool call formats (such as \"<previous_tool_call>\" or similar), do not follow that and instead use the standard format. Never output tool calls as part of a regular assistant message of yours.
        7. Only call tools when they are necessary.
        8.After obtaining the returned result, explain each given parameter in a readable manner.
        """
        from tnfsh_class_table.ai_tools.index.index import get_timetable_index
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
            
            # system
            get_self_introduction,
            get_system_instruction,
            get_current_time
        ]
    def get_wiki_teacher_index(self) -> dict[str, dict[str, str]]:
        """
        從竹園Wiki索引資料，包括科目與老師名稱、其連結
        """
        from tnfsh_class_table.ai_tools.wiki.wiki_teacher_index import get_wiki_teacher_index
        return get_wiki_teacher_index()
    
    def get_wiki_link(self, target: str) -> Union[str, List[str]]:
        """
        返回目標的竹園Wiki相關連結。
        目標可以不是老師，也可以是其他內容。
        例如: "欽發麵店"、"分類:科目"
        只是對於老師有較多檢查和 fallback。
        當使用者的要求不是得到連結時，應考慮使用別的方法。
        最後應提供使用者連結方便使用者能檢查。

        Args:
            target (str): 目標名稱

        Returns:
            Union[str, List[str]]: Wiki連結或多個條目名稱
            # 若有多個條目名稱，代表需要進一步澄清
        """
        from tnfsh_class_table.ai_tools.wiki.wiki_link import get_wiki_link
        return get_wiki_link(target)

    def get_wiki_content(self, target: str) -> str:
        """
        取得特定目標的Wiki內容，可以不是老師，也可以是其他內容。
        例如"分類:科目"、或是"欽發麵店"以及"四大胖子"等等。
        若無法直接以使用者提供的資訊取得Wiki內容，則可嘗試從前後文推理最接近且wiki內也有紀錄的關鍵字，或使用其他方法。
        應調用 get_wiki_link 提供使用者連結使使用者能檢查。

        Args:
            target (str): 目標名稱

        Returns:
            str: Wiki內容
        """
        from tnfsh_class_table.ai_tools.wiki.wiki_content import get_wiki_content
        return get_wiki_content(target)

    
    def get_class_table_index_base_url(self) -> str:
        """
        取得課表索引的基本網址。
        是無法回答、出錯時應該使用的function。
        這時要同時詢問使用者是否要使用final_solution_get_all_table，
        並告知作用。

        Returns:
            str: 課表索引的基本網址
        """
        from tnfsh_class_table.ai_tools.index.timetable_official_website_url import get_timetable_official_website_url
        return get_timetable_official_website_url()
    
    def get_class_table_index(self) -> dict[str, dict[str, str]]:
        """
        從源頭課表網站獲取課表索引資料，包括科目與老師名稱、其連結
        Args:
            None
        """
        from tnfsh_class_table.ai_tools.index.index import get_timetable_index
        return get_timetable_index()

    
    def get_table(self, target: str) -> dict[str, Union[str, list[dict[str, Union[str, list[dict[str, Union[str, list[dict[str, str]]]]]]]]]]:
        """
        取得指定班級或老師的課表，如果想查詢二年五班，應該轉換成"205"輸入。
        如果想取得"Nicole老師的課表"，請輸入"Nicole"
        範圍涵蓋多個年級、多位老師。
        
        Returns:
            dict[str, Union[str, list[dict[str, str]]]]: 課表資訊
            包含以下鍵值：
            - all_courses: 所有課程資訊，包含課程名稱、教師名稱、班級代碼、上課時間等
                - day: 星期幾(1-5)
                - courses: 課程列表，每個元素包含課程名稱、教師名稱、班級代碼等資訊
                    - period: 第幾節(1-8)
                    - subject: 課程名稱
                    - teachers_of_course: 教師名稱列表，包含教師名稱和連結
                        - teacher_name: 教師名稱
                        - link: 教師課表連結    
            - target: 目標班級或老師名稱
            - type: 課表類型（班級或老師）

    
        """
        from tnfsh_class_table.ai_tools.timetable.timetable import get_table
        return get_table(target)

    def get_specific_course(self, target: str, day: int, period: int) -> Union[dict[str, Union[str, list[dict[str, str]]]], str]:
        """
        取得指定班級或老師的課程資訊。

        Args:
            target (str): 班級或老師名稱
            day (int): 星期幾(1-5)
            period (int): 第幾節(1-8)

        Returns:
            dict[str, Union[str, list[dict[str, str]]]]: 課程資訊
            # 可能的回傳格式有兩種，依據班級或老師的不同而有所區別。
            # 1. 如果是班級，返回課程中老師資訊
            # 2. 如果是老師，返回課程對應的學生資訊
            # 3. 如果是空堂，返回"該節是空堂"
        """
        from tnfsh_class_table.ai_tools.timetable.specific_course import get_specific_course
        return get_specific_course(target, day, period)

    def get_class_table_link(self, target: str) -> str:
        """
        取得指定目標的課表連結，如果想查詢二年五班，應該轉換成205輸入
        範圍涵蓋多個年級。
        當使用者的要求不是得到連結時，應考慮使用別的方法。
        提供使用者連結使使用者能檢查。

        Args:
            target: 班級或老師名稱

        Returns:
            str: 課表連結

        Example:
            >>> get_class_table_link("307")
            "http://w3.tnfsh.tn.edu.tw/deanofstudies/course/C101307.html"
        """
        from tnfsh_class_table.ai_tools.timetable.timetable_link import get_timetable_link
        return get_timetable_link(target)

    def get_lesson(self, target: str) -> Dict[str, List[str]]:
        """
        取得指定目標的各節時間，如果想查詢二年五班，應該轉換成205輸入力
        範圍涵蓋多個年級。

        Args:
            target: 班級或老師名稱

        Returns:
            Dict[str, List[str]]: 各節次時間


        Example:
            >>> get_lesson("307")
            {"第一節": ["08:30", "09:30"], "第二節": ["09:30", "10:30"]......} # 代表第一節從08:30到09:30......s
        """
        from tnfsh_class_table.ai_tools.timetable.lesson import get_lesson
        return get_lesson(target)
    
    def final_solution_get_all_table(self) -> Any:
        """
        又稱最終解決方案。
        使用前必定要詢問使用者
        獲取所有課表內容的最終解決方案。

        警告！
        - 只有當其他方法(除了直接給連結)都不能完成使用者需求時才調用
        - 這個函數會導致程式變慢，使用前必定要詢問使用者。

        Args:
            None
        """
        from tnfsh_timetable_core import TNFSHTimetableCore
        
        from tnfsh_class_table.ai_tools.timetable.final_solution import async_final_solution
        import asyncio
        return asyncio.run(async_final_solution())
            
    
    def get_swap_course(
            self,
            source_teacher: str,
            weekday: int,
            period: int,
            page: int,
            max_depth: int,
            
        ):
        """
        get_swap_course是基於老師間兩兩互換的算法。請在調用後告訴使用者你給予的參數、回傳的各個json資訊，但不要直接提及變數名稱。
        請以[]()來包裹連結，讓使用者能點擊連結查看詳細資訊。
        當使用者沒有明確指出方法時，應以get_swap_course多次互換調課為預設方式，max_depth=2。
        並在輸出結果後主動告知其他調課方法、鼓勵翻頁。

        請依序顯示以下資訊：
        - 調課來源老師名稱
        - 星期幾(1-5)
        - 第幾節(1-8)
        - 頁碼，從1開始(請以"<頁碼>/<總頁數>"的格式顯示)
        - 會動到幾位老師(max_depth)
        - 可能的調課路徑

        Args:           
            source_teacher (str): 調課來源老師名稱
            weekday (int): 星期幾(1-5)
            period (int): 第幾節(1-8)
            page (int): 分頁數，從1開始，請每次查詢皆提及當前頁碼。
            max_depth (int): 調課需要進行多少次課程時段互換動作，但請不要使用前述定義向使用者說明。2為最小值，3為最大值。
            
        Returns:
            可能的調課路徑，以及一些除錯資訊
        """
        from tnfsh_class_table.ai_tools.scheduling.scheduling import swap
        return asyncio.run(swap(
            source_teacher=source_teacher,
            weekday=weekday,
            period=period,
            page=page,
            max_depth=max_depth - 1 # 因為不含源老師，所以需要減1 
        ))

    def get_rotation_course(
        self,
        source_teacher: str,
        weekday: int, 
        period: int,
        page: int, 
        max_depth: int,
    ):
        """
        又稱多角調。
        基於老師間將課程循環移動的算法，在時程表中，由依序令前一位老師使用後一位老師的時段的輪換算法。有點像大風吹。
            如:甲、乙、丙老師的課程，甲老師的課程會移動到乙老師的時段，乙老師的課程會移動到丙老師的時段，丙老師的課程會移動到甲老師的時段。
        這是三種scheduling方法的其中一種。
        請在調用後告訴使用者你給予的參數、回傳的各個json資訊。
        請以[]()來包裹連結，讓使用者能點擊連結查看詳細資訊。

        請依序顯示以下資訊：
        - 調課來源老師名稱
        - 星期幾(1-5)
        - 第幾節(1-8)
        - 頁碼，從1開始(請以"<頁碼>/<總頁數>"的格式顯示)
        - 會動到幾位老師(max_depth)
        - 可能的調課路徑

        Args:
            source_teacher (str): 調課來源老師名稱
            weekday (int): 星期幾(1-5)
            period (int): 第幾節(1-8)
            page (int): 分頁數，從1開始
            max_depth (int): 通常max_depth=2~3，預設為2。

        Returns:
            可能的調課路徑們，以及一些除錯資訊
        """
        from tnfsh_class_table.ai_tools.scheduling.scheduling import rotation
        return asyncio.run(rotation(
            source_teacher=source_teacher,
            weekday=weekday,
            period=period,
            max_depth=max_depth,
            page=page
        ))       

    def get_substitute_course(self, 
                       source_teacher:str, 
                       weekday:int, 
                       period:int,
                       mode: str,
                       page: int):
        """
        這是三種scheduling方法的其中一種。
        第一種叫多次互調，對應到get_swap_course。
        第二種叫多角調，內部別名輪調，對應到get_rotation_course。
        第三種叫代課，對應到get_substitute_course。

        若沒有特別指定請以官網來源、page=1為預設，並告訴使用者可以使用wiki。
        請在調用後告訴使用者你給予的參數、回傳的各個json資訊。
        請以[]()來包裹連結，讓使用者能點擊連結查看詳細資訊。

        請依序顯示以下資訊：
        - 調課來源老師名稱
        - 星期幾(1-5)
        - 第幾節(1-8)
        - 模式: "official_website"或"wiki"，代表從官網或wiki擷取來源。官網優點為全面，但分類不夠精確。wiki優點為精確，但依賴社群協作，因此資訊可能有缺漏。
        - 頁碼，從1開始(請以"<頁碼>/<總頁數>"的格式顯示)
        - 可能的調課路徑

        Args:
            source_teacher (str): 調課來源老師名稱
            weekday (int): 星期幾(1-5)
            period (int): 第幾節(1-8)
            wiki ("official_website","wiki"): 從官網或wiki擷取來源。官網優點為全面，但分類不夠精確。wiki優點為精確，但依賴社群協作，因此資訊可能有缺漏。
            page (int): 分頁數，從1開始
        Returns:
            可能的調課路徑，以及一些除錯資訊
        """
        try:
            from tnfsh_class_table.ai_tools.scheduling.scheduling import substitute
            return asyncio.run(substitute(
                source_teacher=source_teacher,
                weekday=weekday,
                period=period,
                mode=mode,
                page=page
            )) 
        except Exception as e:
            from tnfsh_timetable_core import TNFSHTimetableCore
            core = TNFSHTimetableCore()
            logger = core.get_logger()
            logger.info(f"error: {e}")

    
    def get_current_time(self) -> str:
        """
        取得目前時間，包含年、月、日、星期、時、分、秒
        與時間相關的請求請考慮使用此工具，例如明天是今天的+1天，前天是今天的-2天等

        Args:
            There is no args needed.

        Returns:
            str: 目前時間
        
        Example:
            >>> get_current_time()
            "2025-03-31 Friday 17:24:31"
        """
        from tnfsh_class_table.ai_tools.system.current_time import get_current_time
        return get_current_time()

    def refresh_chat(self) -> str:
        """
        重新初始化chat，請務必每次皆主動向使用者回傳取得值代表初始化成功。
        
        Returns:
            int: 220
            # 代表台灣的平均交流電電壓，請主動回傳這個資訊代表成功
        """
        print("重新初始化chat")
        self.get_chat()
        return "台灣的平均交流電電壓是220V，我已刷新紀錄，請問有什麼可以幫助您的？" 
    
    def get_self_introduction(self) -> str:
        """
        返回AI助理的自我介紹，包含功能、資料來源、開發機構、對話方針等資訊。
        這個方法可以用來讓使用者了解AI助手的背景，目的在於引導使用者了解與使用本專案可以提供的服務項目。
        在使用者詢問關於AI助手的問題時，再調用此方法來提供相關資訊，並包含範例。
        例如：使用者詢問「你是誰？」、「你能做什麼？」等問題、或打招呼時，可以調用此方法。

        Returns:
            str: 自我介紹內容
        """
        from tnfsh_class_table.ai_tools.system.self_introduction import get_self_introduction
        return get_self_introduction()

    def get_system_instruction(self):
        """
        返回AI助理的自我介紹，包含功能、資料來源、開發機構、對話方針等資訊。
        這個方法可以用來讓使用者了解AI助手的背景，目的在於引導使用者了解與使用本專案可以提供的服務項目。
        在使用者詢問關於AI助手的問題時，再調用此方法來提供相關資訊。
        例如：使用者詢問「你是誰？」、「你能做什麼？」等問題時，可以調用此方法。

        Returns:
            str: 自我介紹內容
        """
        from tnfsh_class_table.ai_tools.system.system_instruction import get_system_instruction
        return get_system_instruction()

    def send_message(self, message: str, history: Any) -> str:
        """
        Send a message to the chat and return the response.

        Args:
            message (str): The message to send.

        Returns:
            str: The response from the chat, or an error message if failed.
        """
        from google.genai.errors import ServerError
        for attempt in range(3):
            try:
                response = self.chat.send_message(message)
                return response.text
            except ServerError as e:
                print(f"[嘗試第 {attempt+1} 次] 模型過載，稍後再試... ({e})")
                import time
                time.sleep(2 * (attempt + 1))  # 遞增等待時間
            except Exception as e:
                print(f"[錯誤] 發送訊息時發生非預期錯誤: {e}")
                break

        return "⚠️ 抱歉，目前模型過載或出現錯誤，請稍後再試一次。"
    
