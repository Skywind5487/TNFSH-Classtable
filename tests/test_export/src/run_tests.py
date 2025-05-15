import sys
import os
from test_class_table import TestTNFSHClassTable

def run_tests():
    test_instance = TestTNFSHClassTable()
    class_table = test_instance.class_table()
    
    # 測試 JSON 輸出
    try:
        ref_json = test_instance.reference_json()
        tmp_dir = "test_outputs"
        os.makedirs(tmp_dir, exist_ok=True)
        test_instance.test_json_output_matches_reference(class_table, ref_json, tmp_dir)
        print("JSON test passed")
    except Exception as e:
        print(f"JSON test failed: {e}")
        
    # 測試 CSV 輸出
    try:
        test_instance.test_csv_export(class_table, tmp_dir)
        print("CSV test passed")
    except Exception as e:
        print(f"CSV test failed: {e}")
        
    # 測試 ICS 輸出
    try:
        test_instance.test_ics_export(class_table, tmp_dir)
        print("ICS test passed")
    except Exception as e:
        print(f"ICS test failed: {e}")

if __name__ == "__main__":
    run_tests()
