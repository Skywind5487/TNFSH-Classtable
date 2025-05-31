from typing import Union
def get_specific_course(target: str, day: int, period: int) -> Union[dict[str, Union[str, list[dict[str, str]]]], str]:
        """
        取得指定班級或老師的課程資訊。

        Args:
            target (str): 班級或老師名稱
            day (int): 星期幾(1-5)
            period (int): 第幾節(1-8)

        Returns:
            dict[str, Union[str, list[dict[str, str]]]]: 課程資訊
            # 可能的回傳格式有兩種，依據班級或老師的不同而有所區別。
            # 1. 如果是班級，返回課程中老師資訊
            # 2. 如果是老師，返回課程對應的學生資訊
            # 3. 如果是空堂，返回"該節是空堂"
        Example:
            1. 
            {
                "subject": "數學",
                "teacher": [
                    {
                        "name": "陳老師",
                        "link": "example.com/teacher"
                    }, ...
                ]
            }
            2. 
            {
                "subject": "數學",
                "class": [
                    {
                        "class_code": "307",
                        "link": "example.com/teacher"
                    }, ...
                ]
            }
        """
        from tnfsh_class_table.backend import TNFSHClassTable
        class_table = TNFSHClassTable(target)
        table = class_table.transposed_table
        if day < 1 or day > len(table) or period < 1 or period > len(table[0]):
            return "請提供有效的星期和節次範圍"
        course = table[day - 1][period - 1]
        subject = list(course.keys())[0] 
        object = list(course[subject].keys())
        links = list(course[subject].values()) 
        #print(links)
        type = class_table.type
        if type == "class":
            # 如果是班級，返回班級資訊
            result = {}
            result["subject"] = subject
            result["teacher"] = []
            for teacher_name, link in zip(object, links):
                if teacher_name == "" and link == "":
                    return "該節是空堂"
                base_url = "http://w3.tnfsh.tn.edu.tw/deanofstudies/course/"
                result["teacher"].append({"teacher_name": teacher_name, "link": base_url + link})

        else:
            # 如果是老師，返回老師資訊
            result = {}
            result["subject"] = subject
            result["class"] = []
            for teacher_name, link in zip(object, links):
                if teacher_name == "" and link == "":
                    return "該節是空堂"
                base_url = "http://w3.tnfsh.tn.edu.tw/deanofstudies/course/"
                result["class"].append({"class_code": teacher_name, "link": base_url + link})
        
        return result