from __future__ import annotations
import requests
from bs4 import BeautifulSoup, Tag
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from abc import ABC, abstractmethod
import gradio as gr
import threading
import icalendar
from urllib.parse import unquote
from time import sleep
import os

class NewWiki:
    """
    新竹園 Wiki 資料處理類別

    提供與新竹園 Wiki 相關的功能，例如取得教師索引、科目列表等。
    """

    def __init__(self) -> None:
        """
        初始化 NewWiki 類別
        """
        self.base_url = "https://tnfshwiki.tfcis.org"
        self.teacher_index = self._get_new_wiki_teacher_index()
        self.teacher_reverse_index = self._build_teacher_reverse_index()
    
    def _get_new_wiki_normal_url(self, title: str) -> str:
        """
        生成新竹園 Wiki 的標準版 URL

        Args:
            title (str): 頁面標題

        Returns:
            str: 標準版 URL
        """
        url = f"{self.base_url}/{title}"
        return url
    
    def _get_new_wiki_mobile_url(self, title: str) -> str:
        """
        生成新竹園 Wiki 的行動版 URL

        Args:
            title (str): 頁面標題

        Returns:
            str: 行動版 URL
        """
        url = f"{self.base_url}/index.php?title={title}&mobileaction=toggle_view_mobile"
        return url
    
    def _get_new_wiki_teacher_index(self) -> Dict[str, Dict[str, Union[str, Dict[str, str]]]]:
        """
        從新竹園 Wiki 網站取得教師索引

        架構:
        {
            科目: {
                "url": "example.com",
                "teachers": {
                    老師名稱: URL
                }
            }
        }

        Returns:
            Dict[str, Dict[str, Union[str, Dict[str, str]]]]: 教師索引資料
        """
        def _get_new_wiki_subject() -> Dict[str, Dict[str, str]]:
            """
            取得科目列表

            Returns:
                Dict[str, Dict[str, str]]: 科目名稱與對應的 URL
            """
            title = "分類:科目"
            url = self._get_new_wiki_mobile_url(title)
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
            except requests.RequestException:
                return {}  # 若請求失敗，回傳空字典

            soup = BeautifulSoup(response.content, 'html.parser')
            # 取得第二個 mw-category-columns div (包含實際科目列表)
            #print(soup.find_all("div", class_="mw-category mw-category-columns"))
            subject_list = soup.find_all("div", class_="mw-category mw-category-columns")[1]

            subject_index = {}
            # 遍歷所有 a 標籤
            for subject in subject_list.find_all("a"):
                subject_name = subject.text.strip()
                subject_url = subject.get("href")
                if subject_name == "術與人文科":  # 跳過特定科目
                    continue
                if subject_name and subject_url:  # 確保資料有效
                    subject_index[subject_name] = {"url": unquote(subject_url)}

            return subject_index

        def _get_subject_teacher_list(subject_name: str) -> Dict[str, str]:
            """
            取得特定科目的教師列表

            Args:
                subject_name (str): 科目名稱

            Returns:
                Dict[str, str]: 教師名稱與對應的 URL
            """
            url = self._get_new_wiki_mobile_url(f"分類:{subject_name}老師")
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
            except requests.RequestException:
                return {}  # 若請求失敗，回傳空字典

            soup = BeautifulSoup(response.content, 'html.parser')
            if not soup.find("div", class_="mw-category"):
                return {}  # 若無教師資料，回傳空字典

            teacher_list = soup.find("div", class_="mw-category").find_all("a")
            teacher_names = [teacher.text for teacher in teacher_list]
            teacher_urls = [unquote(teacher.get("href")) for teacher in teacher_list]
            return dict(zip(teacher_names, teacher_urls))

        # 取得科目索引
        teacher_index = _get_new_wiki_subject()
        # 遍歷每個科目，取得對應的教師列表
        for subject_name in teacher_index:
            teacher_index[subject_name]["teachers"] = _get_subject_teacher_list(subject_name)

        return teacher_index
    
    def _build_teacher_reverse_index(self) -> Dict[str, Dict[str, str]]:
        """
        建立教師反查表，將教師名稱對應到其教授的科目與相關資訊

        Returns:
            Dict[str, Dict[str, str]]: 教師反查表
        """
        reverse_index = {}
        for subject, data in self.teacher_index.items():
            for teacher, teacher_url in data["teachers"].items():
                reverse_index[teacher] = {  # 直接存儲為字典
                    "subject": subject,
                    "new_wiki_url": self._get_new_wiki_normal_url(teacher_url.replace("/", ""))
                }
        return reverse_index
    def export_teacher_data_to_json(self, filepath: Optional[str] = None) -> str:
        """
        將教師索引與教師反查表匯出為單一 JSON 格式

        Args:
            filepath (str, optional): 輸出檔案路徑，若未指定則自動生成

        Returns:
            str: 實際儲存的檔案路徑

        Raises:
            Exception: 當檔案寫入失敗時
        """
        data = {
            "teacher_index": self.teacher_index,
            "reverse_teacher_index": self.teacher_reverse_index,
            "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # 如果未指定檔案路徑，則自動生成
        if filepath is None:
            filepath = f"new_wiki_teacher_data.json"
        
        # 寫入 JSON 檔案
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return filepath
        except Exception as e:
            raise Exception(f"Failed to write JSON file: {str(e)}")
class class_table:
    """課表處理的主要類別
    
    負責從學校網站擷取課表資訊並進行解析，提供多種匯出格式。
    
    Attributes:
        url (str): 課表網頁的URL
        soup (BeautifulSoup): 解析後的HTML內容
        soup_table (Tag): 課表的HTML元素
        regular_soup_table (Tag): 正規化處理後的課表HTML元素 
        lessons (Dict[str, List[str]]): 課程時間對應表 {"課程名稱": ["開始時間", "結束時間"], ...}
        table (List[List[Dict[str, Dict[str, str]]]]): 結構化的課表資料 [[{"國文": {"王小明": "TK07.HTML"}}, ...], ...]
        last_update (str): 課表最後更新時間
        class_ (Dict[str, Union[int, str]]): 班級資訊
    """

    class TableError(Exception):
        """課表處理相關錯誤的例外類別
        
        Args:
            message (str): 錯誤訊息
        """
        def __init__(self, message: str) -> None:
            self.message = message
            super().__init__(self.message)

    def __init__(self, url: str) -> None:
        """初始化課表物件
        
        Args:
            url (str): 課表網頁的URL
            
        Raises:
            TableError: 當網頁請求或解析失敗時
        """
        self.url: str = url
        self.soup: BeautifulSoup = self._get_soup()
        self.soup_table: Tag = self._get_soup_table()
        self.regular_soup_table: Tag = self._get_regular_soup_table()
        self.lessons: Dict[str, List[str]] = self._get_lesson()
        self.table: List[List[Dict[str, Dict[str, str]]]] = self._get_table()
        self.last_update: str = self._get_last_update()
        self.class_code: Dict[str, Union[int, str]] = self._get_class_code()

    def _get_soup(self) -> BeautifulSoup:
        """發送 GET 請求取得網頁 HTML 內容，並使用 BeautifulSoup 進行解析

        Returns:
            BeautifulSoup: 解析後的 HTML 內容

        Raises:
            TableError: 當網頁請求失敗時

        Example:
            >>> table = class_table("https://example.com/table.html")
            >>> soup = table.get_soup()
        """
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            raise self.TableError(f"網頁請求失敗: {str(e)}")

    def _get_last_update(self) -> str:
        """
        從 HTML 中擷取最後更新日期

        回傳:
        - last_update (str): 更新日期（若無法找到則回傳 "No update date found."）

        範例:
        >>> table = class_table("https://example.com/class_table.html")
        >>> table.get_last_update()
        '2025-03-09'
        """
        # 在 HTML 中尋找 <p> 標籤，屬性 class="MsoNormal"，align="center"
        update_element = self.soup.find('p', class_='MsoNormal', align='center')

        if update_element:
            # 找出所有的 <span> 標籤，通常用來包裹文字
            update_element = update_element.find_all('span')

            if len(update_element) > 1:
                # 第二個 <span> 內容通常是更新日期
                last_update = update_element[1].text.strip()
                return last_update

        # 若未找到更新日期
        return "No update date found."
    
    def _get_soup_table(self) -> Optional[Tag]:
        """取得課表的 HTML 元素"""
        # 找到 HTML 中所有 <table> 標籤
        tables = self.soup.find_all('table')

        if tables:
            return tables[0]
        
    def _get_regular_soup_table(self) -> Tag:
        CLASS_TABLE_CONTENT_WITH_LESSON_WITHOUT_NAP_LENGTH = 7
        not_boarder_pattern = lambda s: s and 'border' not in s
        
        new_table = BeautifulSoup('<table></table>', 'html.parser').table
        
        for row in self.soup_table.find_all('tr'):
            # 刪除包含 border 的 td
            for td in row.find_all('td'):
                if td.get('style') and 'border' in td['style']:
                    td.decompose()  # 直接刪除
                    
            # 檢查剩下的 td 數量是否正確
            if len(row.find_all('td')) == CLASS_TABLE_CONTENT_WITH_LESSON_WITHOUT_NAP_LENGTH:
                new_table.append(row)  # 將處理後的 row 加入新的 table
        
        return new_table

    def _get_lesson(self) -> Dict[str, List[str]]:
        """從課表資料中提取課程時間配對"""
        
        # 檢查是否有課表資料
        if not self.soup_table:
            return []

        lesson_names = []
        lesson_times = []
        import re
        re_pattern = r'(\d{2})(\d{2})'
        re_sub = r'\1:\2'
        for lesson_row in self.regular_soup_table.find_all('tr'):
            lesson_row = lesson_row.find_all('td')
            lesson_name = lesson_row[0].text.strip().replace("\n", "").replace("\r", "")
            lesson_time = [re.sub(re_pattern, re_sub, time.replace(" ","")) 
                           for time in lesson_row[1].text.strip().replace("\n", "").replace("\r", "").split("｜")]
            lesson_names.append(str(lesson_name))
            lesson_times.append(lesson_time)

        lessons = {}
        for lesson_name, lesson_time in zip(lesson_names, lesson_times):
            lessons[lesson_name] = lesson_time
        return lessons

    def _get_table(self) -> List[List[Dict[str, Dict[str, str]]]]:
        """解析課表內容為結構化資料

        Returns:
            List[List[Dict[str, str]]]: 課表二維陣列，每個元素為課程與教師的對應

        Example:
            >>> table = class_table(url).get_table()
            >>> print(table[0][0])  # 第一節星期一的課程
            {"國文": {"王小明": "TK07.HTML"}}
        """
        table = self.regular_soup_table.find_all('tr')
        def class_name_split(class_td) -> Union[Dict[str, str], str]:
            """分析課程字串為課程名稱和教師名稱"""
            ps = class_td.find_all('p')
            if len(ps) == 0:
                return ps
            class_teacher = ps[-1].text.strip("\n").strip("\r").replace(" ","")
            class_teacher_link = ps[-1].find('a').get('href') if ps[-1].find('a') else ""
            class_name = ''.join([p.text for p in ps[:-1]]).strip("\n").strip("\r").replace(" ","")
            return {class_name: {class_teacher: class_teacher_link}} if class_name else class_teacher

        return [[
            class_name_split(class_) for class_ in row.find_all('td')[2:]
        ] for row in table]

    def _get_class_code(self) -> Dict[str, Union[int, str]]:
        """
        從HTML中提取班級資訊，並分離年級和班號

        回傳:
        - dict: 包含年級和班號的字典
        """
        class_spans = self.soup.find_all('span', style="font-family:\"微軟正黑體\",sans-serif;color:blue")
        if class_spans:
            # 取得班級文字
            class_text = class_spans[0].text.strip()
            # 使用正則表達式分離年級和班號
            pattern = r'([一二三四五六]年)(\d+)班'
            grades = {
                "一" : 1,
                "二" : 2,
                "三" : 3
            }
            match = re.match(pattern, class_text)
            if match:
                grade, class_num = match.groups()
                return {
                    "grade": grades[grade[0]],
                    "class": class_num
                }
        return {"grade": "", "class": ""}

    def _get_event_description(self, teacher: Dict[str, str]) -> str:
        def _get_a_href(url: str, text: str) -> str:
            return f'<a href="{url}">{text}</a>'

        def _get_new_wiki_teacher_links_and_name(teacher_name: str) -> List[Tuple[str, str]]:
            """取得新竹園 Wiki 教師連結列表，返回 (URL, 名稱) 的列表"""
            if not os.path.exists("new_wiki_teacher_data.json"):
                teacher_data = NewWiki().export_teacher_data_to_json()

            with open("new_wiki_teacher_data.json", "r", encoding="utf-8") as f:
                teacher_data = json.load(f)

            # 先直接搜尋完全匹配的教師名稱
            if teacher_name in teacher_data["reverse_teacher_index"]:
                teacher_info_list = teacher_data["reverse_teacher_index"][teacher_name]
                return [(teacher_info_list["new_wiki_url"], teacher_name)]

            # 若無完全匹配，搜尋包含教師名稱的項目
            partial_matches = [
                (info_list["new_wiki_url"], name) for name, info_list in teacher_data["reverse_teacher_index"].items()
                if teacher_name in name
            ]

            if partial_matches:
                return partial_matches
            else:
                # 如果還是找不到，嘗試直接生成 URL 並檢查是否有效
                base_url = "https://tnfshwiki.tfcis.org"
                teacher_url = f"{base_url}/{teacher_name}"
                try:
                    response = requests.head(teacher_url, timeout=5)
                    if response.status_code == 200:
                        partial_matches.append((teacher_url, teacher_name))
                except requests.RequestException:
                    pass

            return partial_matches

        description = []
        teacher_name = list(teacher.keys())[0]
        teacher_link = teacher[teacher_name]
        if teacher:
            teacher_url = f"http://w3.tnfsh.tn.edu.tw/deanofstudies/course/{teacher_link}"
            new_wiki_links = _get_new_wiki_teacher_links_and_name(teacher_name)
            tnfsh_official_url = "https://www.tnfsh.tn.edu.tw"
            tnfsh_lesson_information_url = "https://www.tnfsh.tn.edu.tw/latestevent/index.aspx?Parser=22,4,25"

            description.append(
                f"教師： {_get_a_href(teacher_url, f"{teacher_name}-課表")}\n"
                f"本班課表連結： {_get_a_href(self.url, f'{self.class_code['grade']}{self.class_code['class']}-課表')}\n"
            )

            if new_wiki_links:
                new_wiki_descriptions = []
                new_wiki_descriptions.append("新竹園wiki：")
                for link, name in new_wiki_links:
                    new_wiki_descriptions.append(f"{_get_a_href(link, name)} ")
                description.append("".join(new_wiki_descriptions))
            else:
                description.append("新竹園wiki： 無相關資料")

            description.append(
                f"南一中官網： {_get_a_href(tnfsh_official_url, '南一中官網')}"
                f"\n南一中官網-課程資訊： {_get_a_href(tnfsh_lesson_information_url, '教學進度、總體計畫、多元選修等等')}"
            )
        else:
            return "hi"
        return "\n".join(description)
    def export_to_json(self, filepath: Optional[str] = None) -> str:
        """將課表資料匯出為JSON格式
        
        Args:
            filepath (str, optional): 輸出檔案路徑，若未指定則自動生成
            
        Returns:
            str: 實際儲存的檔案路徑
            
        Raises:
            Exception: 當檔案寫入失敗時
            
        Example:
            >>> table = class_table("https://example.com/table")
            >>> filepath = table.export_to_json("output.json")
            >>> print(f"檔案已儲存至 {filepath}")
        """
        data: Dict[str, Any] = {
            "metadata": {
                "class": self.class_code,
                "last_update": self.last_update,
                "url": self.url,
                "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "content": {
                "lessons": self.lessons,
                "table": self.table
            }
        }

        # 如果未指定檔案路徑，則自動生成
        if filepath is None:
            class_info = self.class_code
            grade = class_info.get("grade", "0")
            class_num = class_info.get("class", "0")
            filepath = f"class_{grade}{class_num:02d}.json"

        # 寫入 JSON 檔案
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return filepath
        except Exception as e:
                raise Exception(f"Failed to write JSON file: {str(e)}")
    
    def export_to_csv(self, filepath: str = None) -> str:
        """將課表匯出為 Google Calendar 格式的 CSV"""
        import csv
        from datetime import timedelta
        if filepath is None:
            filepath = f"class_{self.class_code["grade"]}{self.class_code["class"]}.csv"
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ["Subject", "Start Date", "Start Time", "End Time", "Description", "Location", "Repeat"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                # 計算本週一的日期
                today = datetime.today()
                monday = today - timedelta(days=today.weekday())

                # 修改巢狀迴圈順序：先遍歷節次，再遍歷星期
                for lesson_index, lessons in enumerate(self.table):
                    lesson_index_name = list(self.lessons.keys())[lesson_index]
                    for day_index, day in enumerate(lessons):
                        if not day:
                            continue
                        lesson_name = list(day.keys())[0]
                        teacher = list(day.values())[0]
                        start_time, end_time = self.lessons[lesson_index_name]
                        
                        try:
                            current_date = monday + timedelta(days=day_index)
                            
                            start_datetime = datetime.strptime(f"{current_date.date()} {start_time}", "%Y-%m-%d %H:%M")
                            end_datetime = datetime.strptime(f"{current_date.date()} {end_time}", "%Y-%m-%d %H:%M")
                            
                            # 設定每週重複
                            repeat_rule = ("FREQ=WEEKLY;"
                                           "COUNT=52;"
                                           "BYDAY=MO,TU,WE,TH,FR;"
                                           "WKST=MO"
                            )  # 重複52週（一年）
                                                        
                            writer.writerow({
                                "Subject": lesson_name,
                                "Start Date": start_datetime.strftime("%m/%d/%Y"),
                                "Start Time": start_datetime.strftime("%I:%M %p"),
                                "End Time": end_datetime.strftime("%I:%M %p"),
                                "Description": self._get_event_description(teacher),
                                "Location": "701台南市東區民族路一段1號",
                                "Repeat": repeat_rule
                            })
                        except (IndexError, KeyError) as e:
                            print(f"警告：處理課程資料時發生錯誤: {e}")
                            continue
            return filepath
        
        except IOError as e:
            raise IOError(f"無法存取檔案 '{filepath}': {e}")
        except Exception as e:
            raise Exception(f"匯出 CSV 時發生未預期的錯誤: {e}")
    def export_to_ics(self, filename: str = None) -> str:
        """將課表匯出為 ICS 格式檔案"""
        if filename is None:
            filename = f"class_{self.class_code['grade']}{self.class_code['class']}.ics"
        from datetime import timedelta
        try:
            from icalendar import Calendar, Event
            
            # 建立日曆
            cal = Calendar()
            cal.add('prodid', f'-//{filename}_台南一中課表//TW')
            cal.add('version', '2.0')
            
            # 計算本週一的日期和目標結束日期
            today = datetime.today()
            monday = today - timedelta(days=today.weekday())
            
            # 計算到目標日期的週數
            if today.month >= 8:  # 下學期
                target_date = datetime(today.year + 1, 2, 1)
            else:  # 上學期
                target_date = datetime(today.year, 7, 1)
            
            weeks = ((target_date - monday).days // 7) + 1
            
            # 遍歷課表
            for lesson_index, lessons in enumerate(self.table):
                lesson_index_name = list(self.lessons.keys())[lesson_index]
                for day_index, day in enumerate(lessons):
                    if not day:
                        continue
                        
                    lesson_name = list(day.keys())[0]
                    teacher = list(day.values())[0]
                    start_time, end_time = self.lessons[lesson_index_name]
                    
                    try:
                        current_date = monday + timedelta(days=day_index)
                        
                        start_datetime = datetime.strptime(
                            f"{current_date.date()} {start_time}",
                            "%Y-%m-%d %H:%M"
                        )
                        end_datetime = datetime.strptime(
                            f"{current_date.date()} {end_time}",
                            "%Y-%m-%d %H:%M"
                        )
                        
                        # 建立事件
                        event = Event()
                        event.add('summary', lesson_name)
                        event.add('dtstart', start_datetime)
                        event.add('dtend', end_datetime)
                        event.add('location', '701台南市東區民族路一段1號')
                        event.add('description', self._get_event_description(teacher))
                        #event.add('description', "hi")

                        # 設定重複規則 - 只在特定星期重複到目標日期
                        weekday_map = {
                            0: 'MO',
                            1: 'TU',
                            2: 'WE',
                            3: 'TH',
                            4: 'FR'
                        }
                        event.add('rrule', {
                            'freq': 'weekly',
                            'count': weeks,
                            'byday': [weekday_map[day_index]]
                        })
                        
                        
                        cal.add_component(event)
                        
                    except (IndexError, KeyError) as e:
                        print(f"警告：處理課程資料時發生錯誤: {e}")
                        continue
                        
            # 寫入 ICS 檔案
            with open(filename, 'wb') as f:
                f.write(cal.to_ical())
            return filename
            
        except ImportError:
            raise Exception("請安裝 icalendar 套件: poetry add icalendar")
        except IOError as e:
            raise IOError(f"無法存取檔案 '{filename}': {e}")
        except Exception as e:
            raise Exception(f"匯出 ICS 時發生未預期的錯誤: {e}")
class CommandExecutor(ABC):
    """指令執行器的抽象基類
    
    定義了處理課表相關命令的基本介面。
    
    Attributes:
        _url_template (str): 課表URL的模板字串
    """
    
    def __init__(self) -> None:
        self._url_template: str = "http://w3.tnfsh.tn.edu.tw/deanofstudies/course/C{}{}.html"
    
    @abstractmethod
    def display(self, class_code: str) -> Any:
        """顯示課表內容的抽象方法
        
        Args:
            class_code (str): 班級代碼
            
        Returns:
            Any: 根據實作方式回傳不同格式的課表資料
        """
        pass
    
    @abstractmethod
    def save_json(self, class_code: str) -> Any:
        """儲存課表為JSON格式的抽象方法
        
        Args:
            class_code (str): 班級代碼
            
        Returns:
            Any: 根據實作方式回傳不同格式的結果
        """
        pass
    
    @abstractmethod
    def save_csv(self, class_code: str) -> Any:
        """儲存課表為CSV格式的抽象方法
        
        Args:
            class_code (str): 班級代碼
            
        Returns:
            Any: 根據實作方式回傳不同格式的結果
        """
        pass
    
    def _get_url(self, class_code: str) -> str:
        """
        根據班級代碼生成課表URL
        
        Args:
            class_code (str): 3位數的班級代碼
            
        Returns:
            str: 有效的課表URL
            
        Raises:
            TableError: 當班級代碼無效或無法找到對應課表時
        """
        class_type_list = [101, 106, 108]
        if not class_code.isdigit() or len(class_code) != 3:
            raise class_table.TableError("無效的班級代碼，須為3位數字")
            
        for class_type in class_type_list:
            try:
                url = self._url_template.format(class_type, class_code)
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    return url
            except requests.RequestException:
                continue
                
        raise class_table.TableError(f"無法找到班級 {class_code} 的課表")

    @abstractmethod
    def save_ics(self, class_code: str) -> Any:
        """儲存課表為ICS格式的抽象方法
        
        Args:
            class_code (str): 班級代碼
            
        Returns:
            Any: 根據實作方式回傳不同格式的結果
        """
        pass
class CmdExecutor(CommandExecutor):
    """命令列的指令執行器"""
    def display(self, class_code: str) -> Any:
        url = self._get_url(class_code)
        try:
            current_table = class_table(url)
            print("=== 課表內容 ===")
            for data in current_table.table:
                print("Table Data:\n", data)
            print("Last Update:\n", current_table.last_update)
            for lesson in current_table.lessons:
                print("Lessons:\n", lesson)
            print("Class:\n", current_table.class_code)
            return current_table.table
        except Exception as e:
            return f"發生錯誤: {str(e)}"

    def save_json(self, class_code: str) -> Any:
        url = self._get_url(class_code)
        try:
            filepath = class_table(url).export_to_json()
            return f"課表已成功儲存至 {filepath}"
        except Exception as e:
            return f"發生錯誤: {str(e)}"

    def save_csv(self, class_code: str) -> Any:
        url = self._get_url(class_code)
        try:
            filepath = class_table(url).export_to_csv()
            return f"課表已成功儲存至 {filepath}"
        except Exception as e:
            return f"發生錯誤: {str(e)}"
        
    def save_ics(self, class_code: str) -> Any:
        url = self._get_url(class_code)
        try:
            filepath = class_table(url).export_to_ics()
            return f"課表已成功儲存至 {filepath}"
        except Exception as e:
            return f"發生錯誤: {str(e)}"

class GradioExecutor(CommandExecutor):
    """Gradio介面的指令執行器"""
    def display(self, class_code: str) -> Any:
        url = self._get_url(class_code)
        try:
            table = class_table(url)
            # 轉換課表格式為 Dataframe 可用的格式
            rows = []
            for row in table.table:
                formatted_row = []
                for item in row:
                    if isinstance(item, dict):
                        subject = list(item.keys())[0]
                        teacher = item[subject]
                        formatted_row.append(f"{subject}\n{teacher}")
                    else:
                        formatted_row.append("")
                rows.append(formatted_row)
                
            # 建立欄位名稱（星期一到星期五）
            columns = ["星期一", "星期二", "星期三", "星期四", "星期五"]
            
            return gr.Dataframe(
                value=rows,
                headers=columns
            ), None
        except Exception as e:
            return gr.Dataframe(value=[[str(e)]])

    def save_json(self, class_code: str) -> Any:
        url = self._get_url(class_code)
        try:
            table = class_table(url)
            filepath = table.export_to_json()
            return gr.File(value=filepath)  
        except Exception as e:
            return gr.Dataframe(value=[[str(e)]])

    def save_csv(self, class_code: str) -> Any:
        url = self._get_url(class_code)
        try:
            table = class_table(url)
            filepath = table.export_to_csv()
            return gr.File(value=filepath)  
        except Exception as e:
            return gr.Dataframe(value=[[str(e)]])
    
    def save_ics(self, class_code: str) -> Any:
        url = self._get_url(class_code)
        try: 
            table = class_table(url)
            filepath = table.export_to_ics()
            return gr.File(value=filepath)
        except Exception as e:
            return gr.Dataframe(value=[[str(e)]])

# 修改 Commands 類別
class Commands:
    def __init__(self, executor: CommandExecutor) -> None:
        self.executor = executor
        self.commands = {
            "display": self.display,
            "save_json": self.save_json,
            "save_csv": self.save_csv,
            "save_ics": self.save_ics,
            "help": self.help
        }

    def execute(self, command_str: str) -> Any:
        parts = command_str.split()
        if not parts:
            return "請輸入命令"

        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        if command in self.commands:
            return self.commands[command](args)
        return f"未知的命令: {command}"

    def display(self, args: List[str]) -> Any:
        if not args:
            return "請指定班級代碼"
        return self.executor.display(args[0])

    def save_json(self, args: List[str]) -> Any:
        if not args:
            return "請指定班級代碼"
        return self.executor.save_json(args[0])

    def save_csv(self, args: List[str]) -> Any:
        if not args:
            return "請指定班級代碼"
        return self.executor.save_csv(args[0])

    def save_ics(self, args: List[str]) -> Any:
        if not args:
            return "請指定班級代碼"
        return self.executor.save_ics(args[0])

    def help(self, args: List[str] = None) -> str:
        return """支援的指令：
    - display [班級代碼]: 顯示課表
    - save_json [班級代碼]: 儲存為JSON檔案
    - save_csv [班級代碼]: 儲存為CSV檔案 (Google Calendar格式)
    - save_ics [班級代碼]: 儲存為ICS檔案 (iCalendar格式)
    - help: 顯示此說明"""

# 修改介面類別
class UserInterface(ABC):
    def __init__(self, executor: CommandExecutor) -> None:
        self.commands = Commands(executor)
    
    @abstractmethod
    def run(self) -> None:
        pass

class CommandLineInterface(UserInterface):
    def __init__(self) -> None:
        super().__init__(CmdExecutor())
    
    def run(self) -> None:
        while True:
            try:
                command = input("請輸入指令 (輸入 help 查看說明): ")
                if command.lower() == "exit":
                    break
                result = self.commands.execute(command)
                if isinstance(result, str):
                    print(result)
            except Exception as e:
                print(f"錯誤: {str(e)}")

class GradioInterface(UserInterface):
    """Gradio網頁介面實作
    
    提供網頁化的使用者介面，支援課表的顯示和檔案下載。
    """
    
    def __init__(self) -> None:
        super().__init__(GradioExecutor())
    
    def run(self) -> None:
        """啟動Gradio介面"""
        def handle_command(command: str) -> tuple[gr.components.Component, Optional[gr.components.Component]]:
            """處理使用者輸入的命令
            
            Args:
                command (str): 使用者輸入的命令字串
                
            Returns:
                tuple: (課表顯示元件, 檔案下載元件)
            """
            try:
                result = self.commands.execute(command)
                if isinstance(result, tuple):
                    return result
                elif isinstance(result, gr.Dataframe):
                    return result, None
                elif isinstance(result, gr.File):
                    return gr.Dataframe(value=[["檔案已生成"]]), result
                else:
                    return gr.Dataframe(value=[[str(result)]]), None
            except Exception as e:
                return gr.Dataframe(value=[[str(e)]]), None
        
        interface = gr.Interface(
            fn=handle_command,
            inputs=gr.Textbox(label="輸入指令"),
            outputs=[
                gr.Dataframe(label="課表"),
                gr.File(label="下載檔案")
            ],
            title="臺南一中課表查詢系統",
            description="輸入 help 查看可用指令"
        )
        interface.launch(share=True)

class App:
    """應用程式主類別"""
    def __init__(self) -> None:
        self.interfaces = {
            "cmd": CommandLineInterface,
            "gradio": GradioInterface,
            "both": None,
            "": None
        }
    
    def run(self, interface_type: str = "") -> None:
        if interface_type == "" or interface_type == "both":
            
            print("請等待gradio開啟完畢再輸入指令\n")
            # 使用執行緒來運行 Cmd
            cmd_thread = threading.Thread(
                target=self._run_cmd,
                daemon=True  # 設為 daemon thread，主程式結束時會自動結束
            )
            cmd_thread.start()
            gradio_interface = GradioInterface()
            gradio_interface.run()
            
        else:
            interface_class = self.interfaces.get(interface_type, CommandLineInterface)
            interface = interface_class()
            interface.run()
    
    def _run_cmd(self) -> None:
        """在獨立執行緒中運行 Cmd"""
        sleep(3)
        cmd_interface = CommandLineInterface()
        cmd_interface.run()

def main() -> None:
    app = App()
    interface_type = input("請選擇使用者介面(cmd / gradio / both，預設為 both): ")
    app.run(interface_type)

def test() -> None:
    def _get_url(class_code: str) -> str:
        """
        根據班級代碼生成課表URL
        
        Args:
            class_code (str): 3位數的班級代碼
            
        Returns:
            str: 有效的課表URL
            
        Raises:
            TableError: 當班級代碼無效或無法找到對應課表時
        """
        class_type_list = [101, 106, 108]
        if not class_code.isdigit() or len(class_code) != 3:
            raise class_table.TableError("無效的班級代碼，須為3位數字")
            
        for class_type in class_type_list:
            try:
                _url_template: str = "http://w3.tnfsh.tn.edu.tw/deanofstudies/course/C{}{}.html"
                url = _url_template.format(class_type, class_code)
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    return url
            except requests.RequestException:
                continue
                
        raise class_table.TableError(f"無法找到班級 {class_code} 的課表")
    test = class_table(_get_url("307"))
    test.export_to_ics()
    #test = NewWiki()
    #test.export_teacher_data_to_json()
    

if __name__ == "__main__":
    main()
    #test()