import pytest
from tnfsh_class_table.interface import AIAssistant
from tnfsh_class_table.models import TeacherClassInfo, RotationStep, RotationSinglePath, RotationPaths, URLMap


@pytest.mark.asyncio
async def test_get_rotation_course():
    """測試取得輪調資訊功能"""
    ai = AIAssistant()
    
    # 測試有效的輪調請求
    result = ai.get_rotation_course("顏永進", 3, 2)  # 測試星期三第二節
    assert isinstance(result, (RotationPaths, str))
    
    if isinstance(result, RotationPaths):
        # 驗證基本結構
        assert result.target == "顏永進"
        assert isinstance(result.paths, list)
        
        # 驗證每個路徑
        for path in result.paths:
            assert isinstance(path, RotationSinglePath)
            assert isinstance(path.steps, list)
            
            # 驗證每個步驟
            for step in path.steps:
                assert isinstance(step, RotationStep)
                assert isinstance(step.from_, TeacherClassInfo)
                assert isinstance(step.to, TeacherClassInfo)
                assert isinstance(step.next_teacher, list)
                
                # 驗證來源課程資訊
                assert isinstance(step.from_.teacher, list)
                assert isinstance(step.from_.class_, list)
                assert isinstance(step.from_.subject, str)
                assert isinstance(step.from_.weekday, int)
                assert isinstance(step.from_.period, int)
                assert step.from_.streak is None or isinstance(step.from_.streak, int)
                
                # 驗證目標課程資訊
                assert isinstance(step.to.teacher, list)
                assert isinstance(step.to.class_, list)
                assert isinstance(step.to.subject, str)
                assert isinstance(step.to.weekday, int)
                assert isinstance(step.to.period, int)
                assert step.to.streak is None or isinstance(step.to.streak, int)
                
                # 驗證下一個位置的老師資訊
                for teacher in step.next_teacher:
                    assert isinstance(teacher, URLMap)
                    assert teacher.name
                    assert teacher.url.startswith("http")
                
                # 驗證來源課程的教師是目標教師
                for teacher in step.from_.teacher:
                    assert isinstance(teacher, URLMap)
                    assert teacher.name == result.target
                    assert teacher.url.startswith("http")
                
                # 驗證班級資訊
                for class_ in step.from_.class_ + step.to.class_:
                    assert isinstance(class_, URLMap)
                    assert class_.name
                    assert class_.url.startswith("http")
    else:
        # 如果返回錯誤訊息
        assert isinstance(result, str)
        assert "無法找到" in result or "錯誤" in result


@pytest.mark.asyncio
async def test_get_rotation_course_invalid_input():
    """測試無效輸入的情況"""
    ai = AIAssistant()
    
    # 測試不存在的教師
    result = ai.get_rotation_course("不存在的老師", 3, 2)
    assert isinstance(result, str)
    assert "無法找到" in result or "錯誤" in result
    
    # 測試無效的星期
    result = ai.get_rotation_course("顏永進", 6, 2)
    assert isinstance(result, str)
    assert "無法找到" in result or "錯誤" in result
    
    # 測試無效的節次
    result = ai.get_rotation_course("顏永進", 3, 9)
    assert isinstance(result, str)
    assert "無法找到" in result or "錯誤" in result


@pytest.mark.asyncio
async def test_get_rotation_course_empty_slot():
    """測試空堂的情況"""
    ai = AIAssistant()
    
    # 假設星期三第七節是空堂
    result = ai.get_rotation_course("顏永進", 3, 7)
    
    if isinstance(result, RotationPaths):
        assert result.target == "顏永進"
        if result.paths:  # 如果有可能的輪調路徑
            for path in result.paths:
                for step in path.steps:
                    # 檢查空堂的情況
                    if not step.from_.teacher:
                        assert not step.from_.class_
                        assert step.from_.subject == ""
                    if not step.to.teacher:
                        assert not step.to.class_
                        assert step.to.subject == ""
    else:
        assert isinstance(result, str)
        assert "無法找到" in result or "錯誤" in result
