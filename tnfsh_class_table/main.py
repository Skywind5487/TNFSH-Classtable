from __future__ import annotations
import requests
from bs4 import BeautifulSoup, Tag
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Tuple
from abc import ABC, abstractmethod
import gradio as gr
import threading
import icalendar
from urllib.parse import unquote
from time import sleep
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures

def print_format(data: Any, format: str = "json", remove_attrs: bool = True) -> None:
    """將資料輸出為指定格式的字串並直接打印
    
    Args:
        data: 要輸出的資料
        format (str): 輸出格式，支援 "json"、"html" 或 "2d_list" (預設為 "json")
        remove_attrs (bool): 是否移除 HTML 標籤的屬性 (預設為 True，但保留 href)
    """
    if format.lower() == "json":
        if hasattr(data, 'name'):  # 如果是 BeautifulSoup 元素
            output = json.dumps({
                'name': data.name,
                'text': data.text,
                'attrs': data.attrs
            }, ensure_ascii=False, indent=2)
        else:
            output = json.dumps(data, ensure_ascii=False, indent=2)
        print(output)
    
    elif format.lower() == "html":
        if isinstance(data, (str, BeautifulSoup, Tag)):
            try:
                # 如果是字串且看起來不像 HTML，直接打印
                if isinstance(data, str) and not data.strip().startswith('<'):
                    print(data)
                    return None
                
                # 建立新的 BeautifulSoup 物件
                soup = BeautifulSoup(str(data), 'html.parser')
                
                if remove_attrs:
                    for tag in soup.find_all():
                        if tag.name == 'a':
                            # 保留 a 標籤的 href
                            href = tag.get('href', '')
                            tag.attrs = {'href': href} if href else {}
                        else:
                            # 移除其他標籤的屬性
                            tag.attrs = {}
                
                # 移除空白行並打印
                output = soup.prettify()
                output = '\n'.join(line for line in output.split('\n') if line.strip())
                print(output)
            
            except Exception as e:
                print(f"HTML 解析錯誤: {e}")
                print(str(data))
        else:
            print(str(data))
    
    elif format.lower() == "2d_list":
        if isinstance(data, list) and all(isinstance(row, list) for row in data):
            for row in data:
                print("\t".join(map(str, row)))
        else:
            print("資料格式錯誤，無法以 2D 列表格式輸出")
    
    else:
        raise ValueError("不支援的格式。請使用 'json'、'html' 或 '2d_list'")
    
    return None


class TNFSHClassTableIndex:
    """台南一中課表索引的單例類別"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls) -> 'TNFSHClassTableIndex':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        # 確保初始化只執行一次
        if not TNFSHClassTableIndex._initialized:
            self.base_url = "http://w3.tnfsh.tn.edu.tw/deanofstudies/course/"
            self.index = self._get_index()
            self.reverse_index = self._build_reverse_index()
            TNFSHClassTableIndex._initialized = True

    def _get_index(self) -> Dict[str, Union[str, Dict[str, Union[str, Dict[str, Dict[str, str]]]]]]:
        """取得完整的台南一中課表索引"""
        urls = ("_ClassIndex.html", "_TeachIndex.html")
        data_types = ("class", "teacher")

        result = {
            "base_url": self.base_url,
            "root": "course.html"
        }

        for url, data_type in zip(urls, data_types):
            try:
                # 發送請求獲取頁面內容
                response = requests.get(self.base_url + url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                parsed_data = {}
                current_category = None
                for tr in soup.find_all("tr"):
                    category_tag = tr.find("span")
                    if category_tag and not tr.find("a"):
                        current_category = category_tag.text.strip()
                        parsed_data[current_category] = {}
                    for a in tr.find_all("a"):
                        link = a.get("href")
                        text = a.text.strip()
                        if text.isdigit() and link:
                            parsed_data[current_category][text] = link
                        else:
                            match = re.search(r'([\u4e00-\u9fa5]+)', text)
                            if match:
                                text = match.group(1)
                                parsed_data[current_category][text] =  link
                            else:
                                text = text.replace("\r", "").replace("\n", "").replace(" ", "").strip()
                                if len(text) > 3:
                                    text = text[3:].strip()
                                    parsed_data[current_category][text] = link

                result[data_type] = {
                    "url": url,
                    "data": parsed_data
                }

            except Exception as e:
                print(f"Error processing {data_type}: {str(e)}")
                result[data_type] = {
                    "url": url,
                    "data": {}
                }

        return result
    
    def _build_reverse_index(self) -> Dict[str, Dict[str, str]]:
        """建立反查表，將老師/班級對應到其 URL 和分類。

        Returns:
            Dict[str, Dict[str, str]]: 反查表結構為 {老師/班級: {url: url, category: category}}
        """
        reverse_index = {}
        
        # 處理教師資料
        if "teacher" in self.index:
            teacher_data = self.index["teacher"]["data"]
            for subject, teachers in teacher_data.items():
                for teacher_name, teacher_url in teachers.items():
                    reverse_index[teacher_name] = {
                        "url": teacher_url,
                        "category": subject
                    }

        # 處理班級資料
        if "class" in self.index:
            class_data = self.index["class"]["data"]
            for grade, classes in class_data.items():
                for class_num, class_url in classes.items():
                    reverse_index[class_num] = {
                        "url": class_url,
                        "category": grade
                    }
        
        return reverse_index
    
    def export_json(self, export_type: str = "all", filepath: Optional[str] = None) -> str:
        """匯出索引資料為 JSON 格式
        
        Args:
            export_type (str): 要匯出的資料類型 ("index"/"reverse_index"/"all"，預設為 "all")
            filepath (str, optional): 輸出檔案路徑，若未指定則自動生成
            
        Returns:
            str: 實際儲存的檔案路徑
            
        Raises:
            ValueError: 當 export_type 不合法時
            Exception: 當檔案寫入失敗時
        """
        # 驗證 export_type
        valid_types = ["index", "reverse_index", "all"]

        if export_type.lower() not in valid_types:
            raise ValueError(f"不支援的匯出類型。請使用 {', '.join(valid_types)}")
        
        if export_type == "all":
            export_type = "index_all"
        # 準備要匯出的資料
        export_data = {}
        if export_type.lower() == "index":
            export_data["index"] = self.index
        elif export_type.lower() == "reverse_index":
            export_data["reverse_index"] = self.reverse_index
        else:  # all
            export_data = {
                "index": self.index,
                "reverse_index": self.reverse_index
            }

        # 加入匯出時間
        export_data["export_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 如果未指定檔案路徑，則自動生成
        if filepath is None:
            filepath = f"tnfsh_class_table_{export_type}.json"

        # 寫入 JSON 檔案
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            return filepath
        except Exception as e:
            raise Exception(f"Failed to write JSON file: {str(e)}")
    
    def refresh(self) -> None:
        """重新載入索引資料"""
        self.index = self._get_index()
        self.reverse_index = self._build_reverse_index()
        
    @classmethod
    def get_instance(cls) -> 'TNFSHClassTableIndex':
        """取得單例實例
        
        Returns:
            TNFSHClassTableIndex: 索引類別的單例實例
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

class NewWikiTeacherIndex:
    """新竹園 Wiki 教師索引的單例類別"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls) -> 'NewWikiTeacherIndex':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        # 確保初始化只執行一次
        if not NewWikiTeacherIndex._initialized:
            self.base_url = "https://tnfshwiki.tfcis.org"
            # 使用線程池進行並發請求
            with ThreadPoolExecutor(max_workers=10) as executor:
                self.index = self._get_new_wiki_teacher_index(executor)
            self.reverse_index = self._build_teacher_reverse_index()
            NewWikiTeacherIndex._initialized = True
    
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
        url = f"{self.base_url}/index.php?title={title}"
        return url
    
    def _get_new_wiki_teacher_index(self, executor: ThreadPoolExecutor) -> Dict[str, Dict[str, Union[str, Dict[str, str]]]]:
        """並發從新竹園 Wiki 網站取得教師索引"""
        def _get_new_wiki_subject() -> Dict[str, Dict[str, str]]:
            title = "分類:科目"
            url = self._get_new_wiki_normal_url(title)
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')

                subject_list = soup.find_all("div", class_="mw-category")[1]
                #print(subject_list)
                subject_index = {}
                for subject in subject_list.find_all("a"):
                    subject_name = subject.text.strip()
                    subject_url = subject.get("href")
                    if subject_name == "藝術與人文科":
                        continue
                    if subject_name and subject_url:
                        subject_index[subject_name] = {"url": unquote(subject_url)}
                return subject_index
            except requests.RequestException:
                return {}

        def _get_subject_teacher_list(subject_name: str) -> Dict[str, str]:
            url = self._get_new_wiki_mobile_url(f"分類:{subject_name}老師")
            #print(url)
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                #print(response.status_code)
                soup = BeautifulSoup(response.content, 'html.parser')
                if not soup.find("div", class_="mw-category"):
                    return {}

                teacher_list = soup.find("div", class_="mw-category").find_all("a")
                teacher_names = [teacher.text for teacher in teacher_list]
                teacher_urls = [unquote(teacher.get("href")) for teacher in teacher_list]
                result = dict(zip(teacher_names, teacher_urls))
                #print(result)
                return result
            except requests.RequestException:
                return {}

        # 取得科目索引
        teacher_index = _get_new_wiki_subject()
        #print(teacher_index)
        if not teacher_index:
            return {}

        # 建立並發任務
        future_to_subject = {
            executor.submit(_get_subject_teacher_list, subject_name): subject_name
            for subject_name in teacher_index
        }

        # 收集結果
        for future in as_completed(future_to_subject):
            subject_name = future_to_subject[future]
            try:
                teacher_list = future.result()
                teacher_index[subject_name]["teachers"] = teacher_list
            except Exception as e:
                print(f"處理科目 {subject_name} 時發生錯誤: {e}")
                teacher_index[subject_name]["teachers"] = {}

        return teacher_index

    def _build_teacher_reverse_index(self) -> Dict[str, Dict[str, str]]:
        """建立教師反查表，將教師名稱對應到其科目與URL"""
        reverse_index = {}
        for subject, data in self.index.items():
            for teacher, teacher_url in data["teachers"].items():
                reverse_index[teacher] = {
                    "url": teacher_url,
                    "category": subject  # 統一使用 category 作為分類
                }
        return reverse_index
    
    def export(self, export_type: str = "all", filepath: Optional[str] = None) -> str:
        """匯出索引資料為 JSON 格式
        
        Args:
            export_type (str): 要匯出的資料類型 ("index"/"reverse_index"/"all"，預設為 "all")
            filepath (str, optional): 輸出檔案路徑，若未指定則自動生成
            
        Returns:
            str: 實際儲存的檔案路徑
            
        Raises:
            ValueError: 當 export_type 不合法時
            Exception: 當檔案寫入失敗時
        """
        # 驗證 export_type
        valid_types = ["index", "reverse_index", "all"]
        if export_type.lower() not in valid_types:
            raise ValueError(f"不支援的匯出類型。請使用 {', '.join(valid_types)}")

        # 準備要匯出的資料
        export_data = {}
        if export_type.lower() == "index":
            export_data["index"] = self.index
        elif export_type.lower() == "reverse_index":
            export_data["reverse_index"] = self.reverse_index
        else:  # all
            export_data = {
                "index": self.index,
                "reverse_index": self.reverse_index
            }

        # 加入匯出時間
        export_data["export_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 如果未指定檔案路徑，則自動生成
        if filepath is None:
            filepath = f"new_wiki_teacher_{export_type}.json"

        # 寫入 JSON 檔案
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            return filepath
        except Exception as e:
            raise Exception(f"Failed to write JSON file: {str(e)}")

    def refresh(self) -> None:
        """重新載入索引資料"""
        with ThreadPoolExecutor(max_workers=10) as executor:
            self.index = self._get_new_wiki_teacher_index(executor)
        self.reverse_index = self._build_teacher_reverse_index()

    @classmethod
    def get_instance(cls) -> 'NewWikiTeacherIndex':
        """取得單例實例
        
        Returns:
            NewWikiTeacherIndex: 索引類別的單例實例
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

class TNFSHClassTable:
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

    def __init__(self, target: str) -> None:
        """初始化課表物件
        
        Args:
            url (str): 課表網頁的URL
            
        Raises:
            TableError: 當網頁請求或解析失敗時
        """
        self.class_table_index = TNFSHClassTableIndex.get_instance()
        self.target = target
        self.type = self._get_type()
        self.url: str = self._get_url()
        self.soup: BeautifulSoup = self._get_soup()
        self.soup_table: Tag = self._get_soup_table()
        self.regular_soup_table: Tag = self._get_regular_soup_table()
        self.lessons: Dict[str, List[str]] = self._get_lesson()
        self.table: List[List[Dict[str, Dict[str, str]]]] = self._get_table()
        self.last_update: str = self._get_last_update()
    def _get_type(self):
        target = self.target
        if target.isdigit():
            return "class"
        else:
            return "teacher"
    
    def _get_url(self):
        base_url = self.class_table_index.base_url
        reverse_index = self.class_table_index.reverse_index
        target = self.target
        aliases = {"朱蒙":"吳銘"}
        try:
            url = base_url + reverse_index[target]["url"]
            return url
        except:
            try:
                url = base_url + reverse_index[aliases[target]]["url"]
                return url
            except Exception as e:
                raise ValueError(f'找不到班級或老師: {str(e)}')

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
        """解析課表內容為結構化資料"""
        table = self.regular_soup_table.find_all('tr')
        def class_name_split(class_td) -> Dict[str, Dict[str, str]]:
            """分析課程字串為課程名稱和教師名稱，統一回傳字典格式
            
            Args:
                class_td: BeautifulSoup的Tag物件，包含課程資訊
                
            Returns:
                Dict[str, Dict[str, str]]: 格式為 {課程名稱: {教師名稱: 連結}}
            """
            def clean_text(text: str) -> str:
                """清理文字內容，移除多餘空格與換行"""
                return text.strip("\n").strip("\r").strip(" ").replace(" ", ", ")

            def is_teacher_p(p_tag) -> bool:
                """檢查是否為包含教師資訊的p標籤"""
                check = bool(p_tag.find_all('a'))
                if check:
                    pass
                    #print(p_tag)
                return check
            
            def parse_teachers(teacher_ps) -> Dict[str, str]:
                """解析所有教師p標籤的資訊"""
                teachers_dict = {}
                #print(teacher_ps)
                
                for p in teacher_ps:
                    for link in p.find_all('a'):
                        name = clean_text(link.text)
                        href = link.get('href', '')
                        teachers_dict[name] = href
                #print(teachers_dict)
                return teachers_dict
            
            def combine_class_name(class_ps) -> str:
                """組合課程名稱"""
                texts = [clean_text(p.text) for p in class_ps]
                return ''.join(filter(None, texts)).replace("\n", ", ")
            
            # 如果沒有找到任何 p 標籤
            ps = class_td.find_all('p')
            if not ps:
                return {"": {"": ""}}
            
            # 區分教師資訊和課程名稱的p標籤
            teacher_ps = []
            class_ps = []
            #print(ps, "\n")
            for p in ps:
                #print(p)
                if is_teacher_p(p):
                    #print(p)
                    teacher_ps.append(p)
                else:
                    class_ps.append(p)
                    #print(p)
            #print("teacher_ps", teacher_ps)
            # 取得所有教師資訊
            teachers_dict = parse_teachers(teacher_ps) if teacher_ps != [] else {"": ""}
            #print(teachers_dict)
            # 組合課程名稱
            if class_ps:
                class_name = combine_class_name(class_ps)
            elif teacher_ps == {'':''}:  # 只有教師資訊，沒有課程名稱
                class_name = "找不到課程"
            else:  # 沒有任何資訊
                class_name = ""
            
            # 組合最終結果
            if class_name or teachers_dict != {"": ""}:
                result = {class_name: teachers_dict}
                #print(result)
                return result
            return {"": {"": ""}}
        
        result = [[
            class_name_split(class_) 
            for class_ in row.find_all('td')[2:]
            ] for row in table
        ]
        #print_format(result, "json")
        return result

    def _get_event_description(self, target: Dict[str, str]) -> str:
        def _get_a_href(url: str, text: str) -> str:
            return f'<a href="{url}">{text}</a>'

        def _get_new_wiki_teacher_links_and_name(teacher_name: str) -> List[Tuple[str, str]]:
            """取得新竹園 Wiki 教師連結列表，返回 (URL, 名稱) 的列表"""
           
            Index = NewWikiTeacherIndex.get_instance()
            teacher_data = Index.reverse_index
            #print_format(Index.teacher_index)
            # 先直接搜尋完全匹配的教師名稱
            if teacher_name in teacher_data:
                teacher_info_list = teacher_data[teacher_name]
                return [(teacher_info_list["url"], teacher_name)]

            # 若無完全匹配，搜尋包含教師名稱的項目
            partial_matches = [
                (info_list["url"], name) 
                for name, info_list in teacher_data.items()
                if teacher_name in name
            ]
            #print(teacher_name)
            #print_format(teacher_data)
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
        tnfsh_official_url = "https://www.tnfsh.tn.edu.tw"
        tnfsh_lesson_information_url = "https://www.tnfsh.tn.edu.tw/latestevent/index.aspx?Parser=22,4,25"
        
        def _get_class_event_description(self, target):
            if target and target != {"": ""}:  # 如果有教師資訊
                # 課表連結
                table_links = []
                for teacher_name, teacher_link in target.items():
                    teacher_url = f"http://w3.tnfsh.tn.edu.tw/deanofstudies/course/{teacher_link}"
                    table_links.append(f"{_get_a_href(teacher_url, f'{teacher_name}-課表')}")
                description.append(f"教師課表連結： {' | '.join(table_links)}")
                description.append(
                    f"本班課表連結： {_get_a_href(self.url, f'{self.target}-課表')}"
                )

                # 竹園wiki連結
                wiki_links = []
                for teacher_name in target.keys():
                    new_wiki_links = _get_new_wiki_teacher_links_and_name(teacher_name)
                    if new_wiki_links:
                        wiki_links.extend(
                            [_get_a_href(link, f"{name}-wiki") for link, name in new_wiki_links]
                        )
                if wiki_links:
                    description.append(f"新竹園wiki： {' | '.join(wiki_links)}")
                else:
                    description.append("新竹園wiki： 無相關資料")


            else:
                description.append("教師： 無相關資料")
                description.append(
                    f"本班課表連結： {_get_a_href(self.url, f'{self.target}-課表')}"
                )
            description.append("")
            description.append(
                f"南一中官網： {_get_a_href(tnfsh_official_url, '南一中官網')}"
                f"\n南一中官網-課程資訊： {_get_a_href(tnfsh_lesson_information_url, '教學進度、總體計畫、多元選修等等')}"
            )
            
            return "\n".join(description)
        def _get_teacher_event_description(self, target):
            if target and target != {"": ""}:  # 如果有教師資訊
                # 課表連結
                table_links = []

                
                for class_code, class_link in target.items():
                    class_url = f"http://w3.tnfsh.tn.edu.tw/deanofstudies/course/{class_link}"
                    table_links.append(f"{_get_a_href(class_url, f'{class_code}-課表')}")
                description.append(f"任課班級課表連結： {' | '.join(table_links)}")
                
                description.append(
                    f"任課老師課表連結： {_get_a_href(self.url, f'{self.target}-課表')}"
                )
            else:
                description.append("班級： 無相關資料")
                description.append(
                    f"任教老師課表連結： {_get_a_href(self.url, f'{self.target}-課表')}"
                )
            
            description.append("")
            description.append(
                f"南一中官網： {_get_a_href(tnfsh_official_url, '南一中官網')}"
                f"\n南一中官網-課程資訊： {_get_a_href(tnfsh_lesson_information_url, '教學進度、總體計畫、多元選修等等')}"
            )
            
            return "\n".join(description)
        target = target
        if self.type == "class":
            return _get_class_event_description(self, target)
        elif self.type == "teacher":
            return _get_teacher_event_description(self, target)

    def _export_to_json(self, filepath: Optional[str] = None) -> str:
        """將課表資料匯出為JSON格式
        
        Args:
            filepath (str, optional): 輸出檔案路徑，若未指定則自動生成
            
        Returns:
            str: 實際儲存的檔案路徑
            
        Raises:
            Exception: 當檔案寫入失敗時
        """
        data: Dict[str, Any] = {
            "metadata": {
                "object": self.target,
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
            filepath = f"{self.type}_{self.target}.json"

        # 寫入 JSON 檔案
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return filepath
        except Exception as e:
            raise Exception(f"Failed to write JSON file: {str(e)}")

    def _export_to_csv(self, filepath: str = None) -> str:
        """將課表匯出為 Google Calendar 格式的 CSV"""
        import csv
        from datetime import timedelta
        if filepath is None:
            filepath = f"{self.type}_{self.target}.csv"
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = [
                    "Subject", 
                    "Start Date", 
                    "Start Time", 
                    "End Time", 
                    "Description", 
                    "Location", 
                    "Repeat"
                ]
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
                        if lesson_name == "":
                            continue
                        teacher = list(day.values())[0]
                        start_time, end_time = self.lessons[lesson_index_name]
                        
                        try:
                            current_date = monday + timedelta(days=day_index)
                            
                            start_datetime = datetime.strptime(f"{current_date.date()} {start_time}", "%Y-%m-%d %H:%M")
                            end_datetime = datetime.strptime(f"{current_date.date()} {end_time}", "%Y-%m-%d %H:%M")
                            
                            # 設定每週重複(但repeat不能用在google calendar)
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
    
    def _export_to_ics(self, filepath: str = None) -> str:
        """將課表匯出為 ICS 格式檔案"""
        if filepath is None:
            filepath = f"{self.type}_{self.target}.ics"
        from datetime import timedelta
        try:
            from icalendar import Calendar, Event
            
            # 建立日曆
            cal = Calendar()
            cal.add('prodid', f'-//{filepath}_台南一中課表//TW')
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
                    if lesson_name == "":
                        continue
                    #print(lesson_name)
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
            with open(filepath, 'wb') as f:
                f.write(cal.to_ical())
            return filepath
            
        except ImportError:
            raise Exception("請安裝 icalendar 套件: poetry add icalendar")
        except IOError as e:
            raise IOError(f"無法存取檔案 '{filepath}': {e}")
        except Exception as e:
            raise Exception(f"匯出 ICS 時發生未預期的錯誤: {e}")    
    def export(self, type:str, filepath: Optional[str] = None):
        type_list = ["json", "csv", "ics"]

        if type not in type_list:
            raise ValueError(f'沒有模式: {type}')

        if type == "json":
            filepath = self._export_to_json(filepath)
        elif type == "csv":
            filepath = self._export_to_csv(filepath)
        elif type == "ics":
            filepath = self._export_to_ics(filepath)
        
        return filepath


from abc import ABC, abstractmethod
from typing import Any, Optional, List
import gradio as gr
import requests

class Interface(ABC):
    """介面抽象基類
    
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

    @abstractmethod
    def display(self, args: List[str]) -> Any:
        """顯示課表"""
        pass
    
    @abstractmethod
    def save_json(self, args: List[str]) -> Any:
        """儲存為JSON"""
        pass

    @abstractmethod 
    def save_csv(self, args: List[str]) -> Any:
        """儲存為CSV"""
        pass

    @abstractmethod
    def save_ics(self, args: List[str]) -> Any:
        """儲存為ICS"""
        pass
        
    def help(self, args: List[str] = None) -> str:
        """顯示說明"""
        return """支援的指令：
    - display [班級代碼]: 顯示課表
    - save_json [班級代碼]: 儲存為JSON檔案
    - save_csv [班級代碼]: 儲存為CSV檔案 (Google Calendar格式)
    - save_ics [班級代碼]: 儲存為ICS檔案 (iCalendar格式)
    - help: 顯示此說明"""

    @abstractmethod
    def run(self) -> None:
        """啟動介面"""
        pass



class GradioInterface(Interface):
    """Gradio網頁介面實作"""
    
    def __init__(self) -> None:
        super().__init__()
        # 設定年級和班級選項
        self.teacher_index = TNFSHClassTableIndex.get_instance()
        self.grades = list(self.teacher_index.index["class"]["data"].keys())
        self.classes = [f"{i:02d}" for i in range(1, 20)]
        self.export_formats = ["JSON", "CSV", "ICS"]
        
        # 建立教師列表
        

    def display(self, target_type:str, args: List[str]) -> Any:
        """顯示課表 (實作抽象方法)"""
        try:
            if len(args) != 2:
                return gr.Dataframe(), "錯誤: 需要年級和班級參數"
            grade, class_num = args
            grade = str(self.grades.index(grade) + 1)
            class_num = class_num.zfill(2)
            #print(grade)
            return self._display_table(target_type, grade + class_num)
        except Exception as e:
            return gr.Dataframe(), f"錯誤: {str(e)}"

    def save_json(self, args: List[str]) -> Any:
        """儲存為JSON (實作抽象方法)"""
        try:
            if len(args) != 2:
                return None, "錯誤: 需要年級和班級參數"
            grade, class_num = args
            return self._save_file(grade, class_num, "JSON")
        except Exception as e:
            return None, f"錯誤: {str(e)}"

    def save_csv(self, args: List[str]) -> Any:
        """儲存為CSV (實作抽象方法)"""
        try:
            if len(args) != 2:
                return None, "錯誤: 需要年級和班級參數"
            grade, class_num = args
            return self._save_file(grade, class_num, "CSV")
        except Exception as e:
            return None, f"錯誤: {str(e)}"

    def save_ics(self, args: List[str]) -> Any:
        """儲存為ICS (實作抽象方法)"""
        try:
            if len(args) != 2:
                return None, "錯誤: 需要年級和班級參數"
            grade, class_num = args
            return self._save_file(grade, class_num, "ICS")
        except Exception as e:
            return None, f"錯誤: {str(e)}"

    def _display_table(self, target_type: str, target: str) -> tuple[gr.Dataframe, str]:
        """顯示課表內容

        Args:
            target_type (str): 目標類型，"class" 或 "teacher"
            target (str): 目標識別符，如班級代碼或教師名稱

        Returns:
            tuple[gr.Dataframe, str]: (課表資料框, 訊息)
        """

        try:
            table = TNFSHClassTable(target)
            print(target)
            # 轉換課表數據為顯示格式
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
            
            # 設定表頭
            headers = ["星期一", "星期二", "星期三", "星期四", "星期五"]
            
            # 生成訊息
            message = f"成功載入 {target} 的課表"
            if target_type == "class":
                message = f"成功載入 {target[0]}{target[1:]}班 的課表"
            
            return gr.Dataframe(value=rows, headers=headers), message
            
        except Exception as e:
            return gr.Dataframe(), f"錯誤: {str(e)}"

    def _get_file_info(self, table: TNFSHClassTable, format: str) -> str:
        """產生檔案相關資訊文字"""
        info = []
        info.append("=== 課表資訊 ===")
        info.append(f"班級：{table.target}班")
        info.append(f"最後更新：{table.last_update}")
        info.append(f"課表連結：{table.url}")
        info.append("")
        
        info.append("=== 檔案說明 ===")
        if format == "JSON":
            info.append("JSON 格式包含完整的課表資料，適合程式讀取與資料分析")
            info.append("可使用任何文字編輯器開啟")
        elif format == "CSV":
            info.append("CSV 格式適合匯入 Google Calendar")
            info.append("匯入步驟：")
            info.append("1. 前往 Google Calendar 設定")
            info.append("2. 選擇「匯入與匯出」")
            info.append("3. 選擇「匯入」並上傳 CSV 檔案")
            info.append("CSV 格式在 Google Calendar 不支援 repeat ")
        elif format == "ICS":
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

    def _save_file(self, grade: str, class_num: str, format: str) -> tuple[gr.File, str, str]:
        """儲存檔案的實際邏輯"""
        try:
            grade = str(self.grades.index(grade) + 1)
            class_num = class_num.zfill(2)
            table = TNFSHClassTable(grade + class_num)
            
            filepath = table.export(format.lower())
            
            message = f"已將 {grade}年{class_num}班 課表儲存為 {format} 格式"
            info = self._get_file_info(table, format)
            
            return gr.File(value=filepath), message, info
            
        except Exception as e:
            return None, f"錯誤: {str(e)}", ""

    def run(self) -> None:
        """啟動Gradio介面"""
        int
        with gr.Blocks(
            title="臺南一中課表查詢系統",
            theme="Zarkel/IBM_Carbon_Theme"
        ) as interface:
            gr.Markdown("# 臺南一中課表查詢系統")
            
            with gr.Tab("顯示課表"):
                with gr.Row():
                    display_grade = gr.Dropdown(choices=self.grades, label="年級")
                    display_class = gr.Dropdown(choices=self.classes, label="班級")
                    display_btn = gr.Button("顯示課表")
                display_table = gr.Dataframe(label="課表")
            
            with gr.Tab("下載課表"):
                with gr.Row():
                    save_grade = gr.Dropdown(choices=self.grades, label="年級")
                    save_class = gr.Dropdown(choices=self.classes, label="班級")
                    save_format = gr.Dropdown(choices=self.export_formats, label="格式")
                    save_btn = gr.Button("下載課表")
                save_file = gr.File(label="下載檔案")
                file_info = gr.TextArea(label="檔案資訊", interactive=False)
            
            message = gr.Textbox(label="系統訊息", interactive=False)
            
            # 設定事件處理
            display_btn.click(
                fn=lambda g, c: self.display("class", [g , c]),
                inputs=[display_grade, display_class],
                outputs=[display_table, message]
            )
            
            save_btn.click(
                fn=lambda g, c, f: self._save_file(g, c, f),
                inputs=[save_grade, save_class, save_format],
                outputs=[save_file, message, file_info],
            )
        # 啟動介面
        interface.launch(
            share=True,
            inbrowser=True, 
            show_error=True,
            debug=True,
            prevent_thread_lock=True
            
        )

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


def course_swap_finder(src_teacher: str, src_course: Tuple[int, int], src_course_streak: int):
    src_course = [src_course[1] - 1, src_course[0] - 1] # day, period to period day

    def _get_class_stutus(table: List[List[Dict[str, Dict[str, str]]]]) -> List[List[bool]]:
        """取得課表的空堂狀態
    
        Returns:
            List[List[bool]]: 二維陣列，代表每個時段是否有課
            外層 list 為 period (節次)，內層 list 為 day (星期一到五)
        """
        status = []
        for period in table:
            period_status = []
            for course in period:
                period_status.append(bool(course != {"": {"": ""}}))
            status.append(period_status)
        return status

    def _get_class_code(table: List[List[Dict[str, Dict[str, str]]]], src_course: Tuple[int, int]) -> list[str]:
        """取得課程代碼
        
        Returns:
            list[str]: 指定位置的課程代碼列表
            若位置超出範圍或該時段無課程，則回傳空列表
            src_course 格式為 (period, day)，period 為節次，day 為星期幾
        """
        if src_course[0] < 0 or src_course[1] < 0 or src_course[0] >= len(table) or src_course[1] >= len(table[0]):
            return []  # Return an empty list if indices are out of bounds
        src_course = table[src_course[0]][src_course[1]]
        if not src_course:  # Check if src_course is empty
            return []
        src_course_class = list(list(src_course.values())[0].keys())
        if not src_course_class:
            return []
        #print(src_course)
        #print(src_course_class)
        return src_course_class

    def _check_streak_same_target(table: List[List[Dict[str, Dict[str, str]]]], src_course: Tuple[int, int], src_course_streak: int) -> bool:
        """檢查連堂狀態
        
        Returns:
            bool: 是否為相同課程的連堂
            src_course 格式為 (period, day)，period 為節次，day 為星期幾
        """
        src_course_class_code = _get_class_code(table, src_course)
        for i in range(src_course_streak):
            offset_couse_class_code = _get_class_code(table, (src_course[0] + i, src_course[1]))
            if src_course_class_code != offset_couse_class_code:
                return False
       #print(src_course_class_code)
        return True

    def _check_streak_empty(table: List[List[Dict[str, Dict[str, str]]]], src_course: Tuple[int, int], src_course_streak: int) -> bool:
        """檢查連堂是否為空堂
        
        Returns:
            bool: 指定的連續時段是否皆為空堂
            src_course 格式為 (period, day)，period 為節次，day 為星期幾
        """
        for i in range(src_course_streak):
            if src_course[0] + i >= len(table) or src_course[1] >= len(table[0]):
                return False  # Out of bounds
            if table[src_course[0] + i][src_course[1]] != {"": {"": ""}}:
                return False
        return True

    def _find_dst_streak_and_empty(table: List[List[Dict[str, Dict[str, str]]]], src_course_streak: int) -> List[Tuple[int, int]]:
        """尋找目標連堂
        
        Returns:
            List[Tuple[int, int]]: 找到的連堂位置列表
            每個元組格式為 (period, day)，period 為節次，day 為星期幾
        """
        streak_course = []
        for i in range(len(table)):
            for j in range(len(table[0])):
                check = _check_streak_same_target(table, (i, j), src_course_streak)
                if check:
                    streak_course.append((i, j))
        return streak_course

    src_teacher_table = TNFSHClassTable(src_teacher)
    table = src_teacher_table.table
    if _check_streak_empty(table, src_course, src_course_streak):
        print("給定連堂為空堂")
        return
    else:
        print("給定連堂不為空堂")

    if _check_streak_same_target(table, src_course, src_course_streak):
        print("給定連堂確實為連堂")
    else:
        print("給定連堂不為連堂")
        return

    status = _get_class_stutus(table)
    print_format(status, "2d_list")
    dst_class_codes = _get_class_code(table, src_course)
    for dst_class_code in dst_class_codes:
        dst_teacher_table = TNFSHClassTable(dst_class_code)
        dst_table = dst_teacher_table.table
        streak_and_empty = _find_dst_streak_and_empty(dst_table, src_course_streak)
        #print(streak_and_empty)
    
    



def main() -> None:
    #interface_type = input("請選擇使用者介面(cmd / gradio / both，預設為 both): ")
    interface_type = "gradio"
    App().run(interface_type)

def test() -> None:
    course_swap_finder("顏永進", (2, 1), 2)

    

if __name__ == "__main__":
    #main()
    test()


