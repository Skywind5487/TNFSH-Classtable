import pytest
import json
import os
import re
from bs4 import BeautifulSoup
from pathlib import Path
from unittest.mock import patch
from datetime import datetime
from icalendar import Calendar

from tnfsh_class_table.backend import TNFSHClassTable

class MockTNFSHClassTable(TNFSHClassTable):
    def _get_soup(self):
        """覆寫_get_soup方法，使用本地HTML文件"""
        html_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "assests", 
            "307班級課表.html"
        )
        with open(html_path, "r", encoding="utf-16le") as f:
            content = f.read()
        return BeautifulSoup(content, 'html.parser')

class TestTNFSHClassTable:
    def _normalize_ics_content(self, content: bytes) -> str:
        """標準化 ICS 內容以進行比較，只保留課程名和時間"""
        lines = content.decode('utf-8').splitlines()
        result = []
        current_event = []
        
        for line in lines:
            # 跳過 DTSTAMP, RRULE 和其他非必要欄位
            if any(line.startswith(skip) for skip in ('DTSTAMP:', 'RRULE:', 'LOCATION:', 'DESCRIPTION:')):
                continue
                
            # 只保留時間的小時和分鐘
            if line.startswith(('DTSTART:', 'DTEND:')):
                match = re.search(r'T(\d{2})(\d{2})', line)
                if match:
                    hour, minute = match.groups()
                    current_event.append(f"{hour}:{minute}")
                continue
                
            # 保留事件的開始和結束標記
            if line == 'BEGIN:VEVENT':
                current_event = []
            elif line == 'END:VEVENT':
                result.extend(current_event)
                result.append('---')  # 事件分隔符
                
            # 保留課程名稱
            if line.startswith('SUMMARY:'):
                current_event.append(line)
                
        return '\n'.join(result)

    def _normalize_csv_content(self, content: str) -> str:
        """標準化 CSV 內容以進行比較，只保留課程名稱和時間"""
        lines = content.splitlines()
        result = []
        
        # 解析標題行找到相關欄位的索引
        headers = lines[0].split(',')
        subject_idx = headers.index('Subject')
        start_time_idx = headers.index('Start Time')
        end_time_idx = headers.index('End Time')
        
        # 處理每一行
        for line in lines[1:]:
            fields = line.split(',')
            if len(fields) > max(subject_idx, start_time_idx, end_time_idx):
                # 取得課程名稱
                subject = fields[subject_idx]
                # 處理時間格式
                times = []
                for idx in [start_time_idx, end_time_idx]:
                    time_str = fields[idx]
                    match = re.search(r'(\d{1,2}):(\d{2})', time_str)
                    if match:
                        hour, minute = match.groups()
                        times.append(f"{int(hour):02d}:{minute}")
                
                # 組合結果
                if subject and times:
                    result.append(f"{subject}")
                    result.extend(times)
                    result.append('---')  # 分隔符
                
        return '\n'.join(result)

    @pytest.fixture
    def class_table(self):
        """建立測試用的課表物件"""
        return MockTNFSHClassTable("307")

    @pytest.fixture
    def reference_json(self):
        """讀取參考用的 JSON 檔案"""
        reference_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "assests", 
            "class_307.json"
        )
        with open(reference_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_json_output_matches_reference(self, class_table: TNFSHClassTable, reference_json: dict, tmp_path: str):
        """測試 JSON 輸出與參考檔案是否一致"""
        test_file = tmp_path / "test_output.json"
        class_table.export("json", str(test_file))

        with open(test_file, 'r', encoding='utf-8') as f:
            output_json = json.load(f)

        # 只比對課表結構
        assert output_json["content"]["lessons"] == reference_json["content"]["lessons"]
        assert output_json["content"]["table"] == reference_json["content"]["table"]

    def test_csv_export(self, class_table: TNFSHClassTable, tmp_path: str):
        """測試 CSV 輸出"""
        test_file = tmp_path / "test_output.csv"
        class_table.export("csv", str(test_file))
        assert test_file.exists()
        
        reference_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "assests", 
            "class_307.csv"
        )
        
        with open(reference_path, 'r', encoding='utf-8-sig') as ref, \
             open(test_file, 'r', encoding='utf-8-sig') as test:
            ref_content = self._normalize_csv_content(ref.read())
            test_content = self._normalize_csv_content(test.read())
            print("\nReference content:")
            print(ref_content)
            print("\nTest content:")
            print(test_content)
            assert test_content == ref_content

    def test_ics_export(self, class_table: TNFSHClassTable, tmp_path: str):
        """測試 ICS 輸出"""
        test_file = tmp_path / "test_output.ics"
        class_table.export("ics", str(test_file))
        assert test_file.exists()
        
        reference_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "assests", 
            "class_307.ics"
        )
        
        with open(reference_path, 'rb') as ref, \
             open(test_file, 'rb') as test:
            ref_content = self._normalize_ics_content(ref.read())
            test_content = self._normalize_ics_content(test.read())
            print("\nReference content:")
            print(ref_content)
            print("\nTest content:")
            print(test_content)
            assert test_content == ref_content

if __name__ == "__main__":
    pytest.main(['-v', __file__])
