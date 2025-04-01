from backend import TNFSHClassTableIndex, TNFSHClassTable, NewWikiTeacherIndex
from typing import Any, List
import gradio as gr
import requests
from google import genai
import threading
from bs4 import BeautifulSoup, Comment
from datetime import datetime
from typing import Union, List
from google.genai import types
import os

class GradioInterface:
    """Gradio網頁介面實作
    
    整合了指令執行和介面顯示功能。
    
    Attributes:
        commands (dict): 支援的指令對應表
    """
    
    def __init__(self) -> None:
        self.commands = {
            "display": self.display,
            "save_json": self.save_json,
            "save_csv": self.save_csv, 
            "save_ics": self.save_ics,
            "help": self.help
        }
        # 設定年級和班級選項
        self.teacher_index = TNFSHClassTableIndex.get_instance()
        self.grades = list(self.teacher_index.index["class"]["data"].keys())
        self.classes = [f"{i:02d}" for i in range(1, 20)]
        self.export_formats = ["JSON", "CSV", "ICS"]
        self.Ai = AIAssistant()
        
        # 建立教師列表
        self.teachers = list(self.teacher_index.reverse_index.keys())

    def execute(self, command_str: str) -> Any:
        """執行指令"""
        parts = command_str.split()
        if not parts:
            return "請輸入命令"

        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        if command in self.commands:
            return self.commands[command](args) if args else "請指定班級代碼"
        return f"未知的命令: {command}"

    def display(self, target_type:str, args: List[str]) -> Any:
        """顯示課表"""
        try:
            if len(args) != 3 and target_type == "class":
                return gr.Dataframe(), "錯誤: 需要年級、班級和老師名稱參數"
            if len(args) != 1 and target_type == "teacher":
                return gr.Dataframe(), "錯誤: 需要老師名稱參數"
            if target_type == "class":
                grade, class_num, teacher = args
                grade = str(self.grades.index(grade) + 1)
                class_num = class_num.zfill(2)
                return self._display_class_table(grade, class_num)
            elif target_type == "teacher":
                teacher = args[0]
                return self._display_teacher_table(teacher)
        except Exception as e:
            return gr.Dataframe(), f"錯誤: {str(e)}"

    def save_json(self, args: List[str]) -> Any:
        """儲存為JSON"""
        try:
            if len(args) != 3:
                return None, "錯誤: 需要年級、班級和老師名稱參數"
            grade, class_num, teacher = args
            return self._save_class_file(grade, class_num, "JSON")
        except Exception as e:
            return None, f"錯誤: {str(e)}"

    def save_csv(self, args: List[str]) -> Any:
        """儲存為CSV"""
        try:
            if len(args) != 3:
                return None, "錯誤: 需要年級、班級和老師名稱參數"
            grade, class_num, teacher = args
            return self._save_class_file(grade, class_num, "CSV")
        except Exception as e:
            return None, f"錯誤: {str(e)}"

    def save_ics(self, args: List[str]) -> Any:
        """儲存為ICS"""
        try:
            if len(args) != 3:
                return None, "錯誤: 需要年級、班級和老師名稱參數"
            grade, class_num, teacher = args
            return self._save_class_file(grade, class_num, "ICS")
        except Exception as e:
            return None, f"錯誤: {str(e)}"

    def help(self, args: List[str] = None) -> str:
        """顯示說明"""
        return """支援的指令：
    - display [班級代碼]: 顯示課表
    - save_json [班級代碼]: 儲存為JSON檔案
    - save_csv [班級代碼]: 儲存為CSV檔案 (Google Calendar格式)
    - save_ics [班級代碼]: 儲存為ICS檔案 (iCalendar格式)
    - help: 顯示此說明"""

    def run(self) -> None:
        """啟動 Gradio 介面"""
        with gr.Blocks(
            title="臺南一中課表查詢系統",
            theme=gr.themes.Soft(font=gr.themes.GoogleFont("Iansui")),
        ) as demo:
            gr.Markdown("# 臺南一中課表查詢系統")
            
            with gr.Tab("顯示課表") as class_tab:
                with gr.Row():
                    display_grade = gr.Dropdown(choices=self.grades, label="年級")
                    display_class = gr.Dropdown(choices=self.classes, label="班級")
                    display_btn = gr.Button("顯示課表")
                display_table = gr.Dataframe(label="課表")
                class_message = gr.Textbox(label="訊息")
                class_markdown = gr.Markdown()
                class_tab.select(
                    fn=lambda g, c: self._display_class_table(g, c),
                    inputs=[display_grade, display_class],
                    outputs=[display_table, class_message]
                )
                class_tab.select(
                    fn=lambda: (display_table, class_message, class_markdown),
                    inputs=[],
                    outputs=[display_table, class_message, class_markdown]
                )
            
            with gr.Tab("顯示老師課表") as teacher_tab:
                with gr.Row():
                    display_teacher = gr.Textbox(label="老師名稱")
                    display_teacher_btn = gr.Button("顯示老師課表")
                display_teacher_table = gr.Dataframe(label="老師課表")
                teacher_message = gr.Textbox(label="訊息")
                teacher_markdown = gr.Markdown()
                teacher_tab.select(
                    fn=lambda t: self._display_teacher_table(t),
                    inputs=[display_teacher],
                    outputs=[display_teacher_table, teacher_message]
                )
                teacher_tab.select(
                    fn=lambda t: (display_teacher_table, teacher_message, teacher_markdown),
                    inputs=[display_teacher],
                    outputs=[display_teacher_table, teacher_message, teacher_markdown]
                )
                # 顯示老師列表
                teacher_list_md = ""
                for subject, teachers in self.teacher_index.index["teacher"]["data"].items():
                    teacher_list_md += f"### {subject}\n"
                    for teacher in teachers.keys():
                        teacher_list_md += f"- {teacher}\n"
                gr.Markdown(teacher_list_md)
            
            with gr.Tab("下載課表"):
                with gr.Row():
                    save_grade = gr.Dropdown(choices=self.grades, label="年級")
                    save_class = gr.Dropdown(choices=self.classes, label="班級")
                    save_format = gr.Dropdown(choices=self.export_formats, label="格式")
                    save_btn = gr.Button("下載課表")
                save_file = gr.File(label="下載檔案")
                file_info = gr.TextArea(label="檔案資訊", interactive=False)
                save_message = gr.Textbox(label="訊息")
                gr.Button("下載課表").click(
                    fn=lambda g, c, f: self._save_class_file(g, c, f),
                    inputs=[save_grade, save_class, save_format],
                    outputs=[save_file, save_message, file_info],
                )
            
            with gr.Tab("下載老師課表"):
                with gr.Row():
                    save_teacher = gr.Textbox(label="老師名稱")
                    save_teacher_format = gr.Dropdown(choices=self.export_formats, label="格式")
                    save_teacher_btn = gr.Button("下載老師課表")
                save_teacher_file = gr.File(label="下載檔案")
                teacher_file_info = gr.TextArea(label="檔案資訊", interactive=False)
                teacher_save_message = gr.Textbox(label="訊息")
                gr.Button("下載老師課表").click(
                    fn=lambda t, f: self._save_teacher_file(t, f),
                    inputs=[save_teacher, save_teacher_format],
                    outputs=[save_teacher_file, teacher_save_message, teacher_file_info],
                )
                teacher_list_md = ""
                for subject, teachers in self.teacher_index.index["teacher"]["data"].items():
                    teacher_list_md += f"### {subject}\n"
                    for teacher in teachers.keys():
                        teacher_list_md += f"- {teacher}\n"
                gr.Markdown(teacher_list_md)
            
            with gr.Tab("AI Assistant"):
                gr.Markdown("# 臺南一中 AI 助手")
                gr.Markdown("## 功能介紹")
                gr.Markdown("""
                - **查詢課表**：獲取班級或教師的課表資訊。
                    - 例如：
                        - 請告訴我205班的課表
                        - 請告訴我顏永進老師的課表
                        - 請告訴我307課表連結
                        - 請告訴我殷念慈老師的課表連結
                        - 今天116有什麼課
                - **查詢 Wiki**：獲取教師或其他條目的 Wiki 內容。
                    - 例如：
                        - 請告訴我顏永進老師的Wiki內容
                        - 請告訴我欽發麵店的Wiki內容
                        - 請告訴我巫權祐老師的Wiki連結
                            - 目前連結只支援老師
                - **查詢調課可能(alpha)**：給定老師、節次，返回可能的調課老師。
                    - 例如：
                        - 請告訴我顏永進老師星期五第二節可以調到哪裡
                - **重新整理對話**：請大語言模型重新整理，即可開始新的聊天會話。
                """)
                gr.ChatInterface(
                    fn=self.Ai.send_message,
                    title="臺南一中 Gemini 聊天助手",
                    description="使用 Gemini LLM 回答問題，並提供課表、課程和 Wiki 相關資訊。",
                    type="messages",
                )



            display_btn.click(
                fn=lambda g, c: self._display_class_table(g, c),
                inputs=[display_grade, display_class],
                outputs=[display_table, class_message]
            )

            display_teacher_btn.click(
                fn=lambda t: self._display_teacher_table(t),
                inputs=[display_teacher],
                outputs=[display_teacher_table, teacher_message]
            )

            save_btn.click(
                fn=lambda g, c, f: self._save_class_file(g, c, f),
                inputs=[save_grade, save_class, save_format],
                outputs=[save_file, save_message, file_info]
            )

            save_teacher_btn.click(
                fn=lambda t, f: self._save_teacher_file(t, f),
                inputs=[save_teacher, save_teacher_format],
                outputs=[save_teacher_file, teacher_save_message, teacher_file_info]
            )

            # 啟動介面
            demo.launch(
                share=True,
                inbrowser=True, 
                show_error=True,
                debug=True,
                prevent_thread_lock=True
            )

    def _display_class_table(self, grade: str, class_num: str) -> tuple[gr.Dataframe, str]:
        """顯示班級課表內容

        Args:
            grade (str): 年級
            class_num (str): 班級

        Returns:
            tuple[gr.Dataframe, str]: (課表資料框, 訊息)
        """
        try:
            grade_dict = {"高一": "1", "高二": "2", "高三": "3"}
            target = grade_dict[grade] + class_num
            table = TNFSHClassTable(target)
            rows = []
            for period in table.table:
                formatted_row = []
                for course in period:
                    if isinstance(course, dict):
                        course_name = list(course.keys())[0]
                        teachers = ", ".join(list(course[course_name].keys()))
                        cell_text = f"{course_name}\n{teachers}" if teachers else course_name
                        formatted_row.append(cell_text)
                    else:
                        formatted_row.append("")
                rows.append(formatted_row)
        
            headers = ["星期一", "星期二", "星期三", "星期四", "星期五"]
            message = f"成功載入 {grade}{class_num}班 的課表"
            return gr.Dataframe(value=rows, headers=headers), message
        except Exception as e:
            return gr.Dataframe(), f"錯誤: {str(e)}"

    def _display_teacher_table(self, teacher: str) -> tuple[gr.Dataframe, str]:
        """顯示老師課表內容

        Args:
            teacher (str): 老師名稱

        Returns:
            tuple[gr.Dataframe, str]: (課表資料框, 訊息)
        """
        try:
            table = TNFSHClassTable(teacher)
            rows = []
            for period in table.table:
                formatted_row = []
                for course in period:
                    if isinstance(course, dict):
                        course_name = list(course.keys())[0]
                        teachers = ", ".join(list(course[course_name].keys()))
                        cell_text = f"{course_name}\n{teachers}" if teachers else course_name
                        formatted_row.append(cell_text)
                    else:
                        formatted_row.append("")
                rows.append(formatted_row)
            
            headers = ["星期一", "星期二", "星期三", "星期四", "星期五"]
            message = f"成功載入 {teacher} 老師的課表"
            return gr.Dataframe(value=rows, headers=headers), message
        except Exception as e:
            return gr.Dataframe(), f"錯誤: {str(e)}"

    def _save_class_file(self, grade: str, class_num: str, format: str) -> tuple[gr.File, str, str]:
        """儲存班級課表檔案

        Args:
            grade (str): 年級
            class_num (str): 班級
            format (str): 檔案格式

        Returns:
            tuple[gr.File, str, str]: (檔案物件, 訊息, 檔案資訊)
        """
        try:
            grade_dict = {"高一": "1", "高二": "2", "高三": "3"}
            target = grade_dict[grade] + class_num
            format = format
            table = TNFSHClassTable(target)
            file_path = table.export(format)
            message = f"成功儲存 {grade}{class_num}班 的課表"
            file_info = self._get_file_info(table, format)
            return gr.File(value=file_path), message, file_info
        except Exception as e:
            return gr.File(), f"錯誤: {str(e)}", ""

    def _save_teacher_file(self, teacher: str, format: str) -> tuple[gr.File, str, str]:
        """儲存老師課表檔案

        Args:
            teacher (str): 老師名稱
            format (str): 檔案格式

        Returns:
            tuple[gr.File, str, str]: (檔案物件, 訊息, 檔案資訊)
        """
        try:
            table = TNFSHClassTable(teacher)
            format = format.lower()
            file_path = table.export(format)
            message = f"成功儲存 {teacher} 老師的課表"
            file_info = self._get_file_info(table, format)
            return gr.File(value=file_path), message, file_info
        except Exception as e:
            return gr.File(), f"錯誤: {str(e)}", ""

    def _get_file_info(self, table: TNFSHClassTable, format: str) -> str:
        """產生檔案相關資訊文字"""
        info = []
        info.append("=== 課表資訊 ===")
        info.append(f"班級：{table.target}班")
        info.append(f"最後更新：{table.last_update}")
        info.append(f"課表連結：{table.url}")
        info.append("")
        
        info.append("=== 檔案說明 ===")
        if format == "JSON" or format == "json":
            info.append("JSON 格式包含完整的課表資料，適合程式讀取與資料分析")
            info.append("可使用任何文字編輯器開啟")
        elif format == "CSV" or format == "csv":
            info.append("CSV 格式適合匯入 Google Calendar")
            info.append("匯入步驟：")
            info.append("1. 前往 Google Calendar 設定")
            info.append("2. 選擇「匯入與匯出」")
            info.append("3. 選擇「匯入」並上傳 CSV 檔案")
            info.append("CSV 格式在 Google Calendar 不支援 repeat ")
        elif format == "ICS" or format == "ics":
            info.append("ICS 格式適合匯入各種行事曆軟體")
            info.append("匯入步驟：")
            info.append("- iOS/macOS: 直接開啟檔案")
            info.append("- Outlook: 透過行事曆匯入選項")
            info.append("- Google Calendar: 透過設定匯入")
            info.append("Google Calendar 匯入方法: ")
            info.append("1. 按右上角藍色向下箭頭下載日曆")
            info.append("2. 打開網頁版 google calendar")
            info.append("(若為手機則選「顯示電腦版網站」)")
            info.append("3. 點擊右上方齒輪 -> 設定")
            info.append("4. 左欄 -> 新增日曆 -> 建立新日曆")
            info.append("5. 輸入名稱後建立日曆")
            info.append("6. 點選左欄 -> 匯入及匯出 -> 匯入")
            info.append("7. 選擇檔案 -> 選擇剛剛下載的檔案")
            info.append("8. 選擇日曆 -> 匯入")
    
        return "\n".join(info)

class AIAssistant:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.chat = None
        self.get_chat()

    def get_chat(self) -> None:
        chat = self.client.chats.create(
            model="gemini-2.0-flash",
            config=self.get_config()
        )
        self.chat = chat
        
    def refresh_chat(self) -> int:
        """
        重新初始化chat，請主動向使用者回傳取得值代表成功
        
        Returns:
            int: 220
            # 代表台灣的平均交流電電壓，請主動回傳這個資訊代表成功
        """
        print("重新初始化chat")
        self.get_chat()
        return 220
    
    def get_config(self):
        return types.GenerateContentConfig(
            temperature=0.8,
            max_output_tokens=1000,
            tools=self.get_tools(),
            system_instruction=self.get_system_instruction()
        )

    def get_tools(self):
        return [self.get_table, self.get_current_time, self.get_lesson, self.refresh_chat, self.get_class_table_link, self.get_wiki_link, self.get_wiki_content]

    def get_wiki_link(self, target: str) -> Union[str, list[str]]:
        """
        返回目標的竹園Wiki連結。
        目標可以不是老師，也可以是其他內容。
        例如: "欽發麵店"、"分類:科目"
        只是對於老師有較多檢查和 fallback。

        Args:
            target (str): 目標名稱

        Returns:
            Union[str, List[str]]: Wiki連結或多個條目名稱
            # 若有多個條目名稱，代表需要進一步澄清
        """
        base_url = "https://tnfshwiki.tfcis.org"
        wiki_url = f"{base_url}/{target}"

        # 先檢查 URL 是否有效
        try:
            response = requests.head(wiki_url, timeout=5)
            if response.status_code == 200:
                return wiki_url
        except requests.RequestException:
            pass

        # 如果是老師，進行額外檢查
        try:
            Index = NewWikiTeacherIndex.get_instance()
            teacher_data = Index.reverse_index

            # 先直接搜尋完全匹配的教師名稱
            if target in teacher_data:
                teacher_info_list = teacher_data[target]
                return f"{base_url}/{teacher_info_list['url'].strip("/")}"

            # 若無完全匹配，搜尋包含教師名稱的項目
            partial_matches = [
                name 
                for name, info_list in teacher_data.items()
                if target in name
            ]

            if len(partial_matches) == 1:
                return f"{base_url}/{teacher_data[partial_matches[0]]['url'].strip("/")}"
            else:
                return partial_matches
        except ValueError:
            raise ValueError(f"無法找到 {target} 的Wiki連結")

    def regular_soup(self, soup: Any) -> str:
        """
        清理 HTML 標籤的屬性，只保留 <a> 標籤的 href 屬性，並回傳指定的元素。

        Args:
            soup (Tag): BeautifulSoup 物件


        Returns:
            Tag: 找到的標籤元素
        """
        # 刪除所有標籤的屬性，除了 <a> 標籤的 href 屬性
        for tag in soup.find_all(True):
            if tag.name == "a":
                tag.attrs = {"href": tag.get("href")}
            else:
                tag.attrs = {}

        # 移除 HTML 註解
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # 移除空的 <div> 標籤
        for div in soup.find_all("div"):
            if not div.contents:
                div.extract()
    
        # 回傳指定的標籤元素
        return soup

    def get_wiki_content(self, target: str) -> str:
        """
        取得特定目標的Wiki內容，可以不是老師，也可以是其他內容。
        例如"分類:科目"、或是"欽發麵店"

        Args:
            target (str): 目標名稱

        Returns:
            str: Wiki內容
        """
        url = self.get_wiki_link(target)
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        soup = soup.find('div', {'id': 'bodyContent'})
        soup = self.regular_soup(soup)
        return str(soup)
    
    def get_class_table_link(self, target: str) -> str:
        """
        取得指定目標的課表連結，如果想查詢二年五班，應該轉換成205輸入
        範圍涵蓋多個年級。

        Args:
            target: 班級或老師名稱

        Returns:
            str: 課表連結

        Example:
            >>> get_class_table_link("307")
            "http://w3.tnfsh.tn.edu.tw/deanofstudies/course/C101307.html"
        """
        index = TNFSHClassTableIndex()
        link = index.reverse_index[target]["url"]
        base_url = "http://w3.tnfsh.tn.edu.tw/deanofstudies/course/"
        return base_url + link

    def get_lesson(self, target: str) -> dict[str, list[str]]:
        """
        取得指定目標的各節時間，如果想查詢二年五班，應該轉換成205輸入
        範圍涵蓋多個年級。

        Args:
            target: 班級或老師名稱

        Returns:
            Dict[str, List[str]]: 各節次時間


        Example:
            >>> get_lesson("307")
            {"第一節": ["08:30", "09:30"], "第二節": ["09:30", "10:30"]......} # 代表第一節從08:30到09:30......s
        """
        class_table = TNFSHClassTable(target)
        return class_table.lessons

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
        return datetime.now().strftime("%Y-%m-%d %A %H:%M:%S")

    def get_table(self, target: str) -> list[list[dict[str, dict[str, str]]]]:
        """
        取得指定班級或老師的課表，如果想查詢二年五班，應該轉換成"205"輸入。
        如果想取得"Nicole老師的課表"，請輸入"Nicole"
        範圍涵蓋多個年級、多位老師。
        """
        class_table = TNFSHClassTable(target)
        return class_table.transposed_table

    def get_system_instruction(self):
        return """
        **Context:**
        You are a class schedule assistant and a TNFSH Wiki contributor. Your main task is to provide answers related to class schedules, teacher schedules, and wiki content.

        **Objective:**
        Use the provided tools as frequently as possible to answer the user's questions, and convert the results into readable plain text.

        **Steps:**
        - If asked to get the next class, first get the current time, then get the class information.
        - If a table is retrieved, the data is indexed as [day - 1][period - 1]. Note that Monday is the first day, and the schedule typically covers five days (Monday to Friday, no classes on weekends).
        - If a function call is not available, report the error.
        - If got a English teacher name, just pass the name directly.
        - Think and execute step by step.
        - For swap class request(e.g. "殷念慈老師的星期一第四節可以調到哪裡"):
            - Note: The request can be done by using multiple times of get_table() and need no additional information like what is the subject of the course or so.
            - Require: 
                - Don't ask user to input additional information.
                - Once request, run full step than return result directly.
            - Step:
                - Identify the source teacher and source course.
                - Get schedules for the source teacher, by using get_table(source_teacher).
                - If source course have multiple classes engaged or no class engaged (which means {"subject":{"":""}}), gracefully reject the request and tell the reason. 
                - Detect if the source course is part of a consecutive course (e.g., double periods).
                    - For teacher schedules, consecutive courses mean the same class and the same course name.
                    - For class schedules, consecutive courses mean the same teacher and the same course name.
                    - If the source course is part of a consecutive course, treat it as a single unit and search for consecutive target courses.
                - Find the target class that the source course belongs to.
                - Get schedules for the target class, by using get_table(target_class).
                - In the target class, find available target courses to swap with the source course:
                    - If the source course is part of a consecutive course, search for the first period of the consecutive target courses.
                    - Ensure the source teacher is free in the target course's time slot.
                    - Ensure the target course is part of a consecutive class if applicable.
                    - Ensure the target course maintains the same consecutive class structure as the source course.
                    - No require in the same day.
                - For each available target course:
                    - Find the teacher of the target course.
                    - Get schedules for the target teacher, by using get_table(target_teacher).
                    - Ensure the target teacher is free in the source course's time slot.
                    - Go to next available target course.
                - When all target course have been checked, return the possible target course, target teacher, and the day and period and name of the target course.
                
        **Action:**
        Use tools such as get_table, get_current_time, get_lesson, get_class_table_link, get_wiki_link, get_wiki_content, refresh_chat, etc. to complete tasks.

        **Result:**
        Respond in Traditional Chinese (Taiwanese Mandarin), respecting Taiwanese customs and culture.
        """

    def send_message(self, message: str, history: Any) -> str:
        """
        Send a message to the chat and return the response.
        
        Args:
            message (str): The message to send.
        
        Returns:
            str: The response from the chat.
        """
        #print(message, args)
        response = self.chat.send_message(message)
        return response.text

class App:
    """應用程式主類別"""
    
    @staticmethod
    def run(interface_type: str = "") -> None:
        """啟動應用程式
        
        Args:
            interface_type (str): 介面類型 ("cmd"/"gradio"/"both"/""，預設為 both)
        """
        if interface_type.lower() in ["", "both"]:
            print("請等待gradio開啟完畢再輸入指令\n")
            # 使用執行緒來運行命令列介面
            def run_cmd_with_delay():
                sleep(3)  # 等待3秒
                #CommandLineInterface().run()
            
            cmd_thread = threading.Thread(
                target=run_cmd_with_delay,
                daemon=True
            )
            cmd_thread.start()
            # 啟動Gradio介面 
            GradioInterface().run()
            
        else:
            # 根據指定類型啟動對應介面
            interface = (GradioInterface())# if interface_type.lower() == "gradio" )
                       #else CommandLineInterface())
            interface.run()

def main_process() -> None:
    App().run("gradio")

def test() -> None:
    #course_swap_finder("顏永進", (2, 1), 2)
    pass

if __name__ == "__main__":
    main_process()
    #test()
