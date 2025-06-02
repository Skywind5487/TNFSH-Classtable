from tnfsh_class_table.backend import TNFSHClassTableIndex, TNFSHClassTable, NewWikiTeacherIndex
from tnfsh_class_table.depth_1_change_course import change_course
from tnfsh_class_table.models import CourseInfo, SwapStep, SwapSinglePath, SwapPaths, URLMap

from typing import Any, List, Union, Optional, Literal
import gradio as gr
import requests
from google import genai
import threading
import asyncio
from bs4 import BeautifulSoup, Comment
from datetime import datetime
import os
import concurrent.futures
from google.genai import types


import asyncio

try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass  # nest_asyncio is optional but recommended for environments with an existing event loop







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
        from tnfsh_class_table.ai_assistant import AIAssistant
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
            gr.Markdown("[Hackmd](https://hackmd.io/@Skywind5487/tnfsh_class_table/edit)")
            with gr.Tab("下載課表"):
                gr.Markdown("# 下載到Google Calendar")
                gr.Markdown("請選ICS格式，並下載檔案後，請參考說明進行匯入")
                gr.Markdown("說明: [Google匯入日曆說明](https://support.google.com/calendar/answer/37118?hl=zh-Hant)")
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
                        - 請告訴我顏永進老師星期三第二節可以調到哪裡
                - **重新整理對話**：請大語言模型重新整理，即可開始新的聊天會話。
                """)
                gr.ChatInterface(
                    fn=self.Ai.send_message,
                    title="臺南一中 Gemini 聊天助手",
                    description="使用 Gemini LLM 回答問題，並提供課表、課程和 Wiki 相關資訊。",
                    type="messages",
                )
                refresh_btn = gr.Button("重新整理")

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
                """
                原本的老師課表顯示方式
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
                """
                
                # =====下拉式選單分別顯示科目與老師=====

                dropdown_list = {} 
                subject_dropdown = [] 
                
                def choose_subject(sbjt):
                    return gr.Dropdown(choices=dropdown_list[sbjt])
                    
                for subject, teachers in self.teacher_index.index["teacher"]["data"].items():
                    subject_dropdown.append(subject)
                    teacher_dropdown = []
                    for teacher in teachers.keys():
                        teacher_dropdown.append(teacher)  # 修正：直接加入教師名稱
                    dropdown_list[subject] = teacher_dropdown
                    
                with gr.Row():
                    subject_choice = gr.Dropdown(choices=subject_dropdown, label="科目", interactive=True)
                    teacher_choice = gr.Dropdown(choices=[], label="老師", interactive=True)
                    dropdown_teacher_btn = gr.Button("顯示老師課表")
                
                subject_choice.change(  # 改用 .change() 而不是 .select()
                    fn=choose_subject,
                    inputs=[subject_choice],
                    outputs=[teacher_choice]
                )
                dropdown_teacher_table = gr.Dataframe(label="老師課表")
                dropdown_teacher_btn.click(
                    fn=lambda t: self._display_teacher_table(t),
                    inputs=[teacher_choice],
                    outputs=[dropdown_teacher_table, teacher_message]
                )
                # ======下拉式選單結束=====
                """
                原先印出的各科目老師名單
                teacher_list_md = ""
                for subject, teachers in self.teacher_index.index["teacher"]["data"].items():
                    teacher_list_md += f"### {subject}\n"
                    for teacher in teachers.keys():
                        teacher_list_md += f"- {teacher}\n"
                gr.Markdown(teacher_list_md)
                """
                


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

            refresh_btn.click(
                fn=self.Ai.refresh_chat,
                inputs=[],
                outputs=[gr.Textbox(label="重新整理紀錄")]
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
                pass
                #sleep(3)  # 等待3秒
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
    from tnfsh_class_table.ai_assistant import AIAssistant
    aa = AIAssistant()
    bb = aa.get_table("顏永進")
    #bb = TNFSHClassTable("307").export("json")
    import json
    print(json.dumps(bb, indent=4, ensure_ascii=False))
    pass

if __name__ == "__main__":
    main_process()
    #test()
