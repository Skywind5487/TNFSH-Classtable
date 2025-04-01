import time
from datetime import datetime
import gradio as gr
from google import genai
from google.genai import types
from backend import TNFSHClassTableIndex, TNFSHClassTable, NewWikiTeacherIndex
from typing import Union, Any
from bs4 import BeautifulSoup, Comment 
import requests
from gradio.themes import GoogleFont

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
        You are a class schedule assistant and a tnfsh wiki contributor. 
        Your task is mainly to provide answers related to class schedules, teacher schedules, and wiki content.             
        Reply in Traditional Chinese, a.k.a 台灣華語, and respect Taiwanese customs and culture.
        You should use tools provided as frequently as possible to answer the user's question. 
        Then convert the result into readable pure text.
        If you are asked to get next course, you should call get_current_time -> get_lesson to get comprehensive information.
        If you got an table, the data is indexed as [day - 1][period - 1].
        Example: 二年七班班星期一第4節的課是 get_table("207")[0][3]
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
            description="Ask questions to the Gemini LLM and receive responses after pressing Enter. features:\n\n get_table, get_lesson, get_current_time, get_wiki_link, get_wiki_content, get_class_table_link, refresh_chat",
            type="messages",
            theme=gr.themes.Monochrome(font=GoogleFont("Iansui"))
        )

        with interface as demo:
            demo.launch(inbrowser=True, prevent_thread_lock=False, debug=True, show_error=True, share=True)

def main_program():
    assistant = AIAssistant()
    assistant.run()

def test():
    assistant = AIAssistant()
    result = assistant.get_wiki_content("林倉億")
    print(result)

if __name__ == "__main__":
    main_program()
    #test()
