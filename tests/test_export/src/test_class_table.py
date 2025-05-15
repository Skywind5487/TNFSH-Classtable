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

# 🛠️ 通用解碼工具
def safe_read_text(path: str) -> str:
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ["utf-8-sig", "utf-8", "utf-16", "utf-16-le"]:
        try:
            return raw.decode(enc)
        except Exception:
            continue
    raise UnicodeDecodeError("無法解碼", raw, 0, 1, "unsupported format")

def safe_read_json(path: str) -> dict:
    return json.loads(safe_read_text(path))

class MockTNFSHClassTable(TNFSHClassTable):
    def _get_soup(self):
        """覆寫_get_soup方法，使用本地HTML文件"""
        html_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "assests", 
            "class_307.html"
        )
        content = safe_read_text(html_path)
        return BeautifulSoup(content, 'html.parser')


class TestTNFSHClassTable:
    def _normalize_ics_content(self, content: bytes) -> str:
        """標準化 ICS 內容以進行比較，只保留課程名和時間"""
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("utf-16-le")
        lines = text.splitlines()

        result = []
        current_event = []
        for line in lines:
            if any(line.startswith(skip) for skip in ('DTSTAMP:', 'RRULE:', 'LOCATION:', 'DESCRIPTION:')):
                continue
            if line.startswith(('DTSTART:', 'DTEND:')):
                match = re.search(r'T(\d{2})(\d{2})', line)
                if match:
                    hour, minute = match.groups()
                    current_event.append(f"{hour}:{minute}")
                continue
            if line == 'BEGIN:VEVENT':
                current_event = []
            elif line == 'END:VEVENT':
                result.extend(current_event)
                result.append('---')
            if line.startswith('SUMMARY:'):
                current_event.append(line)
        return '\n'.join(result)

    def _normalize_csv_content(self, content: str) -> str:
        lines = content.splitlines()
        result = []
        headers = lines[0].split(',')
        subject_idx = headers.index('Subject')
        start_time_idx = headers.index('Start Time')
        end_time_idx = headers.index('End Time')

        for line in lines[1:]:
            fields = line.split(',')
            if len(fields) > max(subject_idx, start_time_idx, end_time_idx):
                subject = fields[subject_idx]
                times = []
                for idx in [start_time_idx, end_time_idx]:
                    time_str = fields[idx]
                    match = re.search(r'(\d{1,2}):(\d{2})', time_str)
                    if match:
                        hour, minute = match.groups()
                        times.append(f"{int(hour):02d}:{minute}")
                if subject and times:
                    result.append(subject)
                    result.extend(times)
                    result.append('---')
        return '\n'.join(result)

    @pytest.fixture
    def class_table(self):
        return MockTNFSHClassTable("307")

    @pytest.fixture
    def reference_json(self):
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "assests", 
            "class_307.json"
        )
        return safe_read_json(path)

    def test_json_output_matches_reference(self, class_table: TNFSHClassTable, reference_json: dict, tmp_path: str):
        test_file = tmp_path / "test_output.json"
        class_table.export("json", str(test_file))
        output_json = json.loads(safe_read_text(test_file))
        assert output_json["content"]["lessons"] == reference_json["content"]["lessons"]
        assert output_json["content"]["table"] == reference_json["content"]["table"]

    def test_csv_export(self, class_table: TNFSHClassTable, tmp_path: str):
        test_file = tmp_path / "test_output.csv"
        class_table.export("csv", str(test_file))
        assert test_file.exists()
        
        reference_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "assests", 
            "class_307.csv"
        )

        ref_content = self._normalize_csv_content(safe_read_text(reference_path))
        test_content = self._normalize_csv_content(safe_read_text(test_file))

        print("\nReference content:\n", ref_content)
        print("\nTest content:\n", test_content)
        assert test_content == ref_content

    def test_ics_export(self, class_table: TNFSHClassTable, tmp_path: str):
        test_file = tmp_path / "test_output.ics"
        class_table.export("ics", str(test_file))
        assert test_file.exists()

        reference_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "assests", 
            "class_307.ics"
        )

        ref_content = self._normalize_ics_content(Path(reference_path).read_bytes())
        test_content = self._normalize_ics_content(Path(test_file).read_bytes())

        print("\nReference content:\n", ref_content)
        print("\nTest content:\n", test_content)
        assert test_content == ref_content

if __name__ == "__main__":
    pytest.main(['-v', __file__])
