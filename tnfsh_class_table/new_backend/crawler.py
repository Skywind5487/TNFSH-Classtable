from typing import List, Set, Dict, Optional, Literal, Tuple, TypedDict
import aiohttp
from bs4 import BeautifulSoup
from tnfsh_class_table.backend import TNFSHClassTableIndex
import json

class FetchError(Exception):
    pass

class RawParsedResult(TypedDict):
    last_update: str
    periods: Dict[str, Tuple[str, str]]
    table: List[List[Dict[str, Dict[str, str]]]]

def resolve_target(
    target: str,
    reverse_index: Dict[str, Dict[str, str]],
    aliases: List[Set[str]]
) -> Optional[str]:
    """
    根據目標名稱解析別名，回傳可用於 reverse_index 的合法 key。
    """
    if target in reverse_index:
        return target

    for alias_set in aliases:
        if target in alias_set:
            candidates = alias_set - {target}
            for alias in candidates:
                if alias in reverse_index:
                    return alias

    return None

async def fetch_raw_html(target: str) -> BeautifulSoup:
    """
    非同步抓取原始課表 HTML
    """
    index: TNFSHClassTableIndex = TNFSHClassTableIndex.get_instance()
    reverse_index: Dict[str, Dict[str, str]] = index.reverse_index
    base_url: str = index.base_url

    aliases: List[Set[str]] = [
        {"朱蒙", "吳銘"}
    ]
    
    real_target = resolve_target(target, reverse_index, aliases)
    if real_target is None:
        raise FetchError(f"找不到 {target} 的課表網址")

    relative_url = reverse_index[real_target]["url"]
    full_url = base_url + relative_url

    try:
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(full_url, headers=headers) as response:
                response.raise_for_status()
                content = await response.read()
                html_text = content.decode('big5', errors='ignore')
                # 使用 BeautifulSoup 解析 HTML
                soup = BeautifulSoup(html_text, 'html.parser')
                return soup
                
    except Exception as e:
        raise FetchError(f"請求失敗: {e}")

def parse_html(soup: BeautifulSoup, type: Literal["class", "teacher"]) -> RawParsedResult:
    """
    解析原始 HTML，擷取 last_update、periods、table
    """
    # 擷取更新日期
    update_element = soup.find('p', class_='MsoNormal', align='center')
    if update_element:
        spans = update_element.find_all('span')
        last_update = spans[1].text if len(spans) > 1 else "No update date found."
    else:
        last_update = "No update date found."

    # 擷取課表 table 並移除 border
    main_table = None
    for table in soup.find_all("table"):
        new_table = BeautifulSoup('<table></table>', 'html.parser').table
        
        for row in table.find_all("tr"):
            for td in row.find_all('td'):
                if td.get('style') and 'border' in td['style']:
                    td.decompose()
            if len(row.find_all('td')) == 7:
                new_table.append(row)
                
        if len(new_table.find_all('tr')) > 0:
            main_table = new_table
            break

    if main_table is None:
        raise FetchError("找不到符合格式的課表 table")

    # 擷取 periods
    import re
    re_pattern = r'(\d{2})(\d{2})'
    re_sub = r'\1:\2'
    periods: Dict[str, Tuple[str, str]] = {}
    for row in main_table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        lesson_name = cells[0].text.replace("\n", "").replace("\r", "")
        time_text = cells[1].text.replace("\n", "").replace("\r", "")
        times = [re.sub(re_pattern, re_sub, t.replace(" ", "")) for t in time_text.split("｜")]
        if len(times) == 2:
            periods[lesson_name] = (times[0], times[1])

    # 擷取課程名稱和教師名稱
    # 這裡的 class_td 是一個 td 標籤，包含了課程名稱和教師名稱
    def class_name_split(class_td) -> Dict[str, Dict[str, str]]:
        """分析課程字串為課程名稱和教師名稱，統一回傳字典格式"""
        def clean_text(text: str) -> str:
            """清理文字內容，移除多餘空格與換行"""
            return text.strip("\n").strip("\r").strip(" ").replace(" ", ", ")

        def is_teacher_p(p_tag) -> bool:
            """檢查是否為包含教師資訊的p標籤"""
            return bool(p_tag.find_all('a'))
        
        def parse_teachers(teacher_ps) -> Dict[str, str]:
            """解析所有教師p標籤的資訊"""
            teachers_dict = {}
            for p in teacher_ps:
                for link in p.find_all('a'):
                    name = clean_text(link.text)
                    href = link.get('href', '')
                    teachers_dict[name] = href
            return teachers_dict
        
        def combine_class_name(class_ps) -> str:
            """組合課程名稱"""
            texts = [clean_text(p.text) for p in class_ps]
            return ''.join(filter(None, texts)).replace("\n", ", ")
        
        ps = class_td.find_all('p')
        if not ps:
            return {"": {"": ""}}
        
        teacher_ps = []
        class_ps = []
        for p in ps:
            if is_teacher_p(p):
                teacher_ps.append(p)
            else:
                class_ps.append(p)
        
        teachers_dict = parse_teachers(teacher_ps) if teacher_ps else {"": ""}
        
        if class_ps:
            class_name = combine_class_name(class_ps)
        elif teacher_ps == {'':''}:
            class_name = "找不到課程"
        else:
            class_name = ""
        
        if class_name or teachers_dict != {"": ""}:
            return {class_name: teachers_dict}
        return {"": {"": ""}}

    # 擷取 table raw 格式
    table: List[List[Dict[str, Dict[str, str]]]] = []
    for row in main_table.find_all("tr"):
        cells = row.find_all("td")[2:]  # 跳過前兩列（節次和時間）
        row_data = []
        for cell in cells:
            row_data.append(class_name_split(cell))
        if row_data:
            table.append(row_data)

    return RawParsedResult(
        last_update=last_update,
        periods=periods,
        table=table
    )


if __name__ == "__main__":
    import asyncio
    target = "307"
    html_content = asyncio.run(fetch_raw_html(target))
    parsed_result = parse_html(html_content, type="class")
    print(f"Last Update: {parsed_result['last_update']}")
    print("Periods:")
    for lesson, times in parsed_result['periods'].items():
        print(f"  {lesson}: {times[0]} - {times[1]}")
    print("Table:")
    for row in parsed_result['table']:
        for cell in row:
            print("  Cell:")
            for class_name, teachers in cell.items():
                print(f"  {class_name}: {teachers}")
    save_path = "class_307.json"
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(parsed_result['table'], ensure_ascii=False, indent=4))