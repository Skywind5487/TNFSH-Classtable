from tnfsh_class_table.utils.log_func import log_func


@log_func
def get_class_table_link(target: str) -> str:
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
    from tnfsh_class_table.backend import TNFSHClassTableIndex
    index = TNFSHClassTableIndex()
    link = index.reverse_index[target]["url"]
    base_url = "http://w3.tnfsh.tn.edu.tw/deanofstudies/course/"
    return base_url + link + "  "