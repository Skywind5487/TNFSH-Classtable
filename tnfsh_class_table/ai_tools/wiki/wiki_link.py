from typing import Union
from tnfsh_class_table.utils.log_func import log_func

@log_func
def get_wiki_link(target: str) -> Union[str, list[str]]:
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
    # use logger to log func start
    from tnfsh_timetable_core import TNFSHTimetableCore
    wiki_core = TNFSHTimetableCore()
    logger = wiki_core.get_logger()

    logger.info(f"get_wiki_link")

    base_url = "https://tnfshwiki.tfcis.org"
    wiki_url = f"{base_url}/{target}  "
    
    import requests
    # 先檢查 URL 是否有效
    try:
        import tenacity
        @tenacity.retry(
            stop=tenacity.stop_after_attempt(3),
            wait=tenacity.wait_fixed(1),
            retry=tenacity.retry_if_exception_type(requests.RequestException)
        )
        def request_head(url: str, timeout: int = 3) -> requests.Response:
            return requests.head(url, timeout=timeout)
        response = request_head(wiki_url)
        if response.status_code == 200:
            return wiki_url
    except requests.RequestException:
        pass
    except tenacity.RetryError:
        pass

    # 如果是老師，進行額外檢查
    try:
        from tnfsh_wiki_teachers_core import TNFSHWikiTeachersCore
        wiki_core = TNFSHWikiTeachersCore()
        import asyncio
        index = asyncio.run(wiki_core.fetch_index())
        teacher_data = index.reverse_index.root

        # 先直接搜尋完全匹配的教師名稱
        if target in teacher_data:
            teacher_info_list = teacher_data[target]
            return f"{base_url}/{teacher_info_list.url.strip("/")}"

        # 若無完全匹配，搜尋包含教師名稱的項目
        partial_matches = [
            name 
            for name, info_list in teacher_data.items()
            if target in name
        ]

        if len(partial_matches) == 1:
            return f"{base_url}/{teacher_data[partial_matches[0]].url.strip("/")}"
        else:
            return partial_matches
    except ValueError:
        raise ValueError(f"無法找到 {target} 的Wiki連結")

if __name__ == "__main__":
    # 測試 get_wiki_link 函數
    print(get_wiki_link("欽發麵店"))
    print(get_wiki_link("分類:科目"))
    print(get_wiki_link("顏永進"))  # 假設有這位老師
    print(get_wiki_link("不存在的老師"))  # 假設沒有這位老師