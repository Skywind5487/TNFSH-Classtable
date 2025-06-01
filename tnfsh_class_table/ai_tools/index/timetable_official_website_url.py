from tnfsh_class_table.utils.log_func import log_func


@log_func
def get_timetable_official_website_url() -> str:
    """
    取得課表索引的基本網址，供使用者檢查資訊。
    
    使用指引：
        當使用者的要求不是得到連結時，應考慮使用別的方法。

    使用場景：
        1. 使用者需要查詢課表資訊
        2. 使用者希望獲取課表的官方連結
        3. 沒有別的方法可以回答使用者的需求

    Args:
        None

    Returns:
        str: 課表索引的基本網址
    """
    base_url = "http://w3.tnfsh.tn.edu.tw/deanofstudies/course/course.html"
    return base_url