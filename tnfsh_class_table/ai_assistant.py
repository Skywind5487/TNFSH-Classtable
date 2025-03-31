import time
from datetime import datetime
import gradio as gr
from google import genai
from google.genai import types
from backend import TNFSHClassTableIndex, TNFSHClassTable, NewWikiTeacherIndex

class AIAssistant:
    def __init__(self):
        self.client = genai.Client(api_key='AIzaSyATCTiPbnypcnFeFJZuyuXCNK7DYXe_U6A')
        self.chat = None
        self.get_chat()

    def get_chat(self) -> None:
        chat = self.client.chats.create(
            model="gemini-2.0-flash",
            config=self.get_config()
        )
        self.chat = chat
        
    def refresh_chat(self) -> None:
        """
        重新初始化chat
        """
        print("重新初始化chat")
        self.get_chat()
    
    def get_config(self):
        return types.GenerateContentConfig(
            temperature=0.8,
            max_output_tokens=1000,
            tools=self.get_tools(),
            system_instruction=self.get_system_instruction()
        )

    def get_tools(self):
        return [self.get_table, self.get_current_time, self.get_lesson, self.refresh_chat]

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
        取得指定班級或老師的課表，如果想查詢二年五班，應該轉換成205輸入。
        範圍涵蓋多個年級。

        Args:
            target: 班級或老師名稱

        Returns:
            包含課表資訊的字典
            Dict[str, Dict[str, str]]: 格式為 {課程名稱: {教師名稱/班級代碼: 連結}}

        Note:
            課表資訊的索引方式為 [星期 - 1][節次 - 1]

        Example:
            >>> get_table("307")[4][3] # 代表三年七班星期五第4節的課
            {"國文": {"王小明": "http://example.com"}}
            
            >>> get_table("王小明")[4][3] # 代表王小明老師星期五第4節的課
            {"國文": {"307": "http://example.com"}}
        """
        class_table = TNFSHClassTable(target)
        transposed_table = list(map(list, zip(*class_table.table)))
        
        return transposed_table

    def get_system_instruction(self):
        #If any other question is asked, you can gracefully decline.
        return """
        You are a teacher assistant. Your task is to provide answers mainly related to class schedules.
        
        Reply in Traditional Chinese, a.k.a 台灣華語, and respecting Taiwanese customs and culture.
        You should use tools provided frequently to answer the user's question. Then convert the result into readable pure text.
        If you are asked to get next course, you should call get_current_time -> get_lesson to get comprehensive information.
        If you got an table, the data is indexed as [day - 1][period - 1].Example: 二年七班班星期一第4節的課是 get_table("207")[0][3]
        If function call is not available response the error.
        Let's think step by step.
        """ 

    def get_gemini_response(self, message):
        response = self.chat.send_message(message)

        return response.text

    def chatbot(self, message, history):
        
        response = self.get_gemini_response(message)
        return response

    def run(self):
        interface = gr.ChatInterface(
            fn=self.chatbot,
            title="Gemini Chat LLM Application",
            description="Ask questions to the Gemini LLM and receive responses after pressing Enter.",
            type="messages",
            theme="Zarkel/IBM_Carbon_Theme"
        )

        with interface as demo:
            demo.launch(inbrowser=True, prevent_thread_lock=False, debug=True, show_error=True)


if __name__ == "__main__":
    assistant = AIAssistant()
    assistant.run()
