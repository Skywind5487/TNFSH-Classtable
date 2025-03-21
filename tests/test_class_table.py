import pytest
from unittest.mock import Mock, patch
from tnfsh_class_table.main import class_table, TableError, Commands

# 模擬的 HTML 內容
MOCK_HTML = """
<table>
    <tr><td>節次</td><td>時間</td><td>星期一</td></tr>
    <tr><td>第1節</td><td>0810｜0900</td><td>國文\n王小明</td></tr>
</table>
<p class="MsoNormal" align="center">
    <span>課表</span>
    <span>2024-01-15</span>
</p>
<span style='font-family:"微軟正黑體",sans-serif;color:blue'>三年7班</span>
"""

@pytest.fixture
def mock_response():
    """建立模擬的網頁回應"""
    mock = Mock()
    mock.status_code = 200
    mock.content = MOCK_HTML.encode('utf-8')
    return mock

@pytest.fixture
def table(mock_response):
    """建立測試用的課表物件"""
    with patch('requests.get', return_value=mock_response):
        return class_table("http://example.com")

def test_get_class(table):
    """測試班級資訊擷取"""
    assert table.class_ == {"grade": 3, "class": 7}

def test_get_last_update(table):
    """測試最後更新日期擷取"""
    assert table.last_update == "2024-01-15"

def test_get_table(table):
    """測試課表內容擷取"""
    expected = [[{"國文": "王小明"}]]
    assert table.table == expected

def test_invalid_url():
    """測試無效的URL處理"""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception("Connection error")
        with pytest.raises(TableError):
            class_table("http://invalid-url.com")

def test_write_json(table, tmp_path):
    """測試JSON檔案輸出"""
    filepath = tmp_path / "test.json"
    result = table.write(str(filepath))
    assert filepath.exists()

# Commands 類別測試
def test_commands_help():
    """測試help指令"""
    cmd = Commands()
    result = cmd.execute("help")
    assert "display" in result
    assert "save_json" in result

def test_commands_invalid():
    """測試無效指令"""
    cmd = Commands()
    result = cmd.execute("invalid")
    assert "未知的命令" in result

def test_commands_display(mock_response):
    """測試display指令"""
    with patch('requests.get', return_value=mock_response):
        cmd = Commands()
        result = cmd.execute("display 307")
        assert isinstance(result, list)
