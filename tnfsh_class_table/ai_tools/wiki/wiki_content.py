from typing import Any
from bs4 import BeautifulSoup, Tag, Comment
from tnfsh_class_table.utils.log_func import log_func

def _regular_soup(soup: Any) -> str:
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

@log_func
def get_wiki_content(target: str) -> str:
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
    from tnfsh_class_table.ai_tools.wiki.wiki_link import get_wiki_link
    url = get_wiki_link(target)
    import requests
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    soup = soup.find('div', {'id': 'bodyContent'})
    soup = _regular_soup(soup)
    return str(soup)


if __name__ == "__main__":
    # 測試用例
    target = "四大胖子"
    content = get_wiki_content(target)
    print(content)
    # 這裡可以進一步處理 content，例如輸出到文件或其他操作