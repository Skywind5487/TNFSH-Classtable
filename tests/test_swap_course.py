import pytest
from tnfsh_class_table.ai_assistant import AIAssistant
from tnfsh_class_table.models import CourseInfo, SwapStep, SwapSinglePath, SwapPaths, URLMap


def test_get_swap_course():
    """測試取得調課資訊功能"""
    ai = AIAssistant()
    
    # 測試有效的調課請求
    result = ai.get_swap_course("顏永進", 3, 2)  # 測試星期三第二節
    print(result.model_dump_json(indent=4))
    assert isinstance(result, (SwapPaths, str))
    
    if isinstance(result, SwapPaths):
        # 驗證基本結構
        assert result.target == "顏永進"
        assert isinstance(result.paths, list)
        
        # 驗證每個路徑
        for path in result.paths:
            assert isinstance(path, SwapSinglePath)
            assert isinstance(path.steps, list)
            
            # 驗證每個步驟
            for step in path.steps:
                assert isinstance(step, SwapStep)
                assert isinstance(step.from_, CourseInfo)
                assert isinstance(step.to, CourseInfo)
                
                # 驗證來源課程
                assert isinstance(step.from_.teacher, list)
                assert isinstance(step.from_.class_, list)
                assert isinstance(step.from_.weekday, int)
                assert isinstance(step.from_.period, int)
                assert step.from_.streak is None or isinstance(step.from_.streak, int)
                
                # 驗證目標課程
                assert isinstance(step.to.teacher, list)
                assert isinstance(step.to.class_, list)
                assert isinstance(step.to.weekday, int)
                assert isinstance(step.to.period, int)
                assert step.to.streak is None or isinstance(step.to.streak, int)
                
                # 驗證 URL 格式
                for teacher in step.from_.teacher + step.to.teacher:
                    assert isinstance(teacher, URLMap)
                    assert teacher.name
                    assert teacher.url.startswith("http")
                
                for class_ in step.from_.class_ + step.to.class_:
                    assert isinstance(class_, URLMap)
                    assert class_.name
                    assert class_.url.startswith("http")
    else:
        # 如果返回錯誤訊息
        assert isinstance(result, str)
        assert "無法找到" in result or "錯誤" in result


@pytest.mark.asyncio
async def test_get_swap_course_invalid_input():
    """測試無效輸入的情況"""
    ai = AIAssistant()
    
    # 測試不存在的教師
    with pytest.raises(Exception):
        result = ai.get_swap_course("不存在的老師", 3, 2)



@pytest.mark.asyncio
async def test_get_swap_course_empty_slot():
    """測試空堂的情況"""
    ai = AIAssistant()
    
    # 假設星期三第七節是空堂
    with pytest.raises(Exception):
        result = ai.get_swap_course("顏永進", 3, 7)
    
def test_new_get_swap_course():
    from tnfsh_class_table.interface import AIAssistant
    ai = AIAssistant()
    # 測試有效的調課請求
    result = ai.get_swap_course("顏永進", 3, 2)  # 測試星期三第二節
    print(result.model_dump_json(indent=4))