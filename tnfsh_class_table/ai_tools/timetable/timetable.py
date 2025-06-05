from typing import Union

def get_table(target: str) -> dict[str, Union[str, list[dict[str, Union[str, list[dict[str, Union[str, list[dict[str, str]]]]]]]]]]:
        """
        取得指定班級或老師的課表
        
        使用指引:
            1. 如果想查詢二年五班，應該轉換成205輸入
            2. 如果想取得"Nicole老師的課表"，請輸入"Nicole"

        使用場景:
            1. 當使用者需要查詢特定班級或老師的課表時
            2. 當使用者希望獲取課表資訊以便進一步檢查或分析時
            3. 幾乎所有跟課表有關的查詢都可以使用此方法

        Args:
            target (str): 班級或老師名稱
        
        Returns:
            dict[str, Union[str, list[dict[str, str]]]]: 課表資訊
            包含以下鍵值：
            - all_courses: 所有課程資訊，包含課程名稱、教師名稱、班級代碼、上課時間等
                - day: 星期幾(1-5)
                - courses: 課程列表，每個元素包含課程名稱、教師名稱、班級代碼等資訊
                    - period: 第幾節(1-8)
                    - subject: 課程名稱
                    - teachers_of_course: 教師名稱列表，包含教師名稱和連結
                        - teacher_name: 教師名稱
                        - link: 教師課表連結    
            - target: 目標班級或老師名稱
            - type: 課表類型（班級或老師）

        Example:
        {
            "all_courses": [
                {
                    "day": 1,
                    "courses": [
                        {
                            "period": 1,
                            "subject": "",
                            "class_engaged": [
                                {
                                    "class_code": "",
                                    "link": ""
                                }
                            ]
                        },
                        {
                            "period": 2,
                            "subject": "",
                            "class_engaged": [
                                {
                                    "class_code": "",
                                    "link": ""
                                }
                            ]
                        }, ...
                    ]
                }, ...
            ],
            "target": "顏永進",
            "type": "teacher"
        }
        """
        from tnfsh_class_table.backend import TNFSHClassTable
        target: TNFSHClassTable = TNFSHClassTable(target)
        table = target.transposed_table
        result = {}
        type = target.type
        result["all_courses"] = []
        for i, day in enumerate(table):
            day_result = {}
            day_result["day"] = i + 1
            courses = []
            for j, period in enumerate(day):
                if isinstance(period, dict):
                    course = {}
                    course["period"] = j + 1
                    course_name = list(period.keys())[0]
                    objects = list(period[course_name].keys())
                    links = list(period[course_name].values())
                    course["subject"] = course_name
                    if type == "class":
                        for object, link in zip(objects, links):
                            course["teachers_of_course"] = []
                            course["teachers_of_course"].append({
                                "teacher_name": object,
                                "link": link
                            })
                    else: 
                        for object, link in zip(objects, links):
                            course["class_engaged"] = []
                            course["class_engaged"].append({
                                "class_code": object,
                                "link": link
                            })
                    courses.append(course)
                day_result["courses"] = courses
            result["all_courses"].append(day_result)
        
        result["target"] = target.target
        result["type"] = type
        #result["lesson"] = target.lessons
        
        return result