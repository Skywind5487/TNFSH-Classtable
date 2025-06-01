from tnfsh_class_table.utils.log_func import log_func


@log_func
def get_timetable_official_website_url() -> str:
    """
    取得課表索引的基本網址
    當使用者的要求不是得到連結時，應考慮使用別的方法。
    提供使用者連結使使用者能檢查。

    Returns:
        str: 課表索引的基本網址
    """
    base_url = "http://w3.tnfsh.tn.edu.tw/deanofstudies/course/course.html"
    return base_url